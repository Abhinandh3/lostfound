"""
WSGI config for lostfound_project project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lostfound_project.settings')

application = get_wsgi_application()
