from mltsp.Flask import flask_app as fa
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
import shutil
import ntpath
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")


def test_num_lines():
    """Test line counting"""
    num_lines = fa.num_lines(os.path.join(DATA_DIR, "dotastro_215153.dat"))
    npt.assert_equal(num_lines, 170)


def test_check_job_status():
    """Test check job status"""
    assert("finished" in fa.check_job_status(999999))
    assert("currently running" in fa.check_job_status(1))


def test_is_running():
    """Test is_running()"""
    npt.assert_equal(fa.is_running(99999), "False") # Greater than max PID
    assert(fa.is_running(1) != "False") # The init process


def test_db_init():
    """Test RethinkDB init"""
    RDB_HOST = fa.RDB_HOST
    RDB_PORT = fa.RDB_PORT
    MLTSP_DB = fa.MLTSP_DB
    table_names = ['projects', 'users', 'features',
                   'models', 'userauth', 'predictions']
    force = False
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    initial_db_list = r.db_list().run(connection)

    fa.db_init(force=force)

    assert MLTSP_DB in r.db_list().run(connection)
    connection.use(MLTSP_DB)
    if force:
        for table_name in table_names:
            npt.assert_equal(r.table(table_name).count().run(connection), 0)
    connection.close()


def test_add_user():
    """TO-DO - Test add user outside of application context"""
    # TO-DO


def test_check_user_table():
    """TO-DO - Test check user table outside of application context"""


def test_update_model_entry_with_pid():
    """Test update model entry with PID"""
    
