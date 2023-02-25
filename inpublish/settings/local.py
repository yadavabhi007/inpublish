import os

from inpublish.settings import Base


class Local(Base):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "interattivo",
            "USER": "root",
            "PASSWORD": "5PSL6CZf",
            "HOST": "localhost",
            "PORT": "3306",
        },
        "aeb_db": {
            "ENGINE": "django.db.backends.mysql",
            #'NAME': 'aebflyerdb',
            "NAME": "aebflyerdb",
            "USER": "root",
            #'USER': 'localhost',
            "PASSWORD": "HQfdrf34",
            #'PASSWORD': '4tYbCGt0KVkA',
            "HOST": "localhost",  # new-production
            #'HOST': 'localhost', #production
            # 'HOST': 'localhost', #test
            "PORT": "3306",
        },
    }

    # "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])
    SECRET_KEY = "p5yfm0+)h8h-i4glul33=5(vdm51c$jxag9+nswl0353b6*ezd"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PYTHON_PATH = os.path.join(BASE_DIR, "../env/bin/python")

    DEBUG = True

    # AWS_ACCESS_KEY_ID = "interattivo"
    AWS_ACCESS_KEY_ID = "IA5HHRFLCRGM7QFJFGTE"
    # AWS_SECRET_ACCESS_KEY = "RCgmb@726xvr"
    AWS_SECRET_ACCESS_KEY = "NN9sE0cfAMfusSkpXSYiJeHkyiqDhMTR41+IsC8T"
    # AWS_STORAGE_BUCKET_NAME = "test"
    AWS_STORAGE_BUCKET_NAME = "interattivo"
    # AWS_S3_ENDPOINT_URL = "https://r1-it.storage.cloud.it"
