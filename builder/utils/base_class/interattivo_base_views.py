from aeb.connectors.connector import Connector
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from django.utils.translation import gettext as _

from builder.models import InteractiveFlyer
from builder.utils.base_class.threaded_base_class import ThreadedBaseClass


class InterattivoViews(LoginRequiredMixin, ThreadedBaseClass, View):
    page_name = ""

    def dispatch(self, request, *args, **kwargs):
        if "interactive_flyer_id" in kwargs:
            self.flyer = InteractiveFlyer.objects.get(
                pk=kwargs["interactive_flyer_id"]
            )
            if self.flyer.user != request.user:
                messages.error(request, _("Pagina inesistente"))
                return redirect(reverse("builder:dashboard"))

        self.context = self.interattivo_context_data()
        if isinstance(request.user, AnonymousUser):
            return redirect("builder:session_expired")
        self.connector = Connector(connector=request.user.connector_type)
        return super().dispatch(request, *args, **kwargs)

    def get_active_publications(self, user):
        return InteractiveFlyer.objects.filter(
            user=user, status=InteractiveFlyer.PUBLISHED
        ).count()

    def interattivo_context_data(self):
        context = {
            "page": {
                "name": self.page_name,
                "breadcrumbs": {
                    _("Dashboard"): reverse("builder:dashboard"),
                    f"{self.page_name}": "",
                },
            }
        }
        return context
