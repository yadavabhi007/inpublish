from django.core.management.base import BaseCommand
from builder.models.flyer import InteractiveFlyerProduct
import requests


class Command(BaseCommand):
    def handle(self, *args, **options):
        products = InteractiveFlyerProduct.objects.filter(
            principal_product_id__gt=0
        )

        for product in products:
            varieties = product.varieties_list()
            json_giodicart = requests.get(
                f"https://www.giodicart.it/sysapi/product/{product.product_uid}"
            )
            json_giodicart = json_giodicart.json()["data"]

            code = ""
            for prod in json_giodicart:
                temp_name_related = prod["name"].split(" ")
                length = len(temp_name_related) - 1
                if temp_name_related[length] == varieties[0]:
                    code = prod["skul"]
            product.product_uid = code
            product.save()
