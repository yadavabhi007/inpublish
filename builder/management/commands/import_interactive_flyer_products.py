from io import BytesIO

import requests
from django.conf import settings
from django.core import files
from django.core.management.base import BaseCommand

from builder.models import (
    InteractiveFlyer,
    InteractiveFlyerProduct,
    ProductMarker,
    ProductImage,
)

THUMBOR_URL = f"{settings.THUMBOR_URL}unsafe/fit-in/350x350/filters:upscale():fill(white)/"


class Command(BaseCommand):
    help = "Import interactive flyer products from related projects"

    def add_arguments(self, parser):
        parser.add_argument("arguments", nargs="+", type=str)

    def handle(self, *args, **options):
        interactive_flyer_id = options["arguments"][0]

        interactive_flyer = InteractiveFlyer.objects.get(
            pk=interactive_flyer_id
        )
        interactive_flyer.products.all().delete()

        for item in interactive_flyer.project_items():
            item_id = item.pk
            product_uid = item.product.product_id
            field1 = item.field1
            field2 = item.field2
            field3 = item.field3
            field4 = item.field4
            grammage = item.grammageValue
            price_with_iva = item.price_with_IVA
            price_for_kg = item.price_for_Kg
            available_pieces = item.available_pieces
            max_purchasable_pieces = item.max_purchasable_pieces
            punti = item.punti
            fidelity_product = item.fidelity_product
            focus = item.focus
            pam = item.pam
            three_for_two = item.three_for_two
            one_and_one_gratis = item.one_and_one_gratis
            underpriced_product = item.underpriced_product
            try:
                category = item.product.category.name
            except:
                category = ""
            try:
                subcategory = item.product.subcategory.name
            except:
                subcategory = ""
            equivalence = 1
            quantity_step = 1
            price_label = "€ " + f"{price_with_iva:.2f}".replace(".", ",")
            grocery_label = "pz"
            product = InteractiveFlyerProduct.objects.create(
                interactive_flyer=interactive_flyer,
                item_id=item_id,
                product_uid=product_uid,
                field1=field1,
                field2=field2,
                field3=field3,
                field4=field4,
                grammage=grammage,
                price_with_iva=price_with_iva,
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
                subcategory=subcategory,
                equivalence=equivalence,
                quantity_step=quantity_step,
                price_label=price_label,
                grocery_label=grocery_label,
            )

            ProductMarker.objects.create(
                interactive_flyer_product=product, type="plus", data=""
            )

            for picture in item.picture_item.all():
                pitcure_url = (
                    settings.CATALOG_IMAGES_URL + picture.low_resolution_path()
                )
                resp = requests.get(THUMBOR_URL + pitcure_url)
                if resp.status_code == requests.codes.ok:
                    fp = BytesIO()
                    fp.write(resp.content)
                    file_name = pitcure_url.split("/")[-1]
                    product_image = ProductImage.objects.create(
                        interactive_flyer_product=product, cropped=False
                    )
                    product_image.image_file.save(file_name, files.File(fp))

            interactive_flyer.products_imported += 1
            interactive_flyer.save()

        interactive_flyer.products_import_in_progress = False
        interactive_flyer.save()
