from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

from interattivo_worker.service import (
    interactive_flyer_worker_page_image_file_directory_path,
)


class InteractiveFlyerWorker(models.Model):
    flyer_id = models.IntegerField()
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        verbose_name="InteractiveFlyer name",
    )
    assets_token = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    height = models.PositiveIntegerField(default=1)
    width = models.PositiveIntegerField(default=1)
    pdf_url = models.URLField(blank=False, null=False)
    error = models.BooleanField(default=False)
    error_message = models.TextField(default="", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Volantino interattivo Worker"
        verbose_name_plural = "Volantini interattivi Worker"


class InteractiveFlyerPageWorker(models.Model):
    interactive_flyer = models.ForeignKey(
        InteractiveFlyerWorker, on_delete=models.CASCADE, related_name="pages"
    )
    number = models.IntegerField()
    image_file = models.ImageField(
        upload_to=interactive_flyer_worker_page_image_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )
    thumb_image_file = models.ImageField(
        upload_to=interactive_flyer_worker_page_image_file_directory_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )

    def __str__(self):
        return f"page {self.number} - flyer: {self.interactive_flyer.name} {self.interactive_flyer.assets_token}"

    class Meta:
        ordering = ["number"]
        verbose_name = "Pagina interattive Worker"
        verbose_name_plural = "Pagine interattive Worker"
