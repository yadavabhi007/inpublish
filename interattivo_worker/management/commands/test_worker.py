import requests
from django.core.management import BaseCommand
from django.urls import reverse

from builder.models import InteractiveFlyer


class Command(BaseCommand):
    help = "Test worker pdf page"

    def add_arguments(self, parser):
        parser.add_argument("arguments", nargs="+", type=int)

    def handle(self, *args, **options):
        flyer = InteractiveFlyer.objects.get(id=options["arguments"][0])
        requests.post(
            "http://localhost"
            + reverse("interattivo_worker:pages_from_pdf_worker"),
            {
                "flyer_id": flyer.id,
                "name": flyer.name,
                "assets_token": flyer.assets_token,
                "pdf_url": flyer.flyer_pdf_file.url,
            },
        )
