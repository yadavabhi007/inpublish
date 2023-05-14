import os
import tempfile
import urllib.request
from os.path import basename
from urllib.parse import urlparse

from django.core.files import File
from django.views import View

from builder.models import (
    ClientSetting,
    PolotnoToken,
    InteractiveFlyerIndex,
    InteractiveFlyer,
)
from builder.utils.base_class.worker_pdf_pages import WorkerPdfPages
from utils.thumbor_server import ThumborServer


class PolotnoBaseClass(WorkerPdfPages, View):
    def check_user_and_token(self, rqst):
        try:
            custom_user = ClientSetting.objects.get(
                client_id=rqst.get("client_id", 0)
            ).user_client
        except ClientSetting.DoesNotExist:
            return False, False

        if custom_user.auth_token and custom_user.auth_token.key == rqst.get(
            "token", ""
        ):
            return custom_user, PolotnoToken.objects.get(user=custom_user)

        return False, False

    def execute_action_by_type(self, token, img_temp, filename):
        if token.type in ("index", "4"):
            index, _ = InteractiveFlyerIndex.objects.get_or_create(
                interactive_flyer=token.interactive_flyer
            )
            flyer = token.interactive_flyer
            index.image_file.save(filename, File(img_temp))
            index.image_file.save(
                name=os.path.basename(index.image_file.name),
                content=ThumborServer.optimize_image(
                    index.image_file.url,
                    flyer.image_page_width,
                    flyer.image_page_height,
                )[1],
            )
            index.thumb_image_file.save(
                f"thumb_{index.image_file.name}",
                ThumborServer.transform_page_image(
                    index.image_file.url, "200"
                ),
            )

        elif token.type == "ogImageMeta":
            token.interactive_flyer.settings.ogImageMeta.save(
                filename, File(img_temp)
            )

        elif token.type == "ogImageMeta_mobile":
            token.interactive_flyer.settings.ogImageMeta_mobile.save(
                filename, File(img_temp)
            )

        elif token.type == "clientIcon":
            token.interactive_flyer.settings.clientIcon.save(
                filename, File(img_temp)
            )

        elif token.type == "category_banner_mobile":
            token.interactive_flyer.settings.category_banner_mobile.save(
                filename, File(img_temp)
            )

        elif token.type == "category_banner":
            token.interactive_flyer.settings.category_banner.save(
                filename, File(img_temp)
            )

        elif token.type == "product_banner":
            token.interactive_flyer.settings.product_banner.save(
                filename, File(img_temp)
            )
        elif token.type == "logo_full":
            token.interactive_flyer.settings.logo_full.save(
                filename, File(img_temp)
            )

        elif token.type in (
            "Volantino A4",
            "Volantino quadrato",
            "13",
            "14",
            "5",
            "6",
        ):
            token.interactive_flyer.flyer_pdf_file.save(
                filename, File(img_temp)
            )
            token.interactive_flyer.initialization_in_progress = True
            token.interactive_flyer.status = InteractiveFlyer.DRAFT
            token.interactive_flyer.save()

            self.call_pages_from_pdf_worker(token.interactive_flyer)

        elif token.type == "clientIconC":
            token.user.settings.clientIcon.save(filename, File(img_temp))

        elif token.type == "brandImageC":
            token.user.settings.brandImage.save(filename, File(img_temp))

        else:
            index, _ = InteractiveFlyerIndex.objects.get_or_create(
                interactive_flyer=token.interactive_flyer
            )
            index.image_file.save(filename, File(img_temp))
            index.image_file.save(
                name=os.path.basename(index.image_file.name),
                content=ThumborServer.transform_page_image(
                    index.image_file.url
                ),
            )
            index.thumb_image_file.save(
                f"thumb_{index.image_file.name}",
                ThumborServer.transform_page_image(
                    index.image_file.url, "200"
                ),
            )
        # todo aggiungi altri tipi

    def download_image_by_url(self, image_url):
        img_temp = tempfile.NamedTemporaryFile(delete=True)
        req = urllib.request.Request(
            image_url,
            data=None,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req) as response:
            img_temp.write(response.read())
        img_temp.flush()
        filename = basename(urlparse(image_url).path)

        return img_temp, filename
