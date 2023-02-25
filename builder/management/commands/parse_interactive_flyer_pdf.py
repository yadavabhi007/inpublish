import requests
from io import BytesIO
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand
from pdf2image import convert_from_bytes
from django.core.files.base import ContentFile
from django.core import files

from builder.models import InteractiveFlyer

THUMBOR_URL = f"{settings.THUMBOR_URL}unsafe/fit-in/1200x/"


class Command(BaseCommand):
    help = "Generate interactive flyer jpeg pages from flyer PDF"

    def add_arguments(self, parser):
        parser.add_argument("arguments", nargs="+", type=str)

    def handle(self, *args, **options):
        interactive_flyer_id = options["arguments"][0]
        interactive_flyer = InteractiveFlyer.objects.get(
            pk=interactive_flyer_id
        )

        try:
            with tempfile.TemporaryDirectory() as path:
                # page_images = convert_from_path(
                #     interactive_flyer.flyer_pdf_file.path, output_folder=path, paths_only=False)
                page_images = convert_from_bytes(
                    interactive_flyer.flyer_pdf_file.read(),
                    output_folder=path,
                    paths_only=False,
                )
                for ind, page_image in enumerate(page_images, start=1):
                    page_image_io = BytesIO()
                    page_image.save(page_image_io, format="JPEG")
                    interactive_flyer_page = interactive_flyer.pages.create(
                        number=ind
                    )
                    interactive_flyer_page.image_file.save(
                        f"page_{ind}.jpg",
                        content=ContentFile(page_image_io.getvalue()),
                    )

                    pitcure_url = interactive_flyer_page.image_file.url
                    resp = requests.get(THUMBOR_URL + pitcure_url)
                    if resp.status_code == requests.codes.ok:
                        fp = BytesIO()
                        fp.write(resp.content)
                        file_name = pitcure_url.split("/")[-1]
                        interactive_flyer_page.image_file.save(
                            file_name, files.File(fp)
                        )
                        interactive_flyer_page.image_file_local.save(
                            file_name,
                            content=ContentFile(
                                interactive_flyer_page.image_file.read()
                            ),
                        )

            interactive_flyer.initialization_in_progress = False
            interactive_flyer.save()
        except Exception as error:
            interactive_flyer.initialization_error_message = str(error)
            interactive_flyer.initialization_error = True
            interactive_flyer.initialization_in_progress = False
            interactive_flyer.save()
