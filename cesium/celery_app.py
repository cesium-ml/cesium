from celery import Celery
from cesium import _patch_celery

celery_config = {
    'CELERY_ACCEPT_CONTENT': ['pickle'],
    'CELERY_IMPORTS': ['cesium', 'cesium._patch_celery', 'cesium.celery_tasks'],
    'CELERY_RESULT_BACKEND': 'amqp',
    'CELERY_RESULT_SERIALIZER': 'pickle',
    'CELERY_TASK_SERIALIZER': 'pickle',
    'INSTALLED_APPS': ['cesium'],
    'CELERY_BROKER': 'amqp://guest@localhost//'
}
app = Celery('cesium', broker=celery_config['CELERY_BROKER'])
app.config_from_object(celery_config)
