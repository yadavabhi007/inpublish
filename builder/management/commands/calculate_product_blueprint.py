from django.core.management.base import BaseCommand
from django.db.models import signals

from builder.models import (
    InteractiveFlyerPage,
    InteractiveFlyerProduct,
    ProductMarker,
    ProductBlueprint,
    ProductImage,
)
from builder.models.flyer import InteractiveFlyer

from builder.serializers import InteractiveFlyerPageSerializer
from builder.signals import generate_json_page
from utils.custom_logger import log_critical, log_debug


class Command(BaseCommand):
    help = "Forza la rigenerazione del json delle pagine e lo salva nel db"

    def add_arguments(self, parser):
        parser.add_argument("flyer", nargs="+", type=str)

    def handle(self, *args, **options):
        flyer_id = options["flyer"][0]
        
        flyer = InteractiveFlyer.objects.get(pk = flyer_id)
        page_height= flyer.image_page_height
        page_width = flyer.image_page_width
        products = InteractiveFlyerProduct.objects.filter( interactive_flyer_id = flyer_id )

        for product in products:
            try:
                blueprint = ProductBlueprint.objects.get( interactive_flyer_product_id = product.pk )
                blueprint.top = (float(blueprint.top)/ page_height )
                blueprint.left = (float(blueprint.left) / page_width)
                blueprint.width = (float(blueprint.width)/ page_width)
                blueprint.height = (float(blueprint.height) / page_height)
                blueprint.save()
                log_debug('DEBUG','PRODOTTO '+ str(product.pk) +': BLUEPRINT CAMBIATO!')
            except Exception as e:
                log_critical('ERRORE', e)
            
        log_debug('FINITO','COMMAND TERMINATO')
       

       
