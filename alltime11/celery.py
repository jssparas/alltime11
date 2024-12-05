import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings
from .celery_cron import beat_tasks

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alltime11.settings")

app = Celery("alltime11")

app.config_from_object(settings, namespace="CELERY")


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(settings.LOGGING)


app.autodiscover_tasks()
app.conf.beat_schedule = beat_tasks
