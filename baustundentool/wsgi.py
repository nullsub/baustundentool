"""
WSGI config for baustundentool project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/var/www/baustunden/baustundentool')
sys.path.append('/var/www/baustunden/baustunden')
sys.path.append('/var/www/baustunden')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baustundentool.settings")
application = get_wsgi_application()
