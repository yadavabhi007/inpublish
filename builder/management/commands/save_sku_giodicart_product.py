from django.core.management.base import BaseCommand
from builder.models.flyer import InteractiveFlyerProduct
import requests

from utils.custom_logger import log_debug


class Command(BaseCommand):
    help = "Per tutti i prodotti di un volantino: richiama le api di giodicart e salva nel db gli sku"

    def add_arguments(self, parser):
        parser.add_argument("flyer", nargs="+", type=str)

    def handle(self, *args, **options):
        flyer_id = options["flyer"][0]
        products = InteractiveFlyerProduct.objects.filter(
            interactive_flyer=flyer_id, sku=None
        )

        error_products = []
        for product in products:
            try:
                json_giodicart = requests.get(
                    f"https://www.giodicart.it/sysapi/product/{product.product_uid}"
                )
                json_giodicart = json_giodicart.json()["data"]

                sku = json_giodicart[0]["sku"]
                product.sku = sku

                # info = json_giodicart[0]["info"]
                # product.descrizione_estesa = info
                product.save()
            except Exception as e:
                error_products.append(f"{product.id=} {product.product_uid=}")
                log_debug("save_sku", f"{product.product_uid} -> {e}")

        log_debug("prodotti rotti:", f"{error_products=}")
