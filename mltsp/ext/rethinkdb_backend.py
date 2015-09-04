# -*- coding: utf-8 -*-
"""
    celery.backends.rethinkdb
    ~~~~~~~~~~~~~~~~~~~~~~~

    RethinkDB result store backend.

"""
from __future__ import absolute_import

import json

try:
    import rethinkdb as r
except ImportError:  # pragma: no cover
    r = None   # noqa

from kombu.utils import cached_property

from celery import states
from celery.exceptions import ImproperlyConfigured
from celery.five import string_t
from celery.utils.timeutils import maybe_timedelta

from celery.backends.base import BaseBackend

__all__ = ['RethinkBackend']


class Bunch(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)


class RethinkBackend(BaseBackend):
    host = 'localhost'
    port = 28015
    database_name = 'test'
    auth_key = ''
    timeout = 20
    table_name = 'celery_taskmeta'
    options = None

    supports_autoexpire = False

    _connection = None

    def __init__(self, *args, **kwargs):
        """Initialize RethinkDB backend instance.

        :raises celery.exceptions.ImproperlyConfigured: if
            module :mod:`rethinkdb` is not available.

        """
        self.options = {}
        super(RethinkBackend, self).__init__(*args, **kwargs)
        self.expires = kwargs.get('expires') or maybe_timedelta(
            self.app.conf.CELERY_TASK_RESULT_EXPIRES)

        if not r:
            raise ImproperlyConfigured(
                'You need to install the rethinkdb library to use the '
                'RethinkDB backend.')

        config = self.app.conf.get('CELERY_RETHINKDB_BACKEND_SETTINGS')
        if config is not None:
            if not isinstance(config, dict):
                raise ImproperlyConfigured(
                    'RethinkDB backend settings should be grouped in a dict')
            config = dict(config)  # do not modify original

            self.host = config.pop('host', self.host)
            self.port = int(config.pop('port', self.port))
            self.database_name = config.pop('db', self.database_name)
            self.auth_key = config.pop('auth_key', self.auth_key)
            self.timeout = config.pop('timeout', self.timeout)
            self.table_name = config.pop('table', self.table_name)
            self.options = dict(config, **config.pop('options', None) or {})

    def _get_connection(self):
        """Connect to the RethinkDB server."""
        if self._connection is None:
            self._connection = r.connect(host=self.host,
                                         port=self.port,
                                         db=self.database_name,
                                         auth_key=self.auth_key,
                                         timeout=self.timeout,
                                         **self.options)

        return self._connection

    def process_cleanup(self):
        if self._connection is not None:
            # RethinkDB connection will be closed automatically when object
            # goes out of scope
            del(self.table)
            del(self.database)
            del(self.conn)
            self._connection.close()
            self._connection = None

    def _store_result(self, task_id, result, status,
                      traceback=None, request=None, **kwargs):
        """Store return value and status of an executed task."""
        meta = {'id': task_id,
                'status': status,
                'result': json.loads(self.encode(result)),
                'date_done': r.now(),
                'traceback': json.loads(self.encode(traceback)),
                'children': json.loads(self.encode(
                    self.current_task_children(request),
                ))}

        result = self.table.insert(meta, conflict='replace').run(self.conn)
        if result['errors']:
            raise Exception(result['first_error'])

        return meta

    def _get_task_meta_for(self, task_id):
        """Get task metadata for a task by id."""

        obj = self.table.get(task_id).run(self.conn)
        if not obj:
            return {'status': states.PENDING, 'result': None}

        meta = {
            'task_id': obj['id'],
            'status': obj['status'],
            'result': self.decode(json.dumps(obj['result'])),
            'date_done': obj['date_done'],
            'traceback': self.decode(json.dumps(obj['traceback'])),
            'children': self.decode(json.dumps(obj['children'])),
        }

        return meta

    def _save_group(self, group_id, result):
        """Save the group result."""
        meta = {'id': group_id,
                'result': json.loads(self.encode(result)),
                'date_done': r.now()}

        result = self.table.insert(meta, conflict='replace').run(self.conn)
        if result['errors']:
            raise Exception(result['first_error'])

        return meta

    def _restore_group(self, group_id):
        """Get the result for a group by id."""
        obj = self.table.get(group_id).run(self.conn)
        if not obj:
            return

        meta = {
            'task_id': obj['id'],
            'result': self.decode(json.dumps(obj['result'])),
            'date_done': obj['date_done'],
        }

        return meta

    def _delete_group(self, group_id):
        """Delete a group by id."""
        result = self.table.get(group_id).delete().run(self.conn)
        if result['errors']:
            raise Exception(result['first_error'])

    def _forget(self, task_id):
        """
        Remove result from RethinkDB.

        :raises celery.exceptions.OperationsError: if the task_id could not be
                                                   removed.
        """
        # By using safe=True, this will wait until it receives a response from
        # the server.  Likewise, it will raise an OperationsError if the
        # response was unable to be completed.
        result = self.table.get(task_id).delete().run(self.conn)
        if result['errors']:
            raise Exception(result['first_error'])

    def cleanup(self):
        """Delete expired metadata."""
        result = self.table.filter(r.row['date_done'].lt(
            self.app.now() - self.expires
        )).delete().run(self.conn)
        if result['errors']:
            raise Exception(result['first_error'])

    def __reduce__(self, args=(), kwargs={}):
        kwargs.update(
            dict(expires=self.expires))
        return super(RethinkBackendRethinkBackend, self).__reduce__(args, kwargs)

    @cached_property
    def conn(self):
        """Get RethinkDB connection."""
        conn = self._get_connection()

        return conn

    @cached_property
    def database(self):
        """Get database from RethinkDB connection."""
        self._get_connection()

        db = r.db(self.database_name)

        # Ensure database exists
        if not self.database_name in r.db_list().run(self.conn):
            r.db_create(self.database_name).run(self.conn)

        return db

    @cached_property
    def table(self):
        """Get the metadata task table."""
        table = self.database.table(self.table_name)

        # Ensure table exists
        if not self.table_name in self.database.table_list().run(self.conn):
            self.database.table_create(self.table_name).run(self.conn)

        # Ensure an index on date_done is there, if not process the index
        # in the background. Once completed cleanup will be much faster
        if not 'date_done' in table.index_list().run(self.conn):
            table.index_create('date_done').run(self.conn)

        return table
