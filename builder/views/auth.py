import json

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from builder.models import ClientSetting
from builder.my_backend import MyBackend
from builder.utils.base_class.permissions_class import (
    PermissionsUtils,
    CounterCheck,
)


@method_decorator(csrf_exempt, name="dispatch")
class NewUserView(CounterCheck, View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode())
            email = payload["email"]
            client_id = payload["client_id"]
            signboard_id = payload["signboard_id"]
            release_id = payload["release_id"]
            check_string = payload["check_string"]
            client_code = payload.get("client_code", None)
            counter_check = self.calculate_counter_check()
        except Exception:
            return JsonResponse({"success": False, "code": 1})

        if check_string != counter_check:
            return JsonResponse(
                {
                    "email": email,
                    "token": "ERROR IN CONTROL!",
                    "code": 2,
                    "success": False,
                }
            )

        backend = MyBackend()
        if user := backend.create_user(email):
            client_setting = ClientSetting.objects.create(
                user_client=user,
                client_id=client_id,
                release_id=release_id,
                signboard_id=signboard_id if signboard_id else -1,
            )
            client_setting.save()

            return JsonResponse(
                {"email": user.email, "token": user.token, "success": True}
            )

        return JsonResponse({"success": False, "code": 3})


@method_decorator(csrf_exempt, name="dispatch")
class AuthWithTokenView(View):
    def post(self, request):
        backend = MyBackend()
        if user := backend.authenticate_from_interattivo(
            request.POST.get("token")
        ):
            login(request, user)
            return redirect("builder:dashboard")

        return redirect("builder:error_page")


class ErrorPageView(View):
    def get(self, request):
        return render(request, "builder/new/error.html")


class PermissionsApiView(LoginRequiredMixin, PermissionsUtils, View):
    def get(self, request):
        # add apply permissions builder/static/builder/new/permission_manager.js

        try:
            permissions = self.get_permissions(request.user)
            if (
                len(permissions["pacchetto"]) > 0
                and len(permissions["caratteristiche"]) > 0
            ):
                return JsonResponse(
                    {
                        "success": True,
                        "perms": {
                            "interactive_index": self.search_perm_by_id(
                                14, False
                            ),
                            "is_free_user": permissions["pacchetto"]["id"]
                            == 1,
                            "is_essential_user": permissions["pacchetto"]["id"]
                            == 2,
                            "is_standard_user": permissions["pacchetto"]["id"]
                            == 3,
                            "is_premium_user": permissions["pacchetto"]["id"]
                            == 4,
                            "is_enterprice_user": permissions["pacchetto"][
                                "id"
                            ]
                            == 5,
                            # region project settings permissions
                            # Numero interattività per prodotto
                            "number_interactivity_product": self.search_perm_by_id(
                                12, 1
                            ),
                            # Pianifica pubblicazione
                            "publication_date": self.search_perm_by_id(
                                15, False
                            ),
                            # Creazione lista della spesa
                            "grocery_list_create": self.search_perm_by_id(
                                16, False
                            ),
                            # Video all'avvio
                            "video_in_page": self.search_perm_by_id(19, False),
                            # Ricerca prodotto
                            "search_product": self.search_perm_by_id(
                                23, False
                            ),
                            # Condivisione singolo prodotto
                            "single_product_share": self.search_perm_by_id(
                                24, False
                            ),
                            # Prodotti correlati
                            "product_select": self.search_perm_by_id(
                                26, False
                            ),
                            # Visualizzazione pagina "Prodotti"
                            "product_page": self.search_perm_by_id(27, False),
                            # Integrazione in sito web
                            "website_integration": self.search_perm_by_id(
                                33, False
                            ),
                            # Immagine Condivisione personalizzata
                            "custom_opengraph_image_meta": self.search_perm_by_id(
                                35, False
                            ),
                            # Dominio personalizzato
                            "custom_domain": self.search_perm_by_id(36, False),
                            # Attivazione click&Collect
                            "grocery_list_to_market_integration": self.search_perm_by_id(
                                37, False
                            ),
                            # Archivio prodotti
                            "product_archive": self.search_perm_by_id(
                                43, False
                            ),
                            # Cronologia dei dati di analytics
                            "analytics": self.search_perm_by_id(60, False),
                            # Evidenzia Prodotti aggiunti alla lista
                            "highlight_product_added_to_grocery_list": self.search_perm_by_id(
                                123, False
                            ),
                            # Varianti e Tag
                            "variants_and_tags": self.search_perm_by_id(
                                124, False
                            ),
                            # endregion
                        },
                    }
                )

            return JsonResponse({"success": False})
        except Exception:
            return JsonResponse({"success": False})
