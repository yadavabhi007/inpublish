import os

from inpublish.settings import Base


class Local(Base):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DATABASE"),
            "USER": os.getenv("MYSQL_USER"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD"),
            "HOST": os.getenv("MYSQL_HOST"),
            "PORT": "3306",
        },
        "aeb_db": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("AEB_MYSQL_DATABASE"),
            "USER": os.getenv("AEB_MYSQL_USER"),
            "PASSWORD": os.getenv("AEB_MYSQL_PASSWORD"),
            "HOST": os.getenv("AEB_MYSQL_HOST"),
            "PORT": "3306",
        },
    }

    # "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])
    SECRET_KEY = os.getenv("SECRET_KEY")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PYTHON_PATH = os.path.join(BASE_DIR, "../app_env/bin/python")

    DEBUG = True

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = "interattivo"
    # AWS_S3_ENDPOINT_URL = "https://r1-it.storage.cloud.it"
