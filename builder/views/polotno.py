from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from builder.models import PolotnoToken
from builder.utils.base_class.polotno_base_class import PolotnoBaseClass


class PolotnoAuthView(PolotnoBaseClass):
    def get(self, request):
        # ricevo: token
        # restituisco: success, token e params

        try:
            token = PolotnoToken.objects.get(key=request.GET.get("token"))
            args = {
                "user": token.user,
                "action": token.action,
                "id_format": token.id_format,
                "id_template": token.id_template,
                "interactive_flyer_id": None,
                "type": token.type,
                "tab_id": token.tab_id,
            }

            if token.interactive_flyer is not None:
                args["interactive_flyer_id"] = token.interactive_flyer.id

            token.delete()
            token = PolotnoToken.objects.create(**args)

            return JsonResponse(
                {
                    "success": True,
                    "token": token.key,
                    "params": {
                        "action": token.action,
                        "id_client": token.user.settings.client_id,
                        "id_template": token.id_template,
                        "id_format": token.id_format,
                        "tab_id": token.tab_id,
                    },
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "exception": str(e)})

    def post(self, request):
        if request.user.is_authenticated:
            args = {
                "user": request.user,
                "interactive_flyer_id": request.POST.get(
                    "interactive_flyer_id", None
                ),
                "action": request.POST.get("action", "new"),
                "id_format": request.POST.get("id_format"),
                "id_template": request.POST.get("id_template"),
                "type": request.POST.get("type"),
                "tab_id": request.POST.get("tab_id"),
            }
            try:
                token = PolotnoToken.objects.create(**args)
            except:
                token = PolotnoToken.objects.get(user=request.user)
                token.delete()
                token = PolotnoToken.objects.create(**args)

            if args["action"] == "choose":
                img_temp, filename = self.download_image_by_url(
                    request.POST.get("template_url")
                )
                self.execute_action_by_type(token, img_temp, filename)

            return JsonResponse({"success": True, "token": token.key})

        return JsonResponse({"success": False})


@method_decorator(csrf_exempt, name="dispatch")
class PolotnoView(PolotnoBaseClass):
    def post(self, request):
        # ricevo: client_id, token
        # restituisco: success

        custom_user, token = self.check_user_and_token(request.POST)

        if custom_user and token:
            undo = request.POST.get("undo") == "true"
            if undo and token.type in (
                "Volantino A4",
                "Volantino quadrato",
                "13",
                "14",
                "5",
                "6",
            ):
                token.interactive_flyer.delete()

            elif not undo:
                image_url = request.POST.get("url")
                img_temp, filename = self.download_image_by_url(image_url)
                self.execute_action_by_type(token, img_temp, filename)

                img_temp.close()

            return JsonResponse(
                {
                    "success": True,
                }
            )

        return JsonResponse({"success": False})

    def get(self, request):
        # ricevo: client_id, token
        custom_user, token = self.check_user_and_token(request.GET)

        if custom_user and token:
            if token.interactive_flyer:
                i_flyer_id = token.interactive_flyer.id

            login(request, custom_user)

            if token.type == "index":
                redirect_url = redirect(
                    reverse(
                        "builder:edit_interactive_flyer",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                )
            elif token.type == "ogImageMeta":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type == "ogImageMeta_mobile":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type == "clientIcon":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type == "category_banner":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type == "category_banner_mobile":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type == "product_banner":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type == "logo_full":
                redirect_url = redirect(
                    reverse(
                        "builder:interactive_flyer_settings",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                    + "?tab_id="
                    + token.tab_id
                )
            elif token.type in (
                "Volantino A4",
                "Volantino quadrato",
                "13",
                "14",
                "5",
                "6",
            ):
                redirect_url = redirect(
                    reverse("builder:dashboard", kwargs={})
                )
            elif token.type in ("clientIconC", "brandImageC"):
                redirect_url = redirect(reverse("builder:setting_client"))
            else:
                redirect_url = redirect(
                    reverse(
                        "builder:edit_interactive_flyer",
                        kwargs={"interactive_flyer_id": i_flyer_id},
                    )
                )
            # todo aggiungi altri tipi

            token.delete()
            return redirect_url

        return redirect("builder:error_page")
