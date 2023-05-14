from rest_framework import serializers

from interattivo_worker.models import (
    InteractiveFlyerWorker,
    InteractiveFlyerPageWorker,
)


class InteractiveFlyerPageWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractiveFlyerPageWorker
        fields = ("number", "image_file", "thumb_image_file")


class InteractiveFlyerWorkerSerializer(serializers.ModelSerializer):
    pages = InteractiveFlyerPageWorkerSerializer(many=True, required=False)

    class Meta:
        model = InteractiveFlyerWorker
        exclude = ("id",)
