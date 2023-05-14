import os

from inpublish.settings import Base


class Local(Base):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "interattivo",
            "USER": "root",
            "PASSWORD": "35PR*SL6CZf",
            "HOST": "localhost",
            "PORT": "3306",
        },
        "aeb_db": {
            "ENGINE": "django.db.backends.mysql",
            #'NAME': 'aiflyer',
            "NAME": "aebflyerdb",
            "USER": "djangoext",
            #'USER': 'cloud.aeb',
            "PASSWORD": "HQ%0@C@Gq0",
            #'PASSWORD': 'El4tYbCGt0KVkUJA',
            "HOST": "10.194.10.8",  # new-production
            #'HOST': '10.194.10.3', #production
            # 'HOST': '10.194.10.5', #test
            "PORT": "3306",
        },
    }

    # "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])
    SECRET_KEY = "p5yfm0+)h8h-i4glul33=5(vdm51c$jxag9+nswl0353b6*ezd"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PYTHON_PATH = os.path.join(BASE_DIR, "../app_env/bin/python")

    DEBUG = True

    # AWS_ACCESS_KEY_ID = "interattivo"
    AWS_ACCESS_KEY_ID = "AKIA5HHRFLCRGM7QFJXD"
    # AWS_SECRET_ACCESS_KEY = "RCgmb@726xvr"
    AWS_SECRET_ACCESS_KEY = "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"
    # AWS_STORAGE_BUCKET_NAME = "test"
    AWS_STORAGE_BUCKET_NAME = "interattivo"
    # AWS_S3_ENDPOINT_URL = "https://r1-it.storage.cloud.it"
