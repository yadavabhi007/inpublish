import json, tempfile
import urllib.request as urllib2
from django.core.files import File
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import resolve
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from builder.models import (
    InteractiveFlyer,
    InteractiveFlyerPage,
    InteractiveFlyerProduct,
    ProductBlueprint,
    ProductImage,
    ProductMarker,
    InteractiveFlyerIndexLink,
    IndexLinkBlueprint,
    CustomUser,
)
from builder.serializers import (
    InteractiveFlyerSerializer,
    ProjectSettingSerializer,
    InteractiveFlyerProductSerializer,
    ProductImageSerializer,
    ProductMarkerSerializer,
    InteractiveFlyerIndexLinkSerializer,
    InteractiveFlyerPortaleSerializer,
)
from builder.utils.base_class.interattivo_base_api_views import (
    InterattivoApiView,
)
from builder.utils.decorators import threaded
from utils.thumbor_server import ThumborServer
from builder.views import InterattivoViews, CounterCheck
from django.utils.translation import gettext as _
from utils.custom_logger import log_critical
from django.db.models import signals
from builder.signals import generate_json_page



class InteractiveFlyerJsonView(InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        # if not self.flyer.has_pages():
        #     if not self.flyer.pages.filter(number=0).exists():
        #         InteractiveFlyerPage.objects.create(
        #             interactive_flyer=self.flyer, number=0
        #         )
        #     page = self.flyer.pages.filter(number=0)[0]
        #     for product in self.flyer.products.all():
        #         product.interactive_flyer_page = page
        #         product.save()

        # self.flyer.save_json_file()  # TODO potrebbe servire per gli utenti enterprice

        if_serializer = InteractiveFlyerSerializer(self.flyer)
        conf_serializer = ProjectSettingSerializer(self.flyer.settings)

        return JsonResponse(
            {
                "client": {
                    "config": conf_serializer.data,
                    "leaflet": if_serializer.data,
                }
            }
        )


class InteractiveFlyerDetailJsonView(CounterCheck, InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        try:
            token = request.GET["token"]
            check_string = request.GET["check_string"]
            counter_check = self.calculate_counter_check()
        except Exception:
            return JsonResponse({"success": False, "code": 1})

        if check_string != counter_check:
            return JsonResponse(
                {"token": "ERROR IN CONTROL!", "code": 2, "success": False}
            )

        user = CustomUser.objects.get(token=token)
        if self.flyer.user.id == user.id:
            return JsonResponse(
                {
                    "success": True,
                    "flyer": InteractiveFlyerPortaleSerializer(
                        self.flyer
                    ).data,
                },
                safe=False,
            )

        return JsonResponse({"code": 3, "success": False})


@method_decorator(csrf_exempt, name="dispatch")
class InteractiveFlyersJsonView(CounterCheck, View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode())
            token = payload["token"]
            check_string = payload["check_string"]
            counter_check = self.calculate_counter_check()
        except Exception:
            return JsonResponse({"success": False, "code": 1})

        if check_string != counter_check:
            return JsonResponse(
                {"token": "ERROR IN CONTROL!", "code": 2, "success": False}
            )

        user = CustomUser.objects.get(token=token)
        if (
            resolve(request.path_info).url_name
            == "all_interactive_flyers_json"
        ):
            all_flyers = InteractiveFlyer.objects.filter(user=user).all()
            return JsonResponse(
                {
                    "success": True,
                    "flyers": InteractiveFlyerPortaleSerializer(
                        all_flyers, many=True
                    ).data,
                },
                safe=False,
            )

        past_user_flyers = InteractiveFlyer.objects.filter(
            user=user, settings__expirationDate__lt=timezone.now()
        ).order_by("-id")
        current_user_flyers = InteractiveFlyer.objects.filter(
            Q(settings__expirationDate__gt=timezone.now())
            & Q(settings__publicationDate__lt=timezone.now()),
            user=user,
        ).order_by("-id")
        future_user_flyers = InteractiveFlyer.objects.filter(
            user=user, settings__publicationDate__gt=timezone.now()
        ).order_by("-id")

        return JsonResponse(
            {
                "success": True,
                "flyers": {
                    "past": InteractiveFlyerPortaleSerializer(
                        past_user_flyers, many=True
                    ).data,
                    "current": InteractiveFlyerPortaleSerializer(
                        current_user_flyers, many=True
                    ).data,
                    "next": InteractiveFlyerPortaleSerializer(
                        future_user_flyers, many=True
                    ).data,
                },
            },
            safe=False,
        )


class SellerAffiliatesSelectView(InterattivoViews):
    def get(self, request):
        affiliates = self.connector.get_signboards(request.GET["seller_id"])
        context = {"affiliates": affiliates}
        return JsonResponse(context)


class SellerProjectsSelect(InterattivoViews):
    def get(self, request):
        projects = self.connector.get_campaigns(request.GET["seller_id"])
        context = {"projects": projects}
        return JsonResponse(context)


class ZipGenerationStatusView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        return JsonResponse(
            {
                "status": "generating"
                if self.flyer.zip_generation_in_progress
                else "generated"
            }
        )


class InteractiveFlyerDeletePageView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id, page_number):
        try:
            page = self.flyer.pages.get(number=page_number)
            page.delete()
            pages_to_change = self.flyer.pages.filter(number__gte=page_number)
            for page_to_change in pages_to_change:
                page_to_change.number = page_to_change.number - 1
                page_to_change.save()

            return JsonResponse({"success": True})
        except InteractiveFlyerPage.DoesNotExist:
            return JsonResponse({"success": False})


class InteractiveFlyerProductsPageView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id, page_number):
        try:
            products = (
                self.flyer.pages.get(number=page_number)
                .products.all()
                .order_by("-id")
            )
            if_products = InteractiveFlyerProductSerializer(
                products, many=True
            ).data
            return JsonResponse(
                {
                    "success": True,
                    "length": len(if_products),
                    "products": if_products,
                },
                safe=False,
            )
        except InteractiveFlyerPage.DoesNotExist:
            return JsonResponse({"success": False})


class SubcategoriesByCategoryView(InterattivoViews):
    def get(self, request, category_id):
        settings = request.user.settings
        subcategories = self.connector.get_subcategories(
            settings.client_id, settings.signboard_id, category_id
        )
        return JsonResponse(subcategories, safe=False)


class InteractiveFlyerProductsArchiveView(InterattivoViews):
    def get(self, request):
        settings = request.user.settings
        products = self.connector.get_products(
            settings.client_id,
            settings.signboard_id,
            id_category=None,
            term=request.GET.get("term", None),
        )
        return JsonResponse(products, safe=False)


class InteractiveFlyerProjectItemsView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        items = self.flyer.project_items(request.user.settings.client_id)
        return JsonResponse(items, safe=False)


class GetProductCampaignView(InterattivoViews):
    def get(self, request, interactive_flyer_id, product_id):
        client_id = request.user.settings.client_id
        flyer = InteractiveFlyer.objects.get(pk=interactive_flyer_id)
        campaign_id = flyer.projects.first().project_id
        item_data = self.connector.get_product_campaign(
            client_id, campaign_id, product_id
        )
        return JsonResponse(item_data)


class GetProductArchiveView(InterattivoViews):
    def get(self, request, product_id):
        client_id = request.user.settings.client_id
        item_data = self.connector.get_product(client_id, product_id)
        return JsonResponse(item_data)


class InteractiveFlyerCreateProductView(
    LoginRequiredMixin, InterattivoApiView
):
    def post(self, request, interactive_flyer_id):
        product_uid = request.POST.get("product_uid", None)
        codice_interno_insegna = request.POST.get(
            "codice_interno_insegna", None
        )
        flyer_page = None
        if "page" in request.POST:
            flyer_page = self.flyer.pages.all().get(
                number=request.POST["page"]
            )
        if "field1" in request.POST and request.POST["field1"] != "":
            field1 = request.POST.get("field1", None)
        else:
            return JsonResponse(
                {"status": "error", "message": _("Inserisci la descrizione 1")}
            )

        field2 = request.POST.get("field2", None)
        field3 = request.POST.get("field3", None)
        field4 = request.POST.get("field4", None)
        descrizione_estesa = request.POST.get("descrizione_estesa", None)
        grammage = 0
        if "grammage" in request.POST and request.POST["grammage"] != "":
            if (grmg := request.POST["grammage"]) != "":
                grammage = grmg

        price_with_iva = 0
        if (
            "price_with_iva" in request.POST
            and request.POST["price_with_iva"] != ""
        ):
            if (p_w_iva := request.POST["price_with_iva"]) != "":
                price_with_iva = p_w_iva
        else:
            return JsonResponse(
                {"status": "error", "message": _("Inserisci prezzo con IVA")}
            )
        offer_price = request.POST.get("offer_price", None)
        if offer_price == "":
            offer_price = None

        if (
            "price_for_kg" in request.POST
            and request.POST["price_for_kg"] != ""
        ):
            price_for_kg = request.POST["price_for_kg"]
        else:
            price_for_kg = None
        if "available_pieces" in request.POST:
            available_pieces = request.POST["available_pieces"]
        else:
            available_pieces = 1

        max_purchasable_pieces = None
        if "max_purchasable_pieces" in request.POST:
            if (max_p_p := request.POST["max_purchasable_pieces"]) != "-1":
                max_purchasable_pieces = max_p_p
            else:
                max_purchasable_pieces = 1

        punti = request.POST["points"]
        if "fidelity_product" in request.POST:
            fidelity_product = True
        else:
            fidelity_product = False
        if "focus" in request.POST:
            focus = True
        else:
            focus = False
        if "pam" in request.POST:
            pam = True
        else:
            pam = False
        if "three_for_two" in request.POST:
            three_for_two = True
        else:
            three_for_two = False
        if "one_and_one_gratis" in request.POST:
            one_and_one_gratis = True
        else:
            one_and_one_gratis = False
        if "underpriced_product" in request.POST:
            underpriced_product = True
        else:
            underpriced_product = False
        if "weight_unit_of_measure" in request.POST:
            weight_unit_of_measure = request.POST["weight_unit_of_measure"]

        self.get_connector(request)
        category_name = ""
        subcategory_name = ""
        if "category" in request.POST and request.POST["category"] != "":
            category = request.POST["category"]
            categories = self.connector.get_categories(
                request.user.settings.client_id,
                request.user.settings.signboard_id,
            )
            for cat in categories:
                if str(cat["id"]) == str(category):
                    category_name = cat["name"]
            subcategories = self.connector.get_subcategories(
                request.user.settings.client_id,
                request.user.settings.signboard_id,
                int(category),
            )
        else:
            return JsonResponse(
                {"status": "error", "message": _("Scegli una categoria")}
            )

        if "subcategory" in request.POST and request.POST["subcategory"] != "":
            subcategory = request.POST["subcategory"]
            for subcat in subcategories:
                if str(subcat["id"]) == str(subcategory):
                    subcategory_name = subcat["name"]
        else:
            return JsonResponse(
                {"status": "error", "message": _("Scegli una sottocategoria")}
            )

        if "equivalence" in request.POST and request.POST["equivalence"] != "":
            equivalence = request.POST["equivalence"]
        else:
            equivalence = 1
        if (
            "quantity_step" in request.POST
            and request.POST["quantity_step"] != ""
        ):
            quantity_step = request.POST["quantity_step"]
        else:
            quantity_step = 1
        if "price_label" in request.POST:
            price_label = request.POST["price_label"]
        else:
            price_label = None
        if "grocery_label" in request.POST:
            grocery_label = request.POST["grocery_label"]
        else:
            grocery_label = None

        calcolo_prezzo = request.POST.get("calcolo_prezzo", None)

        product = InteractiveFlyerProduct.objects.create(
            descrizione_estesa=descrizione_estesa,
            interactive_flyer_page=flyer_page,
            interactive_flyer=self.flyer,
            product_uid=product_uid,
            codice_interno_insegna=codice_interno_insegna,
            field1=field1,
            field2=field2,
            field3=field3,
            field4=field4,
            grammage=grammage,
            price_with_iva=price_with_iva,
            calcolo_prezzo=calcolo_prezzo,
            offer_price=offer_price,
            price_for_kg=price_for_kg,
            available_pieces=available_pieces,
            max_purchasable_pieces=max_purchasable_pieces,
            punti=punti,
            fidelity_product=fidelity_product,
            focus=focus,
            pam=pam,
            three_for_two=three_for_two,
            one_and_one_gratis=one_and_one_gratis,
            underpriced_product=underpriced_product,
            category=category,
            category_name=category_name,
            subcategory=subcategory,
            subcategory_name=subcategory_name,
            equivalence=equivalence,
            quantity_step=quantity_step,
            price_label=price_label,
            grocery_label=grocery_label,
            weight_unit_of_measure=weight_unit_of_measure,
        )
        varieties = request.POST.get("varieties", "")
        for variety in varieties.split(","):
            if variety:
                product.varieties.create(name=variety)

        if "save_categories_on_catalog" in request.POST:
            if product.item_id is not None:
                # todo versione 2 con aggiornameto dati
                pass

        if flyer_page is not None:
            coordinates_percentage = self.calculate_blueprint_percentage(
                self.flyer.image_page_width,
                self.flyer.image_page_height,
                {
                    "top": request.POST["blueprint_top"],
                    "left": request.POST["blueprint_left"],
                    "width": request.POST["blueprint_width"],
                    "height": request.POST["blueprint_height"],
                },
            )

            ProductBlueprint.objects.create(
                interactive_flyer_product=product,
                top=coordinates_percentage["top"],
                left=coordinates_percentage["left"],
                width=coordinates_percentage["width"],
                height=coordinates_percentage["height"],
            )
            product_image_cropped = ProductImage.objects.create(
                interactive_flyer_product=product,
                image_file=request.FILES["cropped_image"],
                cropped=True,
            )

            picture_url = product_image_cropped.image_file.url
            file_name, image_file = ThumborServer.optimize_image(picture_url)
            try:
                if file_name and image_file.file:
                    product_image_cropped.image_file.save(
                        file_name, image_file
                    )
            except Exception:
                pass
        ProductMarker.objects.create(
            interactive_flyer_product=product, type="plus", data=""
        )

        # TODO gestione futura
        # if item is not None:
        #     for picture in item.picture_item.all():
        #         picture_url = settings.CATALOG_IMAGES_URL + picture.low_resolution_path()
        #         file_name, image_file = ThumborServer.optimize_image(picture_url)
        #         if file_name and image_file:
        #             product_image = ProductImage.objects.create(interactive_flyer_product=product, cropped=False)
        #             product_image.image_file.save(file_name, image_file)

        modify = request.POST.get("modify", None)
        
        if 'images' in request.POST:
            images = request.POST['images'].split(',')
            for image in images:
                try:
                    # req = requests.get(image)
                    img_temp = tempfile.NamedTemporaryFile(delete=True)
                    img_temp.write(urllib2.urlopen(image).read())
                    img_temp.flush()
                    product_image = ProductImage.objects.create(
                        interactive_flyer_product=product,
                        image_file=File(img_temp),
                    )
                    product_image.save()
                except Exception as e:
                    log_critical('Errore immagine', e)
        
        

        return JsonResponse(
            {
                "status": "created",
                "product": InteractiveFlyerProductSerializer(product).data,
                "modify": modify == "1",
            }
        )

class UpdateGiodicartProductView(LoginRequiredMixin, InterattivoApiView):
    def post(self, request, interactive_flyer_id, product_id):
        product = InteractiveFlyerProduct.objects.get(pk=product_id)
        if "field1" in request.POST and request.POST["field1"] != "":
            product.field1 = request.POST.get("field1", None)
        else:
            return JsonResponse(
                {"status": "error", "message": _("Inserisci la descrizione 1")}
            )

        product.field2 = request.POST.get("field2", None)
        product.field3 = request.POST.get("field3", None)
        product.field4 = request.POST.get("field4", None)
        product.descrizione_estesa = request.POST.get(
            "descrizione_estesa", None
        )

        product.save()

        try:
            coordinates_percentage = self.calculate_blueprint_percentage(
                self.flyer.image_page_width,
                self.flyer.image_page_height,
                {
                    "top": request.POST["blueprint_top"],
                    "left": request.POST["blueprint_left"],
                    "width": request.POST["blueprint_width"],
                    "height": request.POST["blueprint_height"],
                },
            )

            product.blueprint.top = coordinates_percentage["top"]
            product.blueprint.left = coordinates_percentage["left"]
            product.blueprint.width = coordinates_percentage["width"]
            product.blueprint.height = coordinates_percentage["height"]
            product.blueprint.save()
        except:
            pass

        modify = request.POST.get("modify", None)
        return JsonResponse(
            {
                "status": "updated",
                "product": InteractiveFlyerProductSerializer(product).data,
                "modify": modify == "1",
            }
        )


class CreateGiodicartProductView(LoginRequiredMixin, InterattivoApiView):
    def post(self, request, interactive_flyer_id):
        flyer_page = None
        if "page" in request.POST:
            flyer_page = self.flyer.pages.filter(
                number=request.POST["page"]
            ).first()

        json_product = json.loads(request.POST.get("json"))

        codice_interno_insegna = json_product["codice_interno_insegna"]
        if "field1" in request.POST and request.POST["field1"] != "":
            field1 = request.POST.get("field1", None)
        else:
            return JsonResponse(
                {"status": "error", "message": _("Inserisci la descrizione 1")}
            )

        field2 = request.POST.get("field2", None)
        field3 = request.POST.get("field3", None)
        field4 = request.POST.get("field4", None)
        descrizione_estesa = request.POST.get("descrizione_estesa", None)
        grammage = 0
        price_with_iva = json_product["price"]
        try:
            decimal_part = price_with_iva.split(".")[1]
            if len(decimal_part) == 1:
                price_with_iva = f"{price_with_iva}0"
        except:
            pass
        offer_price = None

        price_for_kg = None
        available_pieces = 1
        max_purchasable_pieces = 1

        punti = 0
        fidelity_product = False
        focus = False
        pam = False
        three_for_two = False
        one_and_one_gratis = False
        underpriced_product = False

        self.get_connector(request)
        category = ""
        subcategory = ""
        category_name = ""
        subcategory_name = ""
        if json_product["id_category"] and json_product["category"]:
            category = json_product["id_category"]
            category_name = json_product["category"]

        if json_product["id_subcategory"] and json_product["subcategory"]:
            subcategory = json_product["id_subcategory"]
            subcategory_name = json_product["subcategory"]

        equivalence = 1
        quantity_step = 1
        price_label = f"{request.user.settings.price_label} {price_with_iva}"
        grocery_label = "pz."
        calcolo_prezzo = None

        sku = json_product["sku"]
        product_uid = json_product["skul"]
        # if json_product["product_id"] != "":
        #     product_uid = (
        #         f"{codice_interno_insegna}.{json_product['product_id']}"
        #     )

        product = InteractiveFlyerProduct.objects.create(
            descrizione_estesa=descrizione_estesa,
            interactive_flyer_page=flyer_page,
            interactive_flyer=self.flyer,
            sku=sku,
            product_uid=product_uid,
            codice_interno_insegna=codice_interno_insegna,
            field1=field1,
            field2=field2,
            field3=field3,
            field4=field4,
            grammage=grammage,
            price_with_iva=price_with_iva,
            calcolo_prezzo=calcolo_prezzo,
            offer_price=offer_price,
            price_for_kg=price_for_kg,
            available_pieces=available_pieces,
            max_purchasable_pieces=max_purchasable_pieces,
            punti=punti,
            fidelity_product=fidelity_product,
            focus=focus,
            pam=pam,
            three_for_two=three_for_two,
            one_and_one_gratis=one_and_one_gratis,
            underpriced_product=underpriced_product,
            category=category,
            category_name=category_name,
            subcategory=subcategory,
            subcategory_name=subcategory_name,
            equivalence=equivalence,
            quantity_step=quantity_step,
            price_label=price_label,
            grocery_label=grocery_label,
            weight_unit_of_measure=None,
            strike_price=json_product["strike_price"],
            discount_rate=int(json_product["discount_rate"]),
            prices=json_product["prices"],
            promo=json_product["promo"],
            stock=json_product["stock"],
            tdc=json_product["tdc"],
            available_from=json_product["from"],
            brand=json_product["brand"],
            brand_logo=json_product["brand_logo"],
            line=json_product["line"],
            line_logo=json_product["line_logo"],
        )

        self.post_save_product_actions(json_product, product, True)
        product.save()

        if flyer_page is not None:
            coordinates_percentage = self.calculate_blueprint_percentage(
                self.flyer.image_page_width,
                self.flyer.image_page_height,
                {
                    "top": request.POST["blueprint_top"],
                    "left": request.POST["blueprint_left"],
                    "width": request.POST["blueprint_width"],
                    "height": request.POST["blueprint_height"],
                },
            )

            ProductBlueprint.objects.create(
                interactive_flyer_product=product,
                top=coordinates_percentage["top"],
                left=coordinates_percentage["left"],
                width=coordinates_percentage["width"],
                height=coordinates_percentage["height"],
            )

        # gestione related
        
        if json_product["related"]:
            log_critical('JSON', json_product["related"])
            self.related_product(json_product["related"],product,descrizione_estesa,flyer_page,codice_interno_insegna,field1,field2,field3,field4,grammage,price_with_iva,calcolo_prezzo,offer_price,
                        price_for_kg,available_pieces, max_purchasable_pieces, punti, fidelity_product, focus, pam, three_for_two, one_and_one_gratis, underpriced_product, category, 
                        category_name, subcategory, subcategory_name, equivalence, quantity_step, price_label,grocery_label)

        modify = request.POST.get("modify", None)
        return JsonResponse(
            {
                "status": "created",
                "product": InteractiveFlyerProductSerializer(product).data,
                "modify": modify == "1",
            }
        )

    @threaded
    def related_product(self, json_product,product,descrizione_estesa,flyer_page,codice_interno_insegna,field1,field2,field3,field4,grammage,price_with_iva,calcolo_prezzo,offer_price,
                        price_for_kg,available_pieces, max_purchasable_pieces, punti, fidelity_product, focus, pam, three_for_two, one_and_one_gratis, underpriced_product, category, 
                        category_name, subcategory, subcategory_name, equivalence, quantity_step, price_label,grocery_label
    ):
        for related_product in json_product:
                brand = ""
                brand_logo = ""
                line = ""
                line_logo = ""
                if "brand" in related_product:
                    brand = related_product['brand']
                if "brand_logo" in related_product:
                    brand_logo = related_product['brand_logo']
                if "line" in related_product:
                    line = related_product['line']
                if "line_logo" in related_product:
                    line_logo = related_product['line_logo']
                rel_product = InteractiveFlyerProduct.objects.create(
                    principal_product=product,
                    descrizione_estesa=descrizione_estesa,
                    interactive_flyer_page=flyer_page,
                    interactive_flyer= self.flyer,
                    sku=related_product["sku"],
                    product_uid = related_product["skul"],
                    # product_uid=related_product["codice_interno_insegna"]
                    # + "."
                    # + related_product["product_id"]
                    # if related_product["product_id"] != ""
                    # else related_product["codice_interno_insegna"],
                    codice_interno_insegna=codice_interno_insegna,
                    field1=field1,
                    field2=field2,
                    field3=field3,
                    field4=field4,
                    grammage=grammage,
                    price_with_iva=price_with_iva,
                    calcolo_prezzo=calcolo_prezzo,
                    offer_price=offer_price,
                    price_for_kg=price_for_kg,
                    available_pieces=available_pieces,
                    max_purchasable_pieces=max_purchasable_pieces,
                    punti=punti,
                    fidelity_product=fidelity_product,
                    focus=focus,
                    pam=pam,
                    three_for_two = three_for_two,
                    one_and_one_gratis=one_and_one_gratis,
                    underpriced_product=underpriced_product,
                    category=category,
                    category_name=category_name,
                    subcategory=subcategory,
                    subcategory_name=subcategory_name,
                    equivalence=equivalence,
                    quantity_step=quantity_step,
                    price_label=price_label,
                    grocery_label=grocery_label,
                    weight_unit_of_measure=None,
                    strike_price= related_product["strike_price"],
                    discount_rate=int(related_product["discount_rate"]),
                    prices=related_product["prices"],
                    promo=related_product["promo"],
                    stock=related_product["stock"],
                    tdc=related_product["tdc"],
                    available_from=related_product["from"],
                    brand=brand,
                    brand_logo=brand_logo,
                    line=line,
                    line_logo=line_logo,
                )
                self.post_save_product_actions(related_product, rel_product)
                rel_product.save()
                log_critical('SALVATO','Prodotto numero: ' + str(rel_product.pk))

    def post_save_product_actions(self, json_product, product, principal=None):
        ProductMarker.objects.create(
            interactive_flyer_product=product, type="plus", data=""
        )
        if json_product["photo"]:
            with tempfile.TemporaryFile() as img_product_file:
                r = requests.get(json_product["photo"])
                img_product_file.write(r.content)
                img_product_file.seek(0)

                an_image = ProductImage.objects.create(
                    interactive_flyer_product=product,
                    cropped=True if principal else False,
                )
                an_image.image_file.save(
                    f"{json_product['codice_interno_insegna']}{get_random_string(4)}.jpg",
                    img_product_file,
                )

                file_name, image_file = ThumborServer.optimize_image(
                    an_image.image_file.url
                )
                try:
                    if file_name and image_file.file:
                        an_image.image_file.save(file_name, image_file)
                except Exception as e:
                    log_critical("ERROR", e)

        for variety in json_product["varieties"]:
            if variety:
                product.varieties.create(name=variety)


class InteractiveFlyerEditProductView(LoginRequiredMixin, InterattivoApiView):
    def post(self, request, interactive_flyer_id, product_id):
        product = InteractiveFlyerProduct.objects.get(pk=product_id)
        flyer_page = None
        if self.flyer.has_pages():
            flyer_page = product.interactive_flyer_page
        if request.POST["field1"] != "":
            product.field1 = request.POST.get("field1", None)
        else:
            return JsonResponse(
                {"status": "error", "message": "Inserisci la descrizione 1"}
            )
        product.field2 = request.POST.get("field2", None)
        product.field3 = request.POST.get("field3", None)
        product.field4 = request.POST.get("field4", None)
        product.descrizione_estesa = request.POST.get(
            "descrizione_estesa", None
        )

        self.get_connector(request)
        subcategories = []
        if "category" in request.POST and request.POST["category"] != "":
            category = request.POST["category"]
            categories = self.connector.get_categories(
                request.user.settings.client_id,
                request.user.settings.signboard_id,
            )
            for cat in categories:
                if str(cat["id"]) == str(category):
                    product.category_name = cat["name"]
            subcategories = self.connector.get_subcategories(
                request.user.settings.client_id,
                request.user.settings.signboard_id,
                int(category),
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Scegli una categoria"}
            )
            category = None
            product.category_name = ""
        product.category = category

        if "subcategory" in request.POST and request.POST["subcategory"] != "":
            subcategory = request.POST["subcategory"]
            for subcat in subcategories:
                if str(subcat["id"]) == str(subcategory):
                    product.subcategory_name = subcat["name"]
        else:
            return JsonResponse(
                {"status": "error", "message": "Scegli una sottocategoria"}
            )
            subcategory = None
            product.subcategory_name = ""
        product.subcategory = subcategory

        product.price_label = request.POST["price_label"]
        product.grocery_label = request.POST["grocery_label"]
        product.price_with_iva = 0
        if "price_with_iva" in request.POST:
            if (p_w_iva := request.POST["price_with_iva"]) != "":
                product.price_with_iva = p_w_iva

        product.offer_price = None
        if "offer_price" in request.POST:
            if (offer_price := request.POST["offer_price"]) != "":
                product.offer_price = offer_price

        product.grammage = 0
        if "grammage" in request.POST and request.POST["grammage"] != "":
            if (grmg := request.POST["grammage"]) != "":
                product.grammage = grmg

        product.calcolo_prezzo = request.POST.get(
            "calcolo_prezzo", product.calcolo_prezzo
        )
        if "equivalence" in request.POST and request.POST["equivalence"] != "":
            product.equivalence = request.POST.get(
                "equivalence", product.equivalence
            )
        else:
            product.equivalence = 1
        if (
            "quantity_step" in request.POST
            and request.POST["quantity_step"] != ""
        ):
            product.quantity_step = request.POST.get(
                "quantity_step", product.quantity_step
            )
        else:
            product.quantity_step = 1
        if (
            "price_for_kg" in request.POST
            and request.POST["price_for_kg"] != ""
        ):
            price_for_kg = request.POST["price_for_kg"]
        else:
            price_for_kg = None
        product.price_for_kg = price_for_kg
        if (
            "available_pieces" in request.POST
            and request.POST["available_pieces"] != ""
        ):
            available_pieces = request.POST["available_pieces"]
        else:
            available_pieces = 1
        product.available_pieces = available_pieces

        if (
            "max_purchasable_pieces" in request.POST
            and request.POST["max_purchasable_pieces"] != ""
        ):
            if (max_p_p := request.POST["max_purchasable_pieces"]) != "-1":
                product.max_purchasable_pieces = max_p_p
            else:
                product.max_purchasable_pieces = 1

        product.punti = request.POST["points"]
        product.fidelity_product = "fidelity_product" in request.POST
        product.focus = "focus" in request.POST
        product.pam = "pam" in request.POST
        product.three_for_two = "three_for_two" in request.POST
        product.one_and_one_gratis = "one_and_one_gratis" in request.POST
        product.underpriced_product = "underpriced_product" in request.POST

        product.save()

        product.varieties.all().delete()
        varieties = request.POST.get("varieties", "")
        for variety in varieties.split(","):
            if variety:
                product.varieties.create(name=variety)

        if "save_categories_on_catalog" in request.POST:
            if product.item_id is not None:
                # item = Item.objects.get(pk=product.item_id)
                # aeb_product = item.product
                # aeb_category = Category.objects.filter(name=category)[0]
                # aeb_subcategory = Subcategory.objects.filter(name=subcategory)[0]
                # aeb_product.category = aeb_category
                # aeb_product.subcategory = aeb_subcategory
                # aeb_product.save()
                # TODO per la versione 2.0
                pass

        if flyer_page is not None:
            coordinates_percentage = self.calculate_blueprint_percentage(
                self.flyer.image_page_width,
                self.flyer.image_page_height,
                {
                    "top": request.POST["blueprint_top"],
                    "left": request.POST["blueprint_left"],
                    "width": request.POST["blueprint_width"],
                    "height": request.POST["blueprint_height"],
                },
            )

            product.blueprint.top = coordinates_percentage["top"]
            product.blueprint.left = coordinates_percentage["left"]
            product.blueprint.width = coordinates_percentage["width"]
            product.blueprint.height = coordinates_percentage["height"]
            product.blueprint.save()

            product_image_cropped = product.images.filter(cropped=True)[0]
            product_image_cropped.image_file = request.FILES["cropped_image"]
            product_image_cropped.save()

            picture_url = product_image_cropped.image_file.url
            file_name, image_file = ThumborServer.optimize_image(picture_url)
            try:
                if file_name and image_file.file:
                    product_image_cropped.image_file.save(
                        file_name, image_file
                    )
            except Exception:
                pass

        # for picture in item.picture_item.all():
        #     pitcure_url = settings.CATALOG_IMAGES_URL + picture.low_resolution_path()
        #     resp = requests.get(thumbor_url + pitcure_url)
        #     if resp.status_code == requests.codes.ok:
        #         fp = BytesIO()
        #         fp.write(resp.content)
        #         file_name = pitcure_url.split("/")[-1]
        #         product_image = ProductImage.objects.create(
        #             interactive_flyer_product=product, cropped=False)
        #         product_image.image_file.save(file_name, files.File(fp))

        modify = request.POST.get("modify", None)
        return JsonResponse(
            {
                "status": "updated",
                "product": InteractiveFlyerProductSerializer(product).data,
                "modify": modify == "1",
            }
        )


class InteractiveFlyerDeleteProductView(LoginRequiredMixin, View):
    def get(self, request, interactive_flyer_id, product_id):
        InteractiveFlyerProduct.objects.get(pk=product_id).delete()
        return JsonResponse({"status": "deleted"})


class GetProductImagesView(LoginRequiredMixin, View):
    def get(self, request, interactive_flyer_id, product_id):
        product_images = ProductImage.objects.filter(
            interactive_flyer_product_id=product_id
        )
        return JsonResponse(
            ProductImageSerializer(product_images, many=True).data, safe=False
        )


class InteractiveFlyerCreateProductImageView(LoginRequiredMixin, View):
    def post(self, request, interactive_flyer_id, product_id):
        product = InteractiveFlyerProduct.objects.get(pk=product_id)

        product_image = ProductImage.objects.create(
            interactive_flyer_product=product,
            image_file=request.FILES["image"],
        )
        picture_url = product_image.image_file.url
        file_name, image_file = ThumborServer.optimize_image(picture_url)
        try:
            if file_name and image_file.file:
                product_image.image_file.save(file_name, image_file)
        except:
            pass

        return JsonResponse({"status": "created"})


class InteractiveFlyerDeleteProductImageView(LoginRequiredMixin, View):
    def get(self, request, interactive_flyer_id, product_id, image_id):
        ProductImage.objects.get(pk=image_id).delete()
        return JsonResponse({"status": "deleted"})


class InteractiveFlyerProductInteractivityView(
    LoginRequiredMixin, InterattivoApiView
):
    def post(
        self, request, interactive_flyer_id, product_id, interaction_type
    ):
        product = InteractiveFlyerProduct.objects.get(pk=product_id)
        tmp_interaction_type = (
            "play" if interaction_type == "video" else interaction_type
        )
        try:
            marker = product.markers.get(type=tmp_interaction_type)
        except ProductMarker.DoesNotExist:
            marker = product.markers.create(
                type=tmp_interaction_type, active=False
            )
        marker.active = "active" in request.POST
        marker.title = request.POST.get("title", None)
        process_image = False
        # region product interactivity
        if interaction_type == "world":
            marker.link = request.POST.get("link", None)
        elif interaction_type in ("play", "video"):
            if not "do-nothing" in request.POST:
                marker.link = request.POST.get(
                    "link", None
                )  # per il link di youtube
            if interaction_type == "video":
                process_image = True

            marker.tooltip = request.POST.get("tooltip", None)
            marker.open_modal = request.POST.get("open_modal", False)
            marker.show_icon = "show_icon" in request.POST
            # TODO (sviluppi futuri) aggiungi il controllo sul link per decidere l'host del video
            if "video_file" in request.FILES:
                marker.video_type = "video_file"
                if not "do-nothing" in request.POST:
                    marker.video_file = request.FILES["video_file"]
                    marker.link = None
            else:
                if not "do-nothing" in request.POST:
                    marker.video_type = "youtube"
                    marker.video_file = None

        elif interaction_type == "hat-chef":
            marker.ingredients = request.POST.get("ingredients", None)
            marker.recipe = request.POST.get("recipe", "")

        elif interaction_type == "info":
            marker.content_title = request.POST.get("content_title", None)
            marker.content_text = request.POST.get("content_text", None)

        elif interaction_type == "specs":
            marker.content_text = request.POST.get("content_text", None)
        # endregion

        # region page interactivity
        elif interaction_type == "external_link":
            process_image = True
            marker.link_type = request.POST.get("link_type", None)
            marker.link = request.POST.get("link", None)

            marker.tooltip = request.POST.get("tooltip", None)
            marker.show_icon = "show_icon" in request.POST

        elif interaction_type == "internal_link":
            process_image = True
            marker.page_number = request.POST.get("page_number", 0)
            marker.tooltip = request.POST.get("tooltip", None)
            marker.show_icon = "show_icon" in request.POST
        # endregion

        if "image_file" in request.FILES:
            if marker.images.count() > 0:
                image = marker.images.all()[0]
            else:
                image = marker.images.create()
            image.image_file = request.FILES["image_file"]
            image.save()

        if process_image:
            coordinates_percentage = self.calculate_blueprint_percentage(
                self.flyer.image_page_width,
                self.flyer.image_page_height,
                {
                    "top": request.POST["blueprint_top"],
                    "left": request.POST["blueprint_left"],
                    "width": request.POST["blueprint_width"],
                    "height": request.POST["blueprint_height"],
                },
            )

            product.blueprint.top = coordinates_percentage["top"]
            product.blueprint.left = coordinates_percentage["left"]
            product.blueprint.width = coordinates_percentage["width"]
            product.blueprint.height = coordinates_percentage["height"]
            product.blueprint.save()

            product.images.get(cropped=True).delete()
            product_image_cropped = ProductImage.objects.create(
                interactive_flyer_product=product,
                image_file=request.FILES["cropped_image"],
                cropped=True,
            )
            product.save()
            picture_url = product_image_cropped.image_file.url
            file_name, image_file = ThumborServer.optimize_image(picture_url)
            try:
                if file_name and image_file.file:
                    product_image_cropped.image_file.save(
                        file_name, image_file
                    )
            except Exception:
                pass
        marker.save()
        pm_serialized = ProductMarkerSerializer(marker)
        # if marker.active:
        return JsonResponse(
            {
                "status": "ok",
                "product": InteractiveFlyerProductSerializer(product).data,
                "marker": pm_serialized.data,
            }
        )
        # else:
        #     return JsonResponse(
        #         {
        #             "status": "false",
        #             "product": InteractiveFlyerProductSerializer(product).data,
        #             "marker": pm_serialized.data,
        #         }
        #     )


class InteractiveFlyerIndexLinksView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        links_serialized = InteractiveFlyerIndexLinkSerializer(
            self.flyer.index.links.all(), many=True
        )
        return JsonResponse({"status": "ok", "links": links_serialized.data})


class InteractiveFlyerIndexDeleteView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        self.flyer.index.delete()
        return JsonResponse({"status": "deleted"})


class InteractiveFlyerCreateIndexLinkView(
    LoginRequiredMixin, InterattivoApiView
):
    def post(self, request, interactive_flyer_id):
        page = request.POST.get("page", -1)
        external_url = request.POST.get("url", "")
        title = request.POST.get("title", "")
        color = request.POST.get("color", "#000000")
        index_type = InteractiveFlyerIndexLink.TYPE_EXTERNAL_LINK
        if external_url == "":
            index_type = InteractiveFlyerIndexLink.TYPE_INTERNAL_LINK

        index_link = InteractiveFlyerIndexLink.objects.create(
            interactive_flyer_index=self.flyer.index,
            page=page,
            url=external_url,
            type=index_type,
            color=color,
            title=title,
        )

        coordinates_percentage = self.calculate_blueprint_percentage(
            self.flyer.image_page_width,
            self.flyer.image_page_height,
            {
                "top": request.POST["blueprint_top"],
                "left": request.POST["blueprint_left"],
                "width": request.POST["blueprint_width"],
                "height": request.POST["blueprint_height"],
            },
        )

        IndexLinkBlueprint.objects.create(
            interactive_flyer_index_link=index_link,
            top=coordinates_percentage["top"],
            left=coordinates_percentage["left"],
            width=coordinates_percentage["width"],
            height=coordinates_percentage["height"],
        )

        return JsonResponse(
            {
                "status": "created",
                "index": InteractiveFlyerIndexLinkSerializer(index_link).data,
            }
        )


class InteractiveFlyerEditIndexLinkView(
    LoginRequiredMixin, InterattivoApiView
):
    def post(self, request, interactive_flyer_id, link_id):
        link = self.flyer.index.links.get(pk=link_id)
        link.page = request.POST.get("page", -1)
        link.url = request.POST.get("url", "")
        link.title = request.POST.get("title", "")
        link.color = request.POST.get("color", "#000000")
        link.save()

        coordinates_percentage = self.calculate_blueprint_percentage(
            self.flyer.image_page_width,
            self.flyer.image_page_height,
            {
                "top": request.POST["blueprint_top"],
                "left": request.POST["blueprint_left"],
                "width": request.POST["blueprint_width"],
                "height": request.POST["blueprint_height"],
            },
        )

        link.blueprint.top = coordinates_percentage["top"]
        link.blueprint.left = coordinates_percentage["left"]
        link.blueprint.width = coordinates_percentage["width"]
        link.blueprint.height = coordinates_percentage["height"]
        link.blueprint.save()

        return JsonResponse(
            {
                "status": "updated",
                "index": InteractiveFlyerIndexLinkSerializer(link).data,
            }
        )


class InteractiveFlyerDeleteIndexLinkView(
    LoginRequiredMixin, InterattivoApiView
):
    def get(self, request, interactive_flyer_id, link_id):
        self.flyer.index.links.get(pk=link_id).delete()
        return JsonResponse({"status": "deleted"})


class GetPriceLabelsApiView(LoginRequiredMixin, InterattivoApiView):
    def get(self, request, interactive_flyer_id):
        settings = self.flyer.settings
        return JsonResponse(
            {
                "status": "ok",
                "piece_label": settings.piece_label,
                "price_label": settings.price_label,
                "kg_label": settings.kg_label,
                "gr_label": settings.gr_label,
                "hectogram_label": settings.hectogram_label,
                "kg_price_label": settings.kg_price_label,
                "hectogram_price_label": settings.hectogram_price_label,
            }
        )


class InteractiveFlyerInteractivityView(
    LoginRequiredMixin, InterattivoApiView
):
    def post(self, request, interactive_flyer_id, interaction_type):
        flyer_page = None
        if "page" in request.POST:
            flyer_page = self.flyer.pages.all().get(
                number=request.POST["page"]
            )

        if (
            interaction_type in InteractiveFlyerProduct.TYPE_CHOICES_KEYS
            and flyer_page
        ):
            product = InteractiveFlyerProduct.objects.create(
                interactive_flyer_page=flyer_page,
                interactive_flyer=self.flyer,
                type=interaction_type,
            )

            coordinates_percentage = self.calculate_blueprint_percentage(
                self.flyer.image_page_width,
                self.flyer.image_page_height,
                {
                    "top": request.POST["blueprint_top"],
                    "left": request.POST["blueprint_left"],
                    "width": request.POST["blueprint_width"],
                    "height": request.POST["blueprint_height"],
                },
            )

            blueprint = ProductBlueprint.objects.create(
                interactive_flyer_product=product,
                top=coordinates_percentage["top"],
                left=coordinates_percentage["left"],
                width=coordinates_percentage["width"],
                height=coordinates_percentage["height"],
            )
            blueprint.save()
            product_image_cropped = ProductImage.objects.create(
                interactive_flyer_product=product,
                image_file=request.FILES["cropped_image"],
                cropped=True,
            )

            picture_url = product_image_cropped.image_file.url
            file_name, image_file = ThumborServer.optimize_image(picture_url)
            try:
                if file_name and image_file.file:
                    product_image_cropped.image_file.save(
                        file_name, image_file
                    )
            except:
                pass
            product_image_cropped.save()
            marker = product.markers.create(type=interaction_type)
            show_icon = request.POST.get("show_icon", False)
            tooltip = request.POST.get("tooltip", "")
            if interaction_type == "external_link":
                marker.link_type = request.POST.get("link_type", None)
                marker.link = request.POST.get("link", None)

            elif interaction_type == "internal_link":
                marker.page_number = request.POST.get("page_number", None)

            elif interaction_type == "video":
                marker.type = "play"
                marker.video_type = request.POST.get("video_type", None)
                marker.link = request.POST.get("link", None)
                marker.open_modal = request.POST.get("open_modal", False)
                if "video_file" in request.FILES:
                    marker.video_file = request.FILES["video_file"]

            marker.show_icon = show_icon
            marker.tooltip = tooltip
            marker.save()
            return JsonResponse(
                {
                    "status": "created",
                    "product": InteractiveFlyerProductSerializer(product).data,
                }
            )

        return JsonResponse({"status": "error"})


@method_decorator(csrf_exempt, name="dispatch")
class ReceivePagesView(InterattivoApiView):
    @threaded
    def job(self, rqst):
        if not rqst["error"]:
            try:
                for page in rqst["pages"]:
                    number = page["number"]
                    if_page = self.flyer.pages.create(
                        number=number,
                    )
                    if_page.image_file = page["image_file"]
                    if_page.thumb_image_file = page["thumb_image_file"]
                    if_page.save()

                self.flyer.image_page_height = rqst["height"]
                self.flyer.image_page_width = rqst["width"]
                self.flyer.initialization_in_progress = False
                self.flyer.save()
            except Exception as e:
                self.flyer.initialization_in_progress = False
                self.flyer.initialization_error = True
                self.flyer.initialization_error_message = str(e)
                self.flyer.save()
        else:
            self.flyer.initialization_in_progress = False
            self.flyer.initialization_error = True
            self.flyer.initialization_error_message = rqst["error_message"]
            self.flyer.save()

        # todo cancella il volantino dal worker?
        # delete_flyer_url = reverse(
        #     "worker:delete_flyer",
        #     kwargs={"interactive_flyer_id": self.flyer_worker.flyer_id},
        # )
        # requests.get(
        #     f"{settings.WORKER_URL}{delete_flyer_url}"
        # )

    def post(self, request, interactive_flyer_id):
        rqst = json.loads(request.body.decode())
        self.job(rqst)

        return JsonResponse({"success": True})


class GiodicartSearchProductView(InterattivoApiView):
    def post(self, request):
        skul = request.POST.get("skul", None)
        if skul:
            self.get_connector(request)
            product = self.connector.get_product(0, skul)
            return JsonResponse(product)
        else:
            return JsonResponse({"success": False})

class SearchProductView(InterattivoApiView):
    def get(self, request):
        client_id = request.GET.get("client_id", None)
        item_id = request.GET.get("item_id", None)
        try:
            product = InteractiveFlyerProduct.objects.get(pk = item_id)
            related = InteractiveFlyerProduct.objects.filter(principal_product = item_id)
            return JsonResponse({
                    "success" : True,
                    "product" : InteractiveFlyerProductSerializer(product).data,
                    "related" : InteractiveFlyerProductSerializer(related, many = True ).data,
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "Product not found",
                "excpetion" : str(e)
            })
