from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dd_scanner.settings')
app = Celery('dd_scanner', include=['dd_downloader.celery_tasks'])
app.config_from_object('django.conf:settings', namespace='CELERY')



# Using a string here means the worker will not have to
# pickle the object when using Windows.
#app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
	print('Request: {0!r}'.format(self.request))


from celery.schedules import crontab

app.conf.beat_schedule = {
    # Executes every day at  12:30 pm.
    'process-scan-queue-task': {
        'task': 'process-all-scanners',
        'schedule': crontab(minute='*'),
        'args': (),
    },
}