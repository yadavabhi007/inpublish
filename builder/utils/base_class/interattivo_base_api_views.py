from aeb.connectors.connector import Connector
from django.views import View
from builder.models import InteractiveFlyer


class InterattivoApiView(View):
    def dispatch(self, request, *args, **kwargs):
        if "interactive_flyer_id" in kwargs:
            self.flyer = InteractiveFlyer.objects.get(
                pk=kwargs["interactive_flyer_id"]
            )
        return super().dispatch(request, *args, **kwargs)

    def get_connector(self, request):
        self.connector = Connector(connector=request.user.connector_type)

    def calculate_blueprint_percentage(
        self, flyer_page_width, flyer_page_height, coordinates: dict
    ):
        return {
            "top": (float(coordinates["top"]) * 100 / flyer_page_height),
            "left": (float(coordinates["left"]) * 100 / flyer_page_width),
            "width": (float(coordinates["width"]) * 100 / flyer_page_width),
            "height": (float(coordinates["height"]) * 100 / flyer_page_height),
        }
