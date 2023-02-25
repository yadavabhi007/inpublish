from django.core.management.base import BaseCommand
from django.db.models import signals

from builder.models import (
    InteractiveFlyerPage,
    InteractiveFlyerProduct,
    ProductMarker,
    ProductBlueprint,
    ProductImage,
)

from builder.serializers import InteractiveFlyerPageSerializer
from builder.signals import generate_json_page


class Command(BaseCommand):
    help = "Forza la rigenerazione del json delle pagine e lo salva nel db"

    def add_arguments(self, parser):
        parser.add_argument("flyer", nargs="+", type=str)

    def handle(self, *args, **options):
        flyer_id = options["flyer"][0]

        signals.post_save.disconnect(
            generate_json_page, sender=InteractiveFlyerProduct
        )
        signals.post_delete.disconnect(
            generate_json_page, sender=InteractiveFlyerProduct
        )
        signals.post_save.disconnect(generate_json_page, sender=ProductMarker)
        signals.post_save.disconnect(
            generate_json_page, sender=ProductBlueprint
        )
        signals.post_save.disconnect(generate_json_page, sender=ProductImage)
        signals.post_save.disconnect(
            generate_json_page, sender=InteractiveFlyerPage
        )

        for page in InteractiveFlyerPage.objects.filter(interactive_flyer_id = flyer_id):
            page.json_page = InteractiveFlyerPageSerializer(page).data
            page.save()

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
        signals.post_save.connect(generate_json_page, sender=ProductBlueprint)
        signals.post_save.connect(generate_json_page, sender=ProductImage)
