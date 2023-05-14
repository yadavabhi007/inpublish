import datetime
import os
import shutil

import pytz
import requests
from aeb.connectors.connector import Connector
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import JSONField
from django.db.models.fields import (
    BooleanField,
    CharField,
    IntegerField,
    DateField,
)
from django.db.models.fields.files import FileField
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import UpdateView

from builder.forms import ClientSettingForm
from builder.models import (
    InteractiveFlyer,
    ClientSetting,
    InteractiveFlyerProject,
    InteractiveFlyerIndex,
    AWSUploader,
    ProjectSetting,
)
from builder.serializers import (
    InteractiveFlyerIndexLinkSerializer,
    InteractiveFlyerSerializer,
)
from builder.utils.base_class.interattivo_base_views import InterattivoViews
from builder.utils.base_class.worker_pdf_pages import WorkerPdfPages
from builder.utils.service import (
    populate_project_settings_from_client_settings,
)
from utils.thumbor_server import ThumborServer
from utils.custom_logger import log_critical

class DashboardView(InterattivoViews):
    page_name = _("Lista pubblicazioni")

    def get(self, request):
        flyers = request.user.flyers.exclude(
            status=InteractiveFlyer.WAIT_POLOTNO_PDF
        ).order_by("-id")
        flyers_initializing_count = InteractiveFlyer.objects.filter(
            initialization_in_progress=True
        ).count()
        local_tz = pytz.timezone("Europe/Rome")
        today = (
            datetime.datetime.now()
            .replace(tzinfo=pytz.utc)
            .astimezone(local_tz)
        )

        for flyer in flyers:
            try:
                if (
                    today >= flyer.settings.publicationDate
                    and flyer.status == InteractiveFlyer.SCHEDULED
                ):
                    try:
                        flyer.status = 1
                        flyer.save()
                        response = requests.get(
                            f"https://viewmanager.interattivo.net/inpublish/publish"
                            f"?id_volantino={flyer.pk}"
                        )

                        flyer.publication_url = response.json()["url"]
                        flyer.save()

                    except Exception as e:
                        pass
            except Exception as e:
                pass

        self.context.update(
            {
                "flyers": flyers,
                "flyers_initializing_count": flyers_initializing_count,
            }
        )
        if "json" in request.GET:
            class_nome = ""
            class_stato = ""
            if "class_nome" in request.GET:
                class_nome = request.GET["class_nome"]
            if "class_stato" in request.GET:
                class_stato = request.GET["class_stato"]
            return JsonResponse(
                {
                    "flyers": InteractiveFlyerSerializer(
                        flyers, many=True
                    ).data,
                    "class_nome": class_nome,
                    "class_stato": class_stato,
                }
            )
        else:
            return render(request, "builder/new/dashboard.html", self.context)

    def post(self, request):
        source_flyer_id = request.POST["source_flyer_id"]
        source_flyer = InteractiveFlyer.objects.get(pk=source_flyer_id)
        target_flyer = InteractiveFlyer.objects.create(
            name = request.POST["name"],
            status = InteractiveFlyer.DRAFT,
            seller_id = source_flyer.seller_id,
            project_type = source_flyer.project_type,
            flyer_pdf_file = source_flyer.flyer_pdf_file,
            flyer_json_file = source_flyer.flyer_json_file,
            flyer_zip_file = source_flyer.flyer_zip_file,
            affiliate = source_flyer.affiliate,
            assets_token = get_random_string(length=10),
            initialization_in_progress = True,
            user = request.user,
            image_page_width = source_flyer.image_page_width,
            image_page_height = source_flyer.image_page_height,
            products_imported = source_flyer.products_imported
        )

        for project in source_flyer.projects.all():
            target_flyer.projects.create(project_id = project.project_id)

        self.call_command_threaded(
            "clone_interactive_flyer",
            str(source_flyer.id),
            str(target_flyer.id),
        )
        return redirect("builder:dashboard")


class SettingClientView(InterattivoViews, SuccessMessageMixin, UpdateView):
    page_name = _("Modifica Impostazioni Cliente")
    form_class = ClientSettingForm
    model = ClientSetting
    template_name = "builder/new/clientsetting_form.html"
    success_message = _("Impostazioni salvate.")

    def get_object(self, queryset=None):
        return self.request.user.settings

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user_client = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("builder:dashboard")


class DeleteInteractiveFlyerView(InterattivoViews):
    def get(self, request, interactive_flyer_id):
        try:
            shutil.rmtree(
                os.path.join(
                    settings.MEDIA_ROOT, f"interactive_flyer_{self.flyer.id}"
                )
            )
        except Exception:
            pass

        if self.flyer.status == InteractiveFlyer.PUBLISHED:
            requests.get(
                f"https://viewmanager.interattivo.net/inpublish/remove"
                f"?id_volantino={self.flyer.id}"
            )
        
        flyer= InteractiveFlyer.objects.get(pk=self.flyer.pk)
        log_critical('TEST', flyer.status)
        try:
            flyer.delete()
        except Exception as e:
            log_critical('OOOOOOOO', e)
        return redirect("builder:dashboard")


class InteractiveFlyerSettingsView(InterattivoViews):
    page_name = _("Modifica Impostazioni Pubblicazione")

    def dispatch(self, request, *args, **kwargs):

        self.connector = Connector(connector=request.user.connector_type)
        self.flyer = InteractiveFlyer.objects.get(
            pk=kwargs["interactive_flyer_id"]
        )
        self.sellers = self.connector.get_sellers()
        self.projects = self.connector.get_campaigns(self.flyer.seller_id)
        self.flyer_projects = self.flyer.projects.values_list(
            "project_id", flat=True
        )
        try:
            self.ps = self.flyer.settings
        except ObjectDoesNotExist:
            self.ps = populate_project_settings_from_client_settings(
                request.user.settings, self.flyer
            )

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, interactive_flyer_id):
        from_flyer = False
        if 'from' in request.GET:
            from_flyer = True 

        self.context.update(
            {
                "flyer": self.flyer,
                "sellers": self.sellers,
                "projects": self.projects,
                "flyer_projects": self.flyer_projects,
                "from_flyer":from_flyer
            }
        )
        if "tab" in request.GET:
            self.context.update({"tab": request.GET["tab"]})
        return render(
            request,
            "builder/new/interactive_flyer_settings.html",
            self.context,
        )

    def post(self, request, interactive_flyer_id):
        if request.POST["name"] != "":
            self.flyer.name = request.POST["name"]
        else:
            url = (
                reverse(
                    "builder:interactive_flyer_settings",
                    args=[interactive_flyer_id],
                )
                + "?error=Inserisci un nome per il volantino"
            )
            return HttpResponseRedirect(url)

        # seller_id = request.POST["seller"]  # todo verifica quando è null
        seller_id = request.POST.get(
            "seller", False
        )  # todo verifica quando è null
        if seller_id:
            self.flyer.seller_id = seller_id
        else:
            seller_id = request.user.settings.client_id

        self.flyer.save()
        InteractiveFlyerProject.objects.filter(
            interactive_flyer=self.flyer
        ).delete()
        projects = []
        try:
            project_id = request.POST.get("projects")
            projects.append(
                self.connector.get_campaign(seller_id, int(project_id))
            )
            for project in projects:
                if prj_id := project.get("id", None):
                    InteractiveFlyerProject.objects.create(
                        interactive_flyer=self.flyer, project_id=prj_id
                    )
        except:
            pass
        ps_checkboxed_booleans_hide = (
            [  # visible checkboxes linked to booleanFields in the database
                "hide_grocery_list",
            ]
        )
        ps_checkboxed_booleans = (
            [  # visible checkboxes linked to booleanFields in the database
                "send_grocery_list_to_market",
                "marker_product_in_list",
                "ga_active",
                "show_list_check",
                "show_right_index",
                "manager_stock",
                "hide_plus_product",
                "hide_plus_product_price",
            ]
        )

        for field in self.ps._meta.get_fields():
            if field.name == "id":
                pass
            if isinstance(field, BooleanField):
                if field.name in ps_checkboxed_booleans:
                    field_value = request.POST.get(
                        field.name, False
                    )  # if not found: false
                elif field.name in ps_checkboxed_booleans_hide:
                    log_critical('FIEEEEELD',  request.POST.get(field.name))
                    field_value = not request.POST.get(
                         field.name
                    )  # if not found: false
                else:
                    # if not found: previous value
                    field_value = request.POST.get(
                        field.name, getattr(self.ps, field.name)
                    )
                # backend hide_grocery_list, opposite as frontend "Attiva lista della spesa"
                # if field.name.startswith("hide_"):
                #     field_value = not field_value
                setattr(self.ps, field.name, field_value)

            elif isinstance(field, FileField):
                # if field.name in request.FILES:
                if request.FILES.get(field.name) not in [None, ""]:
                    setattr(self.ps, field.name, request.FILES[field.name])

            elif isinstance(field, CharField):
                setattr(
                    self.ps,
                    field.name,
                    request.POST.get(field.name, getattr(self.ps, field.name)),
                )

            elif isinstance(field, IntegerField):
                value = request.POST.get(
                    field.name, getattr(self.ps, field.name)
                )
                try:
                    if value:
                        value = int(value)
                        setattr(self.ps, field.name, value)
                except Exception:
                    if "." in value or "," in value:
                        value = value.split(".")[0]
                        value = value.split(",")[0]
                        setattr(self.ps, field.name, value)

            elif isinstance(field, DateField):
                if field.name in request.POST:
                    field_value = request.POST[field.name]
                    if field_value:

                        field_date = datetime.datetime.strptime(
                            field_value, "%d/%m/%Y %H:%M"
                        )
                        if self.flyer.status == InteractiveFlyer.PUBLISHED:
                            self.flyer.status = (
                                InteractiveFlyer.SCHEDULED_FROM_PUBLISHED
                            )
                            self.flyer.save()
                        # tmp_date
                        # field_date = tmp_date.replace(
                        #     tzinfo=pytz.timezone("Europe/Rome")
                        # )
                    else:
                        field_date = None
                    setattr(self.ps, field.name, field_date)
                elif field.name in ("publicationDate", "expirationDate"):
                    field_date = None
                    setattr(self.ps, field.name, field_date)

            elif isinstance(field, JSONField):
                options = []
                for option in request.POST.getlist(f"{field.name}[]"):
                    options.append(option)
                setattr(self.ps, field.name, options)

        if banner_click := request.POST.get("banner_click", False):
            if banner_click == "1" and (
                product_banner := request.POST.get("product_banner", False)
            ):
                if product_banner == "0":
                    self.ps.product_banner = None
                    self.ps.external_banner_click = False
                    self.ps.internal_banner_click = False
                else:
                    self.ps.product_banner_id = product_banner
                    self.ps.internal_banner_click = True
                    self.ps.external_banner_click = False
            elif banner_click == "2" and (
                href_banner := request.POST.get("href_banner", False)
            ):
                self.ps.href_banner = href_banner
                self.ps.external_banner_click = True
                self.ps.internal_banner_click = False
            else:
                self.ps.external_banner_click = False
                self.ps.internal_banner_click = False
                self.ps.href_banner = ""
                self.ps.product_banner = None
        else:
            self.ps.external_banner_click = False
            self.ps.internal_banner_click = False
            self.ps.href_banner = ""
            self.ps.product_banner = None

        if (
            self.flyer.pages.count() > 35
            and self.ps.pager == ProjectSetting.PAGER_BUTTONS
        ):
            self.ps.pager = ProjectSetting.PAGER_SLIDER
            messages.warning(
                request,
                _(
                    "Il volantino ha troppe pagine ed il layout del paginatore non può essere: Bottoni"
                ),
            )

        self.ps.save()
        if "flyer_pdf" in request.FILES:
            self.flyer.flyer_pdf_file = request.FILES["flyer_pdf"]
            self.flyer.save()



        messages.success(request, "Volantino aggiornato")
        if request.POST["from_flyer"] != "True":
            return redirect("builder:dashboard")
        else:
            return redirect(
                "builder:edit_interactive_flyer",
                interactive_flyer_id=interactive_flyer_id,
            )


class CreateInteractiveFlyer(InterattivoViews, WorkerPdfPages):
    page_name = _("Crea una nuova pubblicazione")

    def get(self, request):
        if "url" in request.GET:
            self.context.update({"url": request.GET["url"]})

        if request.user.connector_type == settings.USER_TYPE_AEB:
            sellers = self.connector.get_sellers()
            self.context.update({"sellers": sellers})

        elif request.user.connector_type == settings.USER_TYPE_INTERNAL:
            projects = self.connector.get_campaigns(
                request.user.settings.client_id
            )
            self.context.update({"projects": projects})
            self.context.update({"max_file_size": settings.MAX_FILE_SIZE})
            self.context.update({"max_file_size_giodicart": settings.MAX_FILE_SIZE_GIODICART })
    
        return render(
            request,
            "builder/new/new_interactive_flyer.html",
            self.context,
        )

    def post(self, request):
        if (
            self.get_active_publications(request.user)
            >= request.user.contemporary_publications_number
        ):
            if "ajax" in request.POST:
                return JsonResponse(
                    {
                        "warning": "Limite di pubblicazioni attive raggiunto.<br>Scopri i piani di InPublish!"
                    }
                )
            else:
                messages.error(
                    request,
                    _(
                        "Limite di pubblicazioni attive raggiunto.<br>Scopri i piani di InPublish!"
                    ),
                )
                return redirect("builder:dashboard")

        if request.user.connector_type == settings.USER_TYPE_AEB:
            seller_id = request.POST["seller"]
        elif request.user.connector_type in [
            settings.USER_TYPE_INTERNAL,
            settings.USER_TYPE_GIODICART,
        ]:
            seller_id = request.user.settings.client_id
        affiliate = None
        affiliate_id = request.POST.get("affiliate", None)
        # if affiliate_id and affiliate:   # TODO ?
        #    affiliate = Affiliate.objects.get(pk=affiliate_id)
        publication_type = request.POST.get("publication-type")
        publication_type_format = request.POST["publication-type-format"]
        # publication_type = request.POST.get("publication-type-format")
        name = request.POST["name"]
        interactive_flyer = InteractiveFlyer.objects.create(
            name=name,
            user=request.user,
            seller_id=seller_id,
            project_type=request.user.connector_type,
            affiliate=affiliate,
            assets_token=get_random_string(length=10),
        )
        interactive_flyer.save()
        project_id = request.POST.get("projects", None)
        if project_id:
            InteractiveFlyerProject.objects.create(
                interactive_flyer=interactive_flyer, project_id=project_id
            )
        proj_settings = populate_project_settings_from_client_settings(
            request.user.settings, interactive_flyer
        )
        proj_settings.type = publication_type
        proj_settings.format = publication_type_format
        proj_settings.save()

        if request.POST["pdf"] == "carica" and "flyer_pdf" in request.FILES:
            interactive_flyer.flyer_pdf_file = request.FILES["flyer_pdf"]
            interactive_flyer.initialization_in_progress = True
            interactive_flyer.save()

            self.call_pages_from_pdf_worker(interactive_flyer)

        elif request.POST["pdf"] == "crea":
            interactive_flyer.status = InteractiveFlyer.WAIT_POLOTNO_PDF
            interactive_flyer.save()
            return JsonResponse(
                {
                    "data": request.POST["publication-type-format"],
                    "clientId": request.POST["seller"],
                    "flyerId": str(interactive_flyer.pk),
                }
            )

        return redirect("builder:dashboard")


class ManagePublicationInteractiveFlyer(InterattivoViews):
    def get(self, request, interactive_flyer_id, new_state):
        if new_state == "publish":
            if (
                self.get_active_publications(request.user)
                > request.user.contemporary_publications_number
            ):
                messages.warning(
                    request,
                    _(
                        "Non è possibile pubblicare il volantino."
                        "<br>Troppe pubblicazioni attive."
                        "<br>Scopri i piani di inPublish."
                    ),
                )
            else:
                try:
                    response = requests.get(
                        f"https://viewmanager.interattivo.net/inpublish/publish"
                        f"?id_volantino={self.flyer.id}"
                    )
                    self.flyer.status = InteractiveFlyer.PUBLISHED
                    self.flyer.publication_url = response.json()["url"]
                    self.flyer.save()

                    self.flyer.settings.publicationDate = timezone.now()
                    self.flyer.settings.save()
                    messages.success(request, _("Volantino pubblicato"))
                except Exception as e:
                    messages.warning(
                        request, _("Si è verificato un errore" + str(e))
                    )

        elif new_state == "re-publish":
            try:
                self.flyer.settings.save()

                requests.get(
                    f"https://viewmanager.interattivo.net/inpublish/re-publish"
                    f"?id_volantino={self.flyer.id}"
                )
                self.flyer.save()

                messages.success(request, _("Volantino aggiornato"))
            except Exception as e:
                messages.warning(request, _("Si è verificato un errore"))

            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        return redirect("builder:dashboard")


class EditInteractiveFlyer(InterattivoViews):
    page_name = _("Modifica volantino interattivo")

    def get(self, request, interactive_flyer_id):
        categories = self.connector.get_categories(
            self.request.user.settings.client_id,
            self.request.user.settings.signboard_id,
        )

        self.context.update(
            {
                "flyer": self.flyer,
                "remove_header": True,
                "remove_footer": True,
                "main_content_extra_class": "bg-gray-100",
                "categories": categories,
            }
        )

        pages_url = []
        thumbs_url = []
        for page in self.flyer.pages.all():
            pages_url.append(page.image_file)
            thumbs_url.append(page.thumb_image_file)

        index_data = {"page_url": "", "links": []}
        if self.flyer.has_index():
            index_data["page_url"] = (self.flyer.index.image_file.url,)
            index_data["links"] = InteractiveFlyerIndexLinkSerializer(
                self.flyer.index.links.all(), many=True
            ).data

        self.context.update(
            {
                "pages": {
                    "has_projects": self.flyer.projects.count() > 0,
                    "index": index_data,
                    "pages_url": pages_url,
                    "thumbs_url": thumbs_url,
                },
                "settings": self.flyer.settings,
            }
        )
        return render(
            request, "builder/new/edit_interactive_flyer.html", self.context
        )

    def post(self, request, interactive_flyer_id):
        action = request.POST.get("action")
        if action == "change-page-image-page":
            if self.flyer.has_pages():
                page_number = int(request.POST["page_number"])
                page_name = f"page_{page_number}.jpg"
                page = self.flyer.pages.filter(number=page_number)[0]

                temp_image = AWSUploader.objects.create(
                    assets_token=self.flyer.assets_token,
                )
                temp_image.image_file.save(page_name, request.FILES["image"])
                temp_image.image_file.save(
                    name=os.path.basename(temp_image.image_file.name),
                    content=ThumborServer.optimize_image(
                        temp_image.image_file.url,
                        self.flyer.image_page_width,
                        self.flyer.image_page_height,
                    )[1],
                )

                thumb_temp_image = AWSUploader.objects.create(
                    assets_token=self.flyer.assets_token,
                )
                thumb_temp_image.image_file.save(
                    f"thumb_{page_name}",
                    ThumborServer.transform_page_image(
                        temp_image.image_file.url, "200"
                    ),
                )

                page.image_file = temp_image.image_file.url
                page.thumb_image_file = thumb_temp_image.image_file.url
                page.save()
                temp_image.delete()
                thumb_temp_image.delete()
                messages.success(request, _("Immagine aggiornata"))
            else:
                messages.error(request, _("Il volantino non contiene pagine"))
        elif action == "change-page":
            if self.flyer.has_pages():
                page_to_change = int(request.POST["page_to_change"])
                page_number = int(request.POST["page_number"])
                page = self.flyer.pages.filter(number=page_to_change)[0]
                page2 = self.flyer.pages.filter(number=page_number)[0]

                page.number = page_number
                page2.number = page_to_change

                page.save()
                page2.save()
                messages.success(request, _("Posizioine pagina cambiata"))
            else:
                messages.error(request, _("Il volantino non contiene pagine"))
        elif action == "add-page":
            new_page_position = int(request.POST["page"])
            if new_page_position == 0:
                new_page_position = self.flyer.pages.count() + 1
                page_name = f"page_{new_page_position}.jpg"
            else:
                page_name = f"page_{new_page_position}_{get_random_string(length=5)}.jpg"
                pages_to_shift = self.flyer.pages.filter(
                    number__gte=new_page_position
                ).order_by("-number")
                for page_to_shift in pages_to_shift:
                    page_to_shift.number += 1
                    page_to_shift.save()

            new_page = self.flyer.pages.create(
                number=new_page_position,
            )

            temp_image = AWSUploader.objects.create(
                assets_token=self.flyer.assets_token,
            )
            temp_image.image_file.save(page_name, request.FILES["image"])
            temp_image.image_file.save(
                os.path.basename(temp_image.image_file.name),
                content=ThumborServer.optimize_image(
                    temp_image.image_file.url,
                    self.flyer.image_page_width,
                    self.flyer.image_page_height,
                )[1],
            )

            thumb_temp_image = AWSUploader.objects.create(
                assets_token=self.flyer.assets_token,
            )
            thumb_temp_image.image_file.save(
                f"thumb_{page_name}",
                ThumborServer.transform_page_image(
                    temp_image.image_file.url, "200"
                ),
            )

            new_page.image_file = temp_image.image_file.url
            new_page.thumb_image_file = thumb_temp_image.image_file.url
            new_page.save()
            temp_image.delete()
            thumb_temp_image.delete()

        return redirect(
            "builder:edit_interactive_flyer",
            interactive_flyer_id=interactive_flyer_id,
        )


class InteractiveFlyerPrevewView(LoginRequiredMixin, View):
    def get(self, request, interactive_flyer_id):
        return redirect(f"{settings.PREVIEW_URL}{interactive_flyer_id}")


class InteractiveFlyerCreateIndexView(LoginRequiredMixin, View):
    def post(self, request, interactive_flyer_id):
        flyer = InteractiveFlyer.objects.get(pk=interactive_flyer_id)
        if "image" in request.FILES:
            index, _ = InteractiveFlyerIndex.objects.get_or_create(
                interactive_flyer=flyer
            )
            index.image_file = request.FILES["image"]
            index.save()
            index.image_file.save(
                name=os.path.basename(index.image_file.name),
                content=ThumborServer.optimize_image(
                    index.image_file.url,
                    flyer.image_page_width,
                    flyer.image_page_height,
                )[1],
            )
            index.thumb_image_file.save(
                f"thumb_{index.image_file.name}",
                ThumborServer.transform_page_image(
                    index.image_file.url, "200"
                ),
            )
        return redirect(
            "builder:edit_interactive_flyer",
            interactive_flyer_id=interactive_flyer_id,
        )


class ShareFlyerView(InterattivoViews):
    page_name = _("Condividi volantino interattivo")

    def get(self, request, interactive_flyer_id):
        pages = []
        i = 1
        while i <= self.flyer.num_pages():
            pages.append(i)
            i += 1
        context = {"flyer": self.flyer, "pages": pages}
        return render(request, "builder/new/share_flyer.html", context)
