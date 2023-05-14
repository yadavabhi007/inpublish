import datetime
import hashlib

from django.conf import settings


class CounterCheck:
    def calculate_counter_check(self):
        pre_salt = settings.PRE_SALT
        post_salt = settings.POST_SALT
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return hashlib.md5(
            f"{pre_salt}{today}{post_salt}".encode()
        ).hexdigest()
