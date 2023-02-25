from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from builder.models import InteractiveFlyer


class Command(BaseCommand):
    help = "Cancella i volantini zombie creati con polotno ma non salvati"

    def handle(self, *args, **options):
        two_hours_before = timezone.now() - timedelta(hours=2)
        flyers = InteractiveFlyer.objects.filter(
            status=InteractiveFlyer.WAIT_POLOTNO_PDF,
            created_at__lt=two_hours_before,
        )

        for flyer in flyers:
            flyer.delete()
