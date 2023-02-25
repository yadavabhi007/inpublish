from io import BytesIO

import requests
from django.conf import settings
from django.core import files
from django.core.management.base import BaseCommand

from builder.models.flyer import ProductImage
from utils.custom_logger import log_debug


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("flyer", nargs="+", type=str)

    def handle(self, *args, **options):
        flyer_id = options["flyer"][0]
        products_images = ProductImage.objects.filter(
            interactive_flyer_product__interactive_flyer=flyer_id
        )
        for image in products_images:
            if image.interactive_flyer_product.product_uid is not None:
                json_giodicart = requests.get(
                    f"https://www.giodicart.it/sysapi/product/{image.interactive_flyer_product.product_uid}"
                )
                try:
                    json_giodicart = json_giodicart.json()
                except Exception as e:
                    log_debug(
                        "Command",
                        f"https://www.giodicart.it/sysapi/product/{image.interactive_flyer_product.product_uid} => {e}",
                    )
                    continue

                cropped = 0
                if image.interactive_flyer_product.principal_product is None:
                    cropped = 1
                product_id = image.interactive_flyer_product.pk
                image.delete()
                new_image = ProductImage.objects.create(
                    cropped=cropped, interactive_flyer_product_id=product_id
                )
                try:
                    thumbor_url = f"{settings.THUMBOR_URL}unsafe/fit-in/350x350/filters:upscale():fill(white)/"
                    resp = requests.get(
                        thumbor_url + json_giodicart["data"][0]["photo"]
                    )
                    if resp.status_code == requests.codes.ok:
                        fp = BytesIO()
                        fp.write(resp.content)
                        fp.seek(0)
                        file_name = json_giodicart["data"][0]["photo"].split(
                            "/"
                        )[-1]

                        new_image.image_file.save(file_name, files.File(fp))
                except:
                    pass
