import tempfile

import requests
from django.db.models import signals
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from builder.models import (
    ProductMarker,
    ProductImage,
    ProductBlueprint,
    InteractiveFlyerPage,
)
from builder.models.flyer import InteractiveFlyerProduct
from builder.signals import generate_json_page

from utils.custom_logger import log_debug
from utils.thumbor_server import ThumborServer


class Command(BaseCommand):
    help = "Merge giodicart product"

    def add_arguments(self, parser):
        parser.add_argument("flyer", nargs="+", type=str)

    def handle(self, *args, **options):
        flyer_id = options["flyer"][0]
        window = options["flyer"][1]

        if window == "1":
            # cancello i prodotti senza skul solo al primo avvio
            signals.post_save.disconnect(
                generate_json_page, sender=InteractiveFlyerProduct
            )
            signals.post_delete.disconnect(
                generate_json_page, sender=InteractiveFlyerProduct
            )
            signals.post_save.disconnect(
                generate_json_page, sender=ProductMarker
            )
            signals.post_save.disconnect(
                generate_json_page, sender=ProductBlueprint
            )
            signals.post_save.disconnect(
                generate_json_page, sender=ProductImage
            )
            signals.post_save.disconnect(
                generate_json_page, sender=InteractiveFlyerPage
            )

            InteractiveFlyerProduct.objects.filter(
                interactive_flyer=flyer_id,
                product_uid="",
                type=InteractiveFlyerProduct.TYPE_PRODUCT,
            ).delete()

            signals.post_save.connect(
                generate_json_page, sender=InteractiveFlyerProduct
            )
            signals.post_delete.connect(
                generate_json_page, sender=InteractiveFlyerProduct
            )
            signals.post_save.connect(generate_json_page, sender=ProductMarker)
            signals.post_save.connect(
                generate_json_page, sender=InteractiveFlyerPage
            )
            signals.post_save.connect(
                generate_json_page, sender=ProductBlueprint
            )
            signals.post_save.connect(generate_json_page, sender=ProductImage)

        count = InteractiveFlyerProduct.objects.filter(
            interactive_flyer=flyer_id,
            type=InteractiveFlyerProduct.TYPE_PRODUCT,
        ).count()

        log_debug("merge_giodicart", f"page={window} / tot_page={count / 500}")

        limit = int(window) * 500
        offset = int(limit) - 500
        products = InteractiveFlyerProduct.objects.filter(
            interactive_flyer=flyer_id,
            type=InteractiveFlyerProduct.TYPE_PRODUCT,
        )[offset:limit]

        for product in products:
            json_giodicart = requests.get(
                f"https://www.giodicart.it/sysapi/product/{product.product_uid}"
            )
            json_giodicart = json_giodicart.json()["data"][1:]

            for prod in json_giodicart:
                rel_product = InteractiveFlyerProduct.objects.create(
                    principal_product=product,
                    descrizione_estesa=prod["info"],
                    interactive_flyer_page=product.interactive_flyer_page,
                    interactive_flyer=product.interactive_flyer_page.interactive_flyer,
                    sku=prod["sku"],
                    product_uid=prod["skul"],
                    codice_interno_insegna=product.codice_interno_insegna,
                    field1=product.field1,
                    field2=product.field2,
                    field3=product.field3,
                    field4=product.field4,
                    grammage=product.grammage,
                    price_with_iva=product.price_with_iva,
                    calcolo_prezzo=product.calcolo_prezzo,
                    offer_price=product.offer_price,
                    price_for_kg=product.price_for_kg,
                    available_pieces=product.available_pieces,
                    max_purchasable_pieces=product.max_purchasable_pieces,
                    punti=product.punti,
                    fidelity_product=product.fidelity_product,
                    focus=product.focus,
                    pam=product.pam,
                    three_for_two=product.three_for_two,
                    one_and_one_gratis=product.one_and_one_gratis,
                    underpriced_product=product.underpriced_product,
                    category=product.category,
                    category_name=product.category_name,
                    subcategory=product.subcategory,
                    subcategory_name=product.subcategory_name,
                    equivalence=product.equivalence,
                    quantity_step=product.quantity_step,
                    price_label=product.price_label,
                    grocery_label=product.grocery_label,
                    weight_unit_of_measure=None,
                    strike_price=prod["strike_price"],
                    discount_rate=int(prod["discount_rate"]),
                    prices=prod["prices"],
                    promo=prod["promo"],
                    stock=prod["stock"],
                    tdc=prod["tdc"],
                    available_from=prod["from"],
                    brand=prod["brand"],
                    brand_logo=prod["brand_logo"],
                    line=prod["line"],
                    line_logo=prod["line_logo"],
                )

                ProductMarker.objects.create(
                    interactive_flyer_product=rel_product, type="plus", data=""
                )
                if prod["photo"]:
                    with tempfile.TemporaryFile() as img_product_file:
                        r = requests.get(prod["photo"])
                        img_product_file.write(r.content)
                        img_product_file.seek(0)

                        an_image = ProductImage.objects.create(
                            interactive_flyer_product=rel_product,
                            cropped=True,
                        )
                        an_image.image_file.save(
                            f"{prod['skul']}{get_random_string(4)}.jpg",
                            img_product_file,
                        )

                        file_name, image_file = ThumborServer.optimize_image(
                            an_image.image_file.url
                        )
                        try:
                            if file_name and image_file.file:
                                an_image.image_file.save(file_name, image_file)
                        except Exception as e:
                            log_debug("ERROR", e)

                variety = prod["name"].replace(product.field1, "").strip()
                rel_product.varieties.create(name=variety)
