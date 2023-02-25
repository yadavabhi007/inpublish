import os
import zipfile
from io import BytesIO
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.conf import settings

from builder.models import InteractiveFlyer


class Command(BaseCommand):
    help = "Generate interactive flyer ZIP for react"

    def add_arguments(self, parser):
        parser.add_argument("arguments", nargs="+", type=str)

    def handle(self, *args, **options):
        interactive_flyer_id = options["arguments"][0]
        # absolute_uri = options['arguments'][1]

        interactive_flyer = InteractiveFlyer.objects.get(
            pk=interactive_flyer_id
        )
        interactive_flyer.save_json_file()

        s = BytesIO()
        folder_path = os.path.join(
            settings.MEDIA_ROOT, f"interactive_flyer_{interactive_flyer.id}"
        )
        parent_folder = os.path.dirname(folder_path)
        contents = os.walk(folder_path)
        zip_file = zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(parent_folder, "media/")
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(parent_folder, "media/")
                zip_file.write(absolute_path, relative_path)
        zip_file.close()

        interactive_flyer.flyer_zip_file.save(
            f"{interactive_flyer.name}.zip", content=ContentFile(s.getvalue())
        )
        interactive_flyer.zip_generation_in_progress = False
        interactive_flyer.zip_last_generation = timezone.now()
        interactive_flyer.save()
