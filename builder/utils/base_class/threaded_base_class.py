from builder.utils.decorators import threaded
from django.core.management import call_command


class ThreadedBaseClass:
    @threaded
    def call_command_threaded(self, *args):
        call_command(*args)
