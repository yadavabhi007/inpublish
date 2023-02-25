import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile

from builder.models import (
    IndexLinkBlueprint,
    InteractiveFlyerIndex,
    ProductBlueprint,
    InteractiveFlyer,
)

THUMBOR_URL = f"{settings.THUMBOR_URL}unsafe/fit-in/1200x/"


class Command(BaseCommand):
    help = "Clone interactive flyer"

    def add_arguments(self, parser):
        parser.add_argument("arguments", nargs="+", type=str)

    def handle(self, *args, **options):
        source_flyer_id = options["arguments"][0]
        target_flyer_id = options["arguments"][1]

        source_flyer = InteractiveFlyer.objects.get(pk=source_flyer_id)
        target_flyer = InteractiveFlyer.objects.get(pk=target_flyer_id)

        if source_flyer.has_index():
            source_index = source_flyer.index
            target_index = InteractiveFlyerIndex.objects.create(
                interactive_flyer=target_flyer
            )
            target_index.image_file.save(
                os.path.basename(source_index.image_file.name),
                content=ContentFile(source_index.image_file.read()),
            )
            target_index.image_file_local.save(
                os.path.basename(source_index.image_file.name),
                content=ContentFile(target_index.image_file.read()),
            )

            for source_link in source_index.links.all():
                target_link = target_index.links.create(page=source_link.page)
                IndexLinkBlueprint.objects.create(
                    interactive_flyer_index_link=target_link,
                    top=source_link.blueprint.top,
                    left=source_link.blueprint.left,
                    width=source_link.blueprint.width,
                    height=source_link.blueprint.height,
                )

        for source_page in source_flyer.pages.all():
            target_page = target_flyer.pages.create(number=source_page.number)

            target_page.image_file.save(
                os.path.basename(source_page.image_file.name),
                content=ContentFile(source_page.image_file.read()),
            )
            target_page.image_file_local.save(
                os.path.basename(source_page.image_file.name),
                content=ContentFile(source_page.image_file.read()),
            )
            target_page.thumb_image_file.save(
                os.path.basename(source_page.thumb_image_file.name),
                content=ContentFile(source_page.thumb_image_file.read()),
            )

            for source_product in source_page.products.all():
                target_product = target_page.products.create(
                    item_id=source_product.item_id,
                    product_uid=source_product.product_uid,
                    field1=source_product.field1,
                    field2=source_product.field2,
                    field3=source_product.field3,
                    field4=source_product.field4,
                    grammage=source_product.grammage,
                    price_with_iva=source_product.price_with_iva,
                    price_for_kg=source_product.price_for_kg,
                    available_pieces=source_product.available_pieces,
                    max_purchasable_pieces=source_product.max_purchasable_pieces,
                    punti=source_product.punti,
                    fidelity_product=source_product.fidelity_product,
                    focus=source_product.focus,
                    pam=source_product.pam,
                    three_for_two=source_product.three_for_two,
                    one_and_one_gratis=source_product.one_and_one_gratis,
                    underpriced_product=source_product.underpriced_product,
                    category=source_product.category,
                    subcategory=source_product.subcategory,
                    equivalence=source_product.equivalence,
                    quantity_step=source_product.quantity_step,
                    price_label=source_product.price_label,
                    grocery_label=source_product.grocery_label,
                )

                for source_product_image in source_product.images.all():
                    target_product_image = target_product.images.create(
                        cropped=source_product_image.cropped
                    )
                    target_product_image.image_file.save(
                        os.path.basename(source_product_image.image_file.name),
                        ContentFile(source_product_image.image_file.read()),
                    )

                ProductBlueprint.objects.create(
                    interactive_flyer_product=target_product,
                    top=source_product.blueprint.top,
                    left=source_product.blueprint.left,
                    width=source_product.blueprint.width,
                    height=source_product.blueprint.height,
                )

                for source_variety in source_product.varieties.all():
                    target_product.varieties.create(name=source_variety.name)

                for source_marker in source_product.markers.all():
                    target_marker = target_product.markers.create(
                        type=source_marker.type,
                        data=source_marker.data,
                        title=source_marker.title,
                        link=source_marker.link,
                        ingredients=source_marker.ingredients,
                        recipe=source_marker.recipe,
                        content_title=source_marker.content_title,
                        content_text=source_marker.content_text,
                        specifications=source_marker.specifications,
                        active=source_marker.active,
                    )
                    if source_marker.video_file:
                        target_marker.video_file.save(
                            os.path.basename(source_marker.video_file.name),
                            content=ContentFile(
                                source_marker.video_file.read()
                            ),
                        )
                    for source_marker_image in source_marker.images.all():
                        target_marker_image = target_marker.images.create()
                        target_marker_image.image_file.save(
                            os.path.basename(
                                source_marker_image.image_file.name
                            ),
                            content=ContentFile(
                                source_marker_image.image_file.read()
                            ),
                        )

        target_flyer.initialization_in_progress = False
        target_flyer.save()
