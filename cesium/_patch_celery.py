"""Patch Celery to use `cloudpickle` instead of `pickle`.

The built-in `pickle` module cannot handle lambda functions or other functions
not imported from modules; this is a major limitation when passing custom
featurization functions to Celery workers. `cloudpickle` handles these cases
correctly, so here we monkey patch the relevant Celery modules/dependencies to
use `cloudpickle` when {,un}serializing.
"""
import cloudpickle
import kombu.serialization

try:
    from io import BytesIO
except:
    try:
        from cStringIO import StringIO as BytesIO
    except ImportError:
        from StringIO import StringIO as BytesIO


def pickle_loads(s, load=cloudpickle.load):
# used to support buffer objects
    return load(BytesIO(s))


def pickle_dumps(obj, dumper=cloudpickle.dumps):
    return dumper(obj, protocol=kombu.serialization.pickle_protocol)


registry = kombu.serialization.registry
kombu.serialization.pickle = cloudpickle

registry.unregister('pickle')

registry.register('pickle', pickle_dumps, pickle_loads,
                  content_type='application/x-python-serialize',
                  content_encoding='binary')

import celery.worker
import celery.concurrency.asynpool
celery.worker.state.pickle = cloudpickle
celery.concurrency.asynpool._pickle = cloudpickle

import billiard
billiard.common.pickle = cloudpickle
billiard.common.pickle_loads = pickle_loads
billiard.common.pickle_dumps = pickle_dumps
