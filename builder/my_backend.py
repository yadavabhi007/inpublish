from django.utils.crypto import get_random_string

from utils.custom_logger import log_debug
from .models import CustomUser
from .utils.service import generate_token


class MyBackend:
    def create_user(self, email):
        try:
            return CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist as e:
            log_debug("create_user 1", e)

        try:
            usr = CustomUser.objects.create_user(
                username=email, email=email, password=generate_token()
            )

            client_code = get_random_string(length=10)
            while CustomUser.objects.filter(client_code=client_code).exists():
                usr.client_code = get_random_string(length=10)

            return usr
        except Exception as ex:
            log_debug("create_user 2", ex)
            return None

    def authenticate_from_interattivo(self, token):
        try:
            return CustomUser.objects.get(token=token)
        except CustomUser.DoesNotExist:
            return None

    def get_user_email(self, token):
        try:
            return CustomUser.objects.get(token=token).email
        except CustomUser.DoesNotExist:
            return None
