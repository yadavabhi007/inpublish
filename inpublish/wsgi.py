"""
WSGI config for inpublish project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
import sys

# necessario in produzione
# sys.path.append('/path_to_deploy/gestionale_interattivo')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inpublish.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Docker")

from configurations.wsgi import get_wsgi_application

application = get_wsgi_application()
