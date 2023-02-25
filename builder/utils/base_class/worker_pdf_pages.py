import requests
from django.conf import settings
from django.urls import reverse


class WorkerPdfPages:
    def call_pages_from_pdf_worker(self, interactive_flyer):
        pdf_worker_url = reverse("interattivo_worker:pages_from_pdf_worker")
        respns = requests.post(
            f"{settings.WORKER_URL}{pdf_worker_url}",
            data={
                "flyer_id": interactive_flyer.id,
                "name": interactive_flyer.name,
                "assets_token": interactive_flyer.assets_token,
                "pdf_url": interactive_flyer.flyer_pdf_file.url,
            },
        )
        if not respns.json()["success"]:
            interactive_flyer.initialization_in_progress = False
            interactive_flyer.initialization_error = True
            interactive_flyer.save()
