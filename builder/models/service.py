from django.db import models
from django_cleanup import cleanup
from storages.backends.s3boto3 import S3Boto3Storage

from builder.utils.service import aws_uploader_path


@cleanup.ignore
class AWSUploader(models.Model):
    assets_token = models.CharField(max_length=100, null=True, blank=True)
    image_file = models.ImageField(
        upload_to=aws_uploader_path,
        max_length=100,
        null=True,
        blank=True,
        storage=S3Boto3Storage(),
    )

    class Meta:
        verbose_name = "AWSUploader"
        verbose_name_plural = "AWSUploader"
