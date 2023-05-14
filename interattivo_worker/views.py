import json
from multiprocessing.pool import CLOSE
import tempfile
import gc

import requests
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pdf2image import convert_from_bytes
from six import BytesIO

from builder.utils.decorators import threaded
from interattivo_worker.models import InteractiveFlyerWorker
from interattivo_worker.serializers import InteractiveFlyerWorkerSerializer
from utils.custom_logger import log_debug
from utils.thumbor_server import ThumborServer
from utils.custom_logger import log_critical

@method_decorator(csrf_exempt, name="dispatch")
class PagesFromPdfWorkerView(View):
    NUM_THREAD = -1
    CLOSED_THREAD = 0

    @threaded
    def job(self):
        try:
            with tempfile.TemporaryDirectory() as path, tempfile.TemporaryFile() as pdf_file:
                r = requests.get(self.flyer_worker.pdf_url)
                pdf_file.write(r.content)
                pdf_file.seek(0)

                page_images = convert_from_bytes(
                    pdf_file.read(),
                    output_folder=path,
                    paths_only=True,
                    fmt='jpg'
                )
                log_critical('PAGES', page_images)
                self.page_images = page_images
                num_pages = len(page_images)
                start = 0
                end = num_pages
                val_pages = 20
                if num_pages % val_pages == 0:
                    self.NUM_THREAD = int(num_pages / val_pages)
                else:
                    self.NUM_THREAD = int(num_pages / val_pages + 1)
                while(start < num_pages):
                    if(num_pages - start < val_pages):
                        end = num_pages -1 
                    else:
                        end = start + val_pages -1
                    self.save_page(page_images[start:end+1], start)
                    start = start + val_pages
                
        except Exception as error:
            log_critical('ERROR', error)
            self.flyer_worker.error_message = f"Exception! -> {error}"
            self.flyer_worker.error = True
            self.flyer_worker.save()
    
    def save_page(self, images, start):
        log_critical('Creo immagini: ', len(images))
        for ind, page_image in enumerate(images, start = start + 1):
            self.create_thumbor_pages(ind, page_image)
        self.CLOSED_THREAD = self.CLOSED_THREAD + 1
        if self.CLOSED_THREAD == self.NUM_THREAD:
            self.check_executed_thred()
  
    def create_thumbor_pages(self, ind, page_image):
        page_file_name = f"page_{ind}.jpg"
        interactive_flyer_page = self.flyer_worker.pages.create(
                number=ind
            )
        with open(page_image, 'rb') as page_image_bytes:
            page_image_bytes.seek(0)
            interactive_flyer_page.image_file.save(page_file_name, content=File(page_image_bytes))
            picture_url = interactive_flyer_page.image_file.url
            full_page = ThumborServer.transform_page_image(picture_url)
            log_critical('Page',picture_url)
            interactive_flyer_page.image_file.save(
                page_file_name,
                full_page,
            )
            thumb_page = ThumborServer.transform_page_image(
                picture_url, "200"
            )
            thumb_file_name = f"thumb_{page_file_name}"
            interactive_flyer_page.thumb_image_file.save(thumb_file_name, thumb_page)        

    def check_executed_thred(self):
        # invio le informazioni a inpublish
        callback_url = reverse(
            "builder:interactive_flyer_receive_pages",
            kwargs={"interactive_flyer_id": self.flyer_worker.flyer_id},
        )
        r = requests.get(self.flyer_worker.pages.first().image_file.url)
        with tempfile.NamedTemporaryFile(mode="wb") as jpg:
            jpg.write(r.content)
            img = Image.open(str(jpg.name))
            log_critical('height',img.height)
            log_critical('width',img.width)
            self.flyer_worker.height = img.height
            self.flyer_worker.width = img.width
        self.flyer_worker.save()
        log_critical('FLYER',self.flyer_worker)
        serializer = InteractiveFlyerWorkerSerializer(self.flyer_worker)
        log_debug(
            "PagesFromPdfWorkerView",
            f"{settings.INPUBLISH_URL}{callback_url} - {json.dumps(serializer.data)}",
        )
        requests.post(
            f"{settings.INPUBLISH_URL}{callback_url}", json=serializer.data
        )

    def post(self, request):
        flyer_id = request.POST.get("flyer_id", None)
        name = request.POST.get("name", None)
        assets_token = request.POST.get("assets_token", None)
        pdf_url = request.POST.get("pdf_url", None)

        if not (flyer_id and name and assets_token and pdf_url):
            return JsonResponse({"success": False})

        self.flyer_worker = InteractiveFlyerWorker.objects.create(
            flyer_id=flyer_id,
            name=name,
            assets_token=assets_token,
            pdf_url=pdf_url,
        )

        self.job()

        return JsonResponse({"success": True})
