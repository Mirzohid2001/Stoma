import os
from celery import Celery
from django.conf import settings as django_settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = django_settings.TIME_ZONE
app.conf.enable_utc = True
app.autodiscover_tasks()
