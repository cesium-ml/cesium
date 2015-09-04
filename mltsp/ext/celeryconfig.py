#CELERY_RESULT_BACKEND = 'mltsp.ext.rethinkdb_backend:RethinkBackend'

CELERY_RESULT_BACKEND = "amqp"

CELERY_RETHINKDB_BACKEND_SETTINGS = {
    'host': '127.0.0.1',
    'port': 28015,
    'db': 'celery_test',
    # 'auth_key': '',
    'timeout': 20,
    'table': 'celery_taskmeta',
    'options': {}
}

CELERY_RESULT_SERIALIZER = 'json'  # NOTE: MUST BE SET TO JSON

#CELERYD_LOG_FILE = "/tmp/celery.log"

CELERYD_LOG_LEVEL = "DEBUG"

INSTALLED_APPS = ["mltsp"]

CELERY_IMPORTS = ("mltsp", "celery_tasks")
