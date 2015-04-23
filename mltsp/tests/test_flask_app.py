from mltsp.Flask import flask_app as fa
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
import pandas as pd
import shutil
import ntpath
import uuid
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_num_lines():
    """Test line counting"""
    num_lines = fa.num_lines(pjoin(DATA_PATH, "dotastro_215153.dat"))
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
    """### TO-DO ### Test add user outside of application context"""


def test_check_user_table():
    """### TO-DO ### Test check user table outside of application context"""


def test_update_model_entry_with_pid():
    """Test update model entry with PID"""
    conn = fa.rdb_conn
    model_key = str(uuid.uuid4())[:10]
    r.table("models").insert({"id": model_key}).run(conn)
    fa.update_model_entry_with_pid(model_key, 9999)
    entry_dict = r.table("models").get(model_key).run(conn)
    npt.assert_equal(entry_dict["pid"], "9999")
    r.table("models").get(model_key).delete().run(conn)
    npt.assert_equal(r.table("models").get(model_key).run(conn), None)


def test_update_featset_entry_with_pid():
    """Test update featset entry with PID"""
    conn = fa.rdb_conn
    feat_key = str(uuid.uuid4())[:10]
    r.table("features").insert({"id": feat_key}).run(conn)
    fa.update_featset_entry_with_pid(feat_key, 9999)
    entry_dict = r.table("features").get(feat_key).run(conn)
    npt.assert_equal(entry_dict["pid"], "9999")
    r.table("features").get(feat_key).delete().run(conn)
    npt.assert_equal(r.table("features").get(feat_key).run(conn), None)


def test_update_prediction_entry_with_pid():
    """Test update prediction entry with PID"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("predictions").insert({"id": key}).run(conn)
    fa.update_prediction_entry_with_pid(key, 9999)
    entry_dict = r.table("predictions").get(key).run(conn)
    npt.assert_equal(entry_dict["pid"], "9999")
    r.table("predictions").get(key).delete().run(conn)
    npt.assert_equal(r.table("predictions").get(key).run(conn), None)


def test_update_prediction_entry_with_results():
    """Test update prediction entry with results"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("predictions").insert({"id": key}).run(conn)
    html_str = "<HTML></HTML>"
    features_dict = {"fname": {"feat1": 2.1}}
    ts_data = {"fname": [1,2,3]}
    results = {"fname": ['c1', 1.0]}
    fa.update_prediction_entry_with_results(key, html_str, features_dict,
                                            ts_data, results)
    entry_dict = r.table("predictions").get(key).run(conn)
    npt.assert_equal(entry_dict["results_str_html"], html_str)
    npt.assert_equal(entry_dict["features_dict"], features_dict)
    npt.assert_equal(entry_dict["ts_data_dict"], ts_data)
    npt.assert_equal(entry_dict["pred_results_list_dict"], results)
    r.table("predictions").get(key).delete().run(conn)


def test_update_prediction_entry_with_results_err():
    """Test update prediction entry with results - w/ err msg"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("predictions").insert({"id": key}).run(conn)
    html_str = "<HTML></HTML>"
    features_dict = {"fname": {"feat1": 2.1}}
    ts_data = {"fname": [1,2,3]}
    results = {"fname": ['c1', 1.0]}
    fa.update_prediction_entry_with_results(key, html_str, features_dict,
                                            ts_data, results, "err_msg")
    entry_dict = r.table("predictions").get(key).run(conn)
    npt.assert_equal(entry_dict["results_str_html"], html_str)
    npt.assert_equal(entry_dict["features_dict"], features_dict)
    npt.assert_equal(entry_dict["ts_data_dict"], ts_data)
    npt.assert_equal(entry_dict["pred_results_list_dict"], results)
    npt.assert_equal(entry_dict["err_msg"], "err_msg")
    r.table("predictions").get(key).delete().run(conn)


def test_update_model_entry_with_results_msg():
    """Test update model entry with results msg"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("models").insert({"id": key}).run(conn)
    fa.update_model_entry_with_results_msg(key, "MSG")
    entry_dict = r.table("models").get(key).run(conn)
    npt.assert_equal(entry_dict["results_msg"], "MSG")
    r.table("models").get(key).delete().run(conn)


def test_update_model_entry_with_results_msg_err():
    """Test update model entry with results - w/ err msg"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("models").insert({"id": key}).run(conn)
    fa.update_model_entry_with_results_msg(key, "MSG", err="ERR_MSG")
    entry_dict = r.table("models").get(key).run(conn)
    npt.assert_equal(entry_dict["results_msg"], "MSG")
    npt.assert_equal(entry_dict["err_msg"], "ERR_MSG")
    r.table("models").get(key).delete().run(conn)


def test_update_featset_entry_with_results_msg():
    """Test update featset entry with results msg"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("features").insert({"id": key}).run(conn)
    fa.update_featset_entry_with_results_msg(key, "MSG")
    entry_dict = r.table("features").get(key).run(conn)
    npt.assert_equal(entry_dict["results_msg"], "MSG")
    r.table("features").get(key).delete().run(conn)


def test_update_featset_entry_with_results_msg_err():
    """Test update featset entry with results msg - err"""
    conn = fa.rdb_conn
    key = str(uuid.uuid4())[:10]
    r.table("features").insert({"id": key}).run(conn)
    fa.update_featset_entry_with_results_msg(key, "MSG", "ERR_MSG")
    entry_dict = r.table("features").get(key).run(conn)
    npt.assert_equal(entry_dict["results_msg"], "MSG")
    npt.assert_equal(entry_dict["err_msg"], "ERR_MSG")
    r.table("features").get(key).delete().run(conn)


def test_get_current_userkey():
    """### TO-DO ### Test get current user key outisde of application context"""


def test_get_all_projkeys():
    """Test get all project keys"""
    conn = fa.rdb_conn
    keys = []
    for i in range(3):
        key = str(uuid.uuid4())[:10]
        keys.append(key)
        r.table("projects").insert({"id": key}).run(conn)
    all_projkeys = fa.get_all_projkeys()
    assert all(key in all_projkeys for key in keys)
    r.table("projects").get_all(*keys).delete().run(conn)


def test_get_authed_projkeys():
    """Test get authed project keys"""
    conn = fa.rdb_conn
    keys = []
    for i in range(3):
        key = str(uuid.uuid4())[:10]
        keys.append(key)
        r.table("userauth").insert({"projkey": key, "id": key,
                                    "userkey": "testhandle@gmail.com",
                                    "active": "y"}).run(conn)
    authed_projkeys = fa.get_authed_projkeys("testhandle@gmail.com")
    npt.assert_equal(len(authed_projkeys), 3)
    assert all(key in authed_projkeys for key in keys)
    r.table("userauth").get_all(*keys).delete().run(conn)


def test_get_authed_projkeys_not_authed():
    """Test get authed project keys - not authorized"""
    conn = fa.rdb_conn
    keys = []
    for i in range(3):
        key = str(uuid.uuid4())[:10]
        keys.append(key)
        r.table("userauth").insert({"projkey": key, "id": key,
                                    "userkey": "testhandle@gmail.com",
                                    "active": "y"}).run(conn)
    authed_projkeys = fa.get_authed_projkeys("testhandle2@gmail.com")
    npt.assert_equal(len(authed_projkeys), 0)
    assert all(key not in authed_projkeys for key in keys)
    r.table("userauth").get_all(*keys).delete().run(conn)


def test_get_authed_projkeys_inactive():
    """Test get authed project keys - inactive"""
    conn = fa.rdb_conn
    keys = []
    for i in range(3):
        key = str(uuid.uuid4())[:10]
        keys.append(key)
        r.table("userauth").insert({"projkey": key, "id": key,
                                    "userkey": "testhandle@gmail.com",
                                    "active": "n"}).run(conn)
    authed_projkeys = fa.get_authed_projkeys("testhandle@gmail.com")
    npt.assert_equal(len(authed_projkeys), 0)
    assert all(key not in authed_projkeys for key in keys)
    r.table("userauth").get_all(*keys).delete().run(conn)


def test_list_featuresets():
    """Test list featuresets"""
    
