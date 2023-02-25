import os
from pathlib import Path

from inpublish.settings import Base


class Docker(Base):
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

    BASE_DIR = Path(__file__).resolve().parent.parent

    INPUBLISH_URL = os.getenv("INPUBLISH_URL", "")
    WORKER_URL = os.getenv("WORKER_URL", "")
    ABSOLUTE_URL = os.getenv("ABSOLUTE_URL", "")

    PYTHON_PATH = os.getenv("PYTHONPATH")
    DEBUG = os.getenv("DEBUG") == "True"
    MEDIA_URL = f'{os.getenv("ABSOLUTE_URL", "")}/media/'

    AWS_ACCESS_KEY_ID = "AKIA5HHRFLCRGM7QFJXD"
    AWS_SECRET_ACCESS_KEY = "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"
    AWS_STORAGE_BUCKET_NAME = "interattivo-dev"

    PRE_SALT = os.getenv("PRE_SALT")
    POST_SALT = os.getenv("POST_SALT")
    THUMBOR_URL = os.getenv("THUMBOR_URL")
    PREVIEW_URL = os.getenv("PREVIEW_URL")

    SESSION_MINUTE_EXPIRATION = os.getenv("SESSION_MINUTE_EXPIRATION")
    LOGOUT_REDIRECT_URL = os.getenv("LOGOUT_REDIRECT_URL")
    INTERATTIVO_ANALYTICS = os.getenv("INTERATTIVO_ANALYTICS")

    DATA_UPLOAD_MAX_MEMORY_SIZE = 1073741824
    FILE_UPLOAD_MAX_MEMORY_SIZE = 1073741824
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000
