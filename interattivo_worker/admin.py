from django.contrib import admin

from interattivo_worker.models import (
    InteractiveFlyerWorker,
    InteractiveFlyerPageWorker,
)
from interattivo_worker.serializers import InteractiveFlyerWorkerSerializer


class InteractiveFlyerPageWorkerInline(admin.TabularInline):
    model = InteractiveFlyerPageWorker
    extra = 0


@admin.register(InteractiveFlyerWorker)
class InteractiveFlyerWorkerAdmin(admin.ModelAdmin):
    readonly_fields = ("json_volantino",)
    model = InteractiveFlyerWorker
    inlines = (InteractiveFlyerPageWorkerInline,)

    def json_volantino(self, obj):
        serializer = InteractiveFlyerWorkerSerializer(obj)
        return serializer.data
