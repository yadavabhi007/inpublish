import requests
from io import BytesIO

from django.conf import settings
from django.core import files


class ThumborServer:
    THUMBOR_URL = f"{settings.THUMBOR_URL}unsafe/"

    @staticmethod
    def transform_page_image(source_image_url, height="1200"):
        url = f"{ThumborServer.THUMBOR_URL}fit-in/{height}x/{source_image_url}"
        resp = requests.get(url)
        if resp.status_code == requests.codes.ok:
            fp = BytesIO()
            fp.write(resp.content)
            return files.File(fp)
        else:
            resp_2 = requests.get(url)
            fp_2 = BytesIO()
            fp_2.write(resp_2.content)
            return files.File(fp_2)

    @staticmethod
    def optimize_image(picture_url, width="350", height="350"):
        thumbor_url = f"{ThumborServer.THUMBOR_URL}fit-in/{width}x{height}/filters:upscale():fill(white)/"
        resp = requests.get(thumbor_url + picture_url)
        if resp.status_code == requests.codes.ok:
            fp = BytesIO()
            fp.write(resp.content)
            file_name = picture_url.split("/")[-1]
            return file_name, files.File(fp)

        return None, None
