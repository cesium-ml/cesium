from cesium_app.config import cfg
print('[testing] Configure cesium to use test database')
cfg['testing']['test_db'] = 1

print('[testing] Configure cesium to disable authentication')
cfg['testing']['disable_auth'] = 1

import os
from cesium_app import flask_app as fa
from cesium_app import custom_exceptions
from cesium_app import docker_util
import cesium
from cesium import build_model
from cesium import obs_feature_tools as oft
from cesium import science_feature_tools as sft
from nose.tools import with_setup
import numpy.testing as npt
from numpy.testing import decorators as dec
import numpy as np
from os.path import join as pjoin
import uuid
import rethinkdb as rdb
import unittest
import time
import json
import shutil
import pandas as pd
import xarray as xr
from sklearn.externals import joblib

DATA_DIR = pjoin(os.path.dirname(cesium.__file__), "tests/data")
APP_DATA_DIR = pjoin(os.path.dirname(__file__), "data")
TEST_EMAIL = "testhandle@test.com"
TEST_PASSWORD = "TestPass15"

fa.db_init(force=True)

# Need at least 2 of each class for stratified splitting
TS_FILES = ["dotastro_215153_with_class.nc", "dotastro_215176_with_class.nc",
           "dotastro_215153_with_class_copy.nc",
            "dotastro_215176_with_class_copy.nc"]
CUSTOM_SCRIPT = "testfeature1.py"
if docker_util.docker_images_available():
    USE_DOCKER = True
else:
    USE_DOCKER = False
    print("WARNING: computing custom features outside Docker container...")

def featurize_setup():
    ts_paths = [pjoin(cfg['paths']['upload_folder'], f) for f in TS_FILES]
    custom_script_path = pjoin(cfg['paths']['upload_folder'], CUSTOM_SCRIPT)
    for fname in TS_FILES:
        fpath = pjoin(DATA_DIR, fname)
        shutil.copy(fpath, cfg['paths']['upload_folder'])
    shutil.copy(pjoin(APP_DATA_DIR, CUSTOM_SCRIPT), cfg['paths']['upload_folder'])
    rdb.table("datasets").insert({"id": "ds1", "projkey": "111",
                                "name": "Test dataset", "created": "111",
                                "ts_filenames": ts_paths}).run(fa.g.rdb_conn)
    return ts_paths, custom_script_path


def delete_entries_by_table(table_name):
    conn = fa.g.rdb_conn
    for e in rdb.table(table_name).run(conn):
        rdb.table(table_name).get(e['id']).delete().run(conn)


def featurize_teardown():
    for fname in TS_FILES + [CUSTOM_SCRIPT]:
        fpath = pjoin(cfg['paths']['upload_folder'], fname)
        if os.path.exists(fpath):
            os.remove(fpath)


def build_model_setup():
    shutil.copy(pjoin(DATA_DIR, "test_featureset.nc"),
                pjoin(cfg['paths']['features_folder'], "test_featureset.nc"))
    shutil.copy(pjoin(DATA_DIR, "asas_training_subset_featureset.nc"),
                pjoin(cfg['paths']['features_folder'], "asas_training_subset_featureset.nc"))


def prediction_setup():
    fa.app.preprocess_request()
    conn = fa.g.rdb_conn
    fset = xr.open_dataset(pjoin(DATA_DIR, "test_featureset.nc"))
    model_path = pjoin(cfg['paths']['models_folder'], "test.pkl")
    build_model.create_and_pickle_model(fset, "RandomForestClassifier",
                                        model_path)
    ts_paths = [pjoin(cfg['paths']['upload_folder'], f) for f in TS_FILES]
    custom_script_path = pjoin(cfg['paths']['upload_folder'], CUSTOM_SCRIPT)
    for fname in TS_FILES:
        fpath = pjoin(DATA_DIR, fname)
        shutil.copy(fpath, cfg['paths']['upload_folder'])
    rdb.table("datasets").insert({"id": "ds1", "projkey": "111",
                                "name": "Test dataset", "created": "111",
                                "ts_filenames": ts_paths}).run(fa.g.rdb_conn)
    rdb.table("projects").insert({"id": "test",
                                "name": "test"}).run(conn)
    rdb.table("features").insert({"id": "test",
                                "projkey": "test",
                                "name": "test",
                                "created": "test",
                                "meta_feats": ["meta1", "meta2", "meta3"],
                                "featlist": ["std_err", "amplitude"]}).run(conn)
    rdb.table("models").insert({"id": "test",
                              "type": "RandomForestClassifier",
                              "featset_key": "test",
                              "featureset_name": "test",
                              "projkey": "test",
                              "parameters": {},
                              "name": "test"}).run(conn)
    return ts_paths, custom_script_path


def model_and_prediction_teardown():
    fnames = ["test_featureset.nc", "asas_training_subset_featureset.nc",
              "test.pkl"]
    for fname in fnames:
        for data_dir in [cfg['paths']['features_folder'], cfg['paths']['models_folder']]:
            try:
                os.remove(pjoin(data_dir, fname))
            except OSError:
                pass


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        fa.app.testing = True
        fa.app.config['DEBUG'] = True
        fa.app.config['WTF_CSRF_ENABLED'] = False
        self.app = fa.app.test_client()
        self.login()
        self.app.post('/check_user_table')

    def tearDown(self):
        """Reset database to initial empty state after each test. Leaves users,
        userauth intact.
        """
        conn = rdb.connect(db="cesium_testing")
        for table_name in ["models", "features", "predictions", "projects", "datasets"]:
            rdb.table(table_name).delete().run(conn)

    def login(self, username=TEST_EMAIL, password=TEST_PASSWORD, app=None):
        if app is None:
            app = self.app
        return app.post('/login', data=dict(
            login=username,
            password=password
        ), follow_redirects=True)

    def test_check_job_status(self):
        """Test check job status"""
        rv = self.app.post('/check_job_status/?PID=999999')
        assert b'finished' in rv.data
        rv = self.app.post('/check_job_status/?PID=1')
        assert b'currently running' in rv.data

    def test_is_running(self):
        """Test is_running()"""
        npt.assert_equal(fa.is_running(99999), "False")  # Greater than max PID
        assert(fa.is_running(1) != "False")  # The init process

    def test_db_init(self):
        """Test RethinkDB init"""
        RDB_HOST = fa.RDB_HOST
        RDB_PORT = fa.RDB_PORT
        CESIUM_DB = fa.CESIUM_DB
        table_names = ['projects', 'users', 'features',
                       'models', 'userauth', 'predictions']
        force = False
        connection = rdb.connect(host=RDB_HOST, port=RDB_PORT)
        initial_db_list = rdb.db_list().run(connection)
        fa.db_init(force=force)
        assert CESIUM_DB in rdb.db_list().run(connection)
        connection.use(CESIUM_DB)
        if force:
            for table_name in table_names:
                npt.assert_equal(rdb.table(table_name).count().run(connection),
                                 0)
        connection.close()

    def test_add_user(self):
        """Test add user"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            fa.add_user()
            N = rdb.table("users").filter({"email": TEST_EMAIL})\
                                .count().run(fa.g.rdb_conn)
            npt.assert_equal(N, 1)
            rdb.table('users').get(TEST_EMAIL).delete().run(fa.g.rdb_conn)
            N = rdb.table("users").filter({"email": TEST_EMAIL})\
                                .count().run(fa.g.rdb_conn)
            npt.assert_equal(N, 0)

    def test_check_user_table(self):
        """Test check user table"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            N = rdb.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            if N > 0:
                rdb.table("users").get(TEST_EMAIL).delete().run(conn)
                N = rdb.table('users').filter({'email': TEST_EMAIL}).count()\
                                                                  .run(conn)
                npt.assert_equal(N, 0)

            fa.check_user_table()
            N = rdb.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 1)
            rdb.table("users").get(TEST_EMAIL).delete().run(conn)
            rdb.table("users").insert({"id": TEST_EMAIL,
                                     "email": TEST_EMAIL})\
                .run(conn)
            N = rdb.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 1)
            fa.check_user_table()
            N = rdb.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 1)
            rdb.table("users").get(TEST_EMAIL).delete().run(conn)
            N = rdb.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 0)

    def test_update_model_entry_with_pid(self):
        """Test update model entry with PID"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            model_key = str(uuid.uuid4())[:10]
            rdb.table("models").insert({"id": model_key}).run(conn)
            fa.update_model_entry_with_pid(model_key, 9999)
            entry_dict = rdb.table("models").get(model_key).run(conn)
            npt.assert_equal(entry_dict["pid"], "9999")
            rdb.table("models").get(model_key).delete().run(conn)
            npt.assert_equal(rdb.table("models").get(model_key).run(conn), None)

    def test_update_featset_entry_with_pid(self):
        """Test update featset entry with PID"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            feat_key = str(uuid.uuid4())[:10]
            rdb.table("features").insert({"id": feat_key}).run(conn)
            fa.update_featset_entry_with_pid(feat_key, 9999)
            entry_dict = rdb.table("features").get(feat_key).run(conn)
            npt.assert_equal(entry_dict["pid"], "9999")
            rdb.table("features").get(feat_key).delete().run(conn)
            npt.assert_equal(rdb.table("features").get(feat_key).run(conn), None)

    def test_update_prediction_entry_with_pid(self):
        """Test update prediction entry with PID"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("predictions").insert({"id": key}).run(conn)
            fa.update_prediction_entry_with_pid(key, 9999)
            entry_dict = rdb.table("predictions").get(key).run(conn)
            npt.assert_equal(entry_dict["pid"], "9999")
            rdb.table("predictions").get(key).delete().run(conn)
            npt.assert_equal(rdb.table("predictions").get(key).run(conn), None)

    def test_update_prediction_entry_with_results(self):
        """Test update prediction entry with results"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("predictions").insert({"id": key}).run(conn)
            html_str = "<HTML></HTML>"
            features_dict = {"fname": {"feat1": 2.1}}
            ts_data = {"fname": [1, 2, 3]}
            results = {"fname": ['c1', 1.0]}
            fa.update_prediction_entry_with_results(key, html_str,
                                                    features_dict,
                                                    ts_data, results)
            entry_dict = rdb.table("predictions").get(key).run(conn)
            npt.assert_equal(entry_dict["results_str_html"], html_str)
            npt.assert_equal(entry_dict["features_dict"], features_dict)
            npt.assert_equal(entry_dict["ts_data_dict"], ts_data)
            npt.assert_equal(entry_dict["pred_results_dict"], results)

    def test_update_prediction_entry_with_results_err(self):
        """Test update prediction entry with results - w/ err msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("predictions").insert({"id": key}).run(conn)
            html_str = "<HTML></HTML>"
            features_dict = {"fname": {"feat1": 2.1}}
            ts_data = {"fname": [1, 2, 3]}
            results = {"fname": ['c1', 1.0]}
            fa.update_prediction_entry_with_results(key, html_str,
                                                    features_dict,
                                                    ts_data, results,
                                                    "err_msg")
            entry_dict = rdb.table("predictions").get(key).run(conn)
            npt.assert_equal(entry_dict["results_str_html"], html_str)
            npt.assert_equal(entry_dict["features_dict"], features_dict)
            npt.assert_equal(entry_dict["ts_data_dict"], ts_data)
            npt.assert_equal(entry_dict["pred_results_dict"], results)
            npt.assert_equal(entry_dict["err_msg"], "err_msg")

    def test_update_model_entry_with_results_msg(self):
        """Test update model entry with results msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("models").insert({"id": key}).run(conn)
            fa.update_model_entry_with_results_msg(key, "MSG")
            entry_dict = rdb.table("models").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")

    def test_update_model_entry_with_results_msg_err(self):
        """Test update model entry with results - w/ err msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("models").insert({"id": key}).run(conn)
            fa.update_model_entry_with_results_msg(key, "MSG", err="ERR_MSG")
            entry_dict = rdb.table("models").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")
            npt.assert_equal(entry_dict["err_msg"], "ERR_MSG")

    def test_update_featset_entry_with_results_msg(self):
        """Test update featset entry with results msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("features").insert({"id": key}).run(conn)
            fa.update_featset_entry_with_results_msg(key, "MSG")
            entry_dict = rdb.table("features").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")

    def test_update_featset_entry_with_results_msg_err(self):
        """Test update featset entry with results msg - err"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            rdb.table("features").insert({"id": key}).run(conn)
            fa.update_featset_entry_with_results_msg(key, "MSG", "ERR_MSG")
            entry_dict = rdb.table("features").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")
            npt.assert_equal(entry_dict["err_msg"], "ERR_MSG")

    def test_get_current_userkey(self):
        """Test get current user key"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"id": TEST_EMAIL, "email": TEST_EMAIL})\
                            .run(conn)
            result = fa.get_current_userkey()
            rdb.table("users").get(TEST_EMAIL).delete().run(conn)
            npt.assert_equal(result, TEST_EMAIL)

    def test_get_all_projkeys(self):
        """Test get all project keys"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            keys = []
            for i in range(3):
                key = str(uuid.uuid4())[:10]
                keys.append(key)
                rdb.table("projects").insert({"id": key}).run(conn)
            all_projkeys = fa.get_all_projkeys()
            assert all(key in all_projkeys for key in keys)

    def test_get_authed_projkeys(self):
        """Test get authed project keys"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            keys = []
            for i in range(3):
                key = str(uuid.uuid4())[:10]
                keys.append(key)
                rdb.table("userauth").insert({"projkey": key, "id": key,
                                            "userkey": "testhandle@gmail.com",
                                            "active": "y"}).run(conn)
            authed_projkeys = fa.get_authed_projkeys("testhandle@gmail.com")
            rdb.table("userauth").get_all(*keys).delete().run(conn)
            npt.assert_equal(len(authed_projkeys), 3)
            assert all(key in authed_projkeys for key in keys)

    def test_get_authed_projkeys_not_authed(self):
        """Test get authed project keys - not authorized"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            keys = []
            for i in range(3):
                key = str(uuid.uuid4())[:10]
                keys.append(key)
                rdb.table("userauth").insert({"projkey": key, "id": key,
                                            "userkey": "testhandle@gmail.com",
                                            "active": "y"}).run(conn)
            authed_projkeys = fa.get_authed_projkeys("testhandle2@gmail.com")
            rdb.table("userauth").get_all(*keys).delete().run(conn)
            npt.assert_equal(len(authed_projkeys), 0)
            assert all(key not in authed_projkeys for key in keys)

    def test_get_authed_projkeys_inactive(self):
        """Test get authed project keys - inactive"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            keys = []
            for i in range(3):
                key = str(uuid.uuid4())[:10]
                keys.append(key)
                rdb.table("userauth").insert({"projkey": key, "id": key,
                                            "userkey": "testhandle@gmail.com",
                                            "active": "n"}).run(conn)
            authed_projkeys = fa.get_authed_projkeys("testhandle@gmail.com")
            rdb.table("userauth").get_all(*keys).delete().run(conn)
            npt.assert_equal(len(authed_projkeys), 0)
            assert all(key not in authed_projkeys for key in keys)

    def test_list_featuresets_authed(self):
        """Test list featuresets - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("features").insert({"id": "111", "projkey": "111",
                                        "name": "111", "created": "111",
                                        "featlist": [1, 2]}).run(conn)
            featsets = fa.list_featuresets()
            rdb.table("userauth").get("test").delete().run(conn)
            npt.assert_equal(len(featsets), 1)
            assert "created" in featsets[0] and "test" in featsets[0]

    def test_list_featuresets_all(self):
        """Test list featuresets - all featsets and name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("features").insert({"id": "111", "projkey": "111",
                                        "name": "111", "created": "111",
                                        "featlist": [1, 2]}).run(conn)
            featsets = fa.list_featuresets(auth_only=False, name_only=True)
            rdb.table("userauth").get("test").delete().run(conn)
            assert len(featsets) > 1
            assert all("created" not in featset for featset in featsets)

    def test_list_featuresets_html(self):
        """Test list featuresets - as HTML and by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("userauth").insert({"projkey": "111", "id": "111",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("features").insert({"id": "111", "projkey": "111",
                                        "name": "111", "created": "111",
                                        "featlist": [1, 2]}).run(conn)
            featsets = fa.list_featuresets(auth_only=True, by_project="test",
                                           as_html_table_string=True)
            rdb.table("userauth").get("test").delete().run(conn)
            rdb.table("userauth").get("111").delete().run(conn)
            assert "table id" in featsets and "test" in featsets

    def test_list_models_authed(self):
        """Test list models - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "created": "test",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("models").insert({"id": "111", "projkey": "111",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "name": "111", "created": "111",
                                      "meta_feats": ["1", "2"]}).run(conn)
            models = fa.list_models()
            npt.assert_equal(len(models), 1)
            rdb.table("userauth").get("test").delete().run(conn)
            assert "created" in models[0] and "test" in models[0]

    def test_list_models_all(self):
        """Test list models - all models and name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test",
                                      "type":
                                      "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "created": "test",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("models").insert({"id": "111", "projkey": "111",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "name": "111", "created": "111",
                                      "meta_feats": ["1", "2"]}).run(conn)
            results = fa.list_models(auth_only=False, name_only=True)
            rdb.table("userauth").get("test").delete().run(conn)
            assert len(results) > 1
            assert all("created" not in result for result in results)

    def test_list_models_html(self):
        """Test list models - as HTML and by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("userauth").insert({"projkey": "111", "id": "111",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test",
                                      "type":
                                      "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "created": "test",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("models").insert({"id": "111", "projkey": "111",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "name": "111", "created": "111",
                                      "meta_feats": ["1", "2"]}).run(conn)
            results = fa.list_models(auth_only=True, by_project="test",
                                     as_html_table_string=True)
            rdb.table("userauth").get("test").delete().run(conn)
            rdb.table("userauth").get("111").delete().run(conn)
            assert "table id" in results and "test" in results

    def test_list_preds_authed(self):
        """Test list predictions - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "MODEL_NAME",
                                           "created": "test",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                .run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("predictions").insert({"id": "111", "projkey": "111",
                                           "name": "111",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "MODEL_NAME",
                                           "created": "111",
                                           "filename": "111.txt",
                                           "results_str_html": "111HTML"})\
                .run(conn)
            results = fa.list_predictions(auth_only=True)
            rdb.table("userauth").get("test").delete().run(conn)
            npt.assert_equal(len(results), 1)
            assert "MODEL_NAME" in results[0]

    def test_list_predictions_all(self):
        """Test list predictions - all predictions, name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "MODEL_NAME",
                                           "created": "test",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                .run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("predictions").insert({"id": "111", "projkey": "111",
                                           "name": "111",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "MODEL_NAME",
                                           "created": "111",
                                           "filename": "111.txt",
                                           "results_str_html": "111HTML"})\
                .run(conn)
            results = fa.list_predictions(auth_only=False, detailed=False)
            rdb.table("userauth").get("test").delete().run(conn)
            assert len(results) > 1
            assert all("created" not in result for result in results)

    def test_list_predictions_html(self):
        """Test list predictions - as HTML and by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("userauth").insert({"projkey": "111", "id": "111",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "MODEL_NAME",
                                           "created": "test",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                .run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            rdb.table("predictions").insert({"id": "111", "projkey": "111",
                                           "name": "111",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "MODEL_NAME",
                                           "created": "111",
                                           "filename": "111.txt",
                                           "results_str_html": "111HTML"})\
                .run(conn)
            results = fa.list_predictions(by_project="test",
                                          as_html_table_string=True)
            rdb.table("userauth").get("test").delete().run(conn)
            rdb.table("userauth").get("111").delete().run(conn)
            assert "table id" in results and "test" in results

    def test_get_list_of_projects(self):
        """Test get list of projects"""
        conn = fa.rdb_conn
        rdb.table("projects").insert({"id": "test",
                                    "name": "test"}).run(conn)
        rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                    "userkey": TEST_EMAIL,
                                    "email": TEST_EMAIL,
                                    "active": "y"}).run(conn)
        rv = self.app.get('/get_list_of_projects')
        rdb.table("userauth").get("test").delete().run(conn)
        assert "test" in json.loads(rv.data.decode())["list"]

    def test_list_projects_authed(self):
        """Test list projects - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            results = fa.list_projects()
            rdb.table("userauth").get("test").delete().run(conn)
            npt.assert_equal(len(results), 1)
            assert "test" in results[0]

    def test_list_projects_all(self):
        """Test list projects - all and name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("userauth").insert({"projkey": "test", "id": "test",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            results = fa.list_projects(auth_only=False, name_only=True)
            rdb.table("userauth").get("test").delete().run(conn)
            assert len(results) >= 2
            assert all("created" not in res for res in results)

    def test_add_project(self):
        """Test add project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_projkey = fa.add_project(name="TEST")
            entry = rdb.table("projects").get(new_projkey).run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['description'], "")
            cur = rdb.table("userauth").filter({"projkey": new_projkey})\
                                     .run(conn)
            auth_entries = []
            for e in cur:
                auth_entries.append(e)
            rdb.table("userauth").get(auth_entries[0]["id"]).delete().run(conn)
            npt.assert_equal(len(auth_entries), 1)
            npt.assert_equal(auth_entries[0]["active"], "y")

    def test_add_project_addl_users(self):
        """Test add project - addl users"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_projkey = fa.add_project(name="TEST",
                                         addl_authed_users=["1@2.com"])
            entry = rdb.table("projects").get(new_projkey).run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['description'], "")
            cur = rdb.table("userauth").filter({"projkey": new_projkey})\
                                     .run(conn)
            auth_entries = []
            for e in cur:
                auth_entries.append(e)
            rdb.table("userauth").get(auth_entries[0]["id"]).delete().run(conn)
            rdb.table("userauth").get(auth_entries[1]["id"]).delete().run(conn)
            npt.assert_equal(len(auth_entries), 2)
            npt.assert_equal(auth_entries[0]["active"], "y")

    def test_add_featureset(self):
        """Test add feature set"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_featset_key = fa.add_featureset(name="TEST", projkey="abc",
                                                pid="2", featlist=['f1', 'f2'])
            entry = rdb.table("features").get(new_featset_key).run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['featlist'], ['f1', 'f2'])

    def test_add_model(self):
        """Test add model"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_key = fa.add_model(model_name="TEST_NAME",
                                   featureset_name="TEST",
                                   featureset_key="123",
                                   model_type="RandomForestClassifier",
                                   model_params={},
                                   projkey="ABC", pid="2")
            entry = rdb.table("models").get(new_key).run(conn)
            npt.assert_equal(entry['name'], "TEST_NAME")
            npt.assert_equal(entry['projkey'], "ABC")
            rdb.table("models").get(new_key).delete().run(conn)

    def test_add_model_meta_feats(self):
        """Test add model - with meta features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("features").insert({"id": "123",
                                        "meta_feats": ['f1', 'f2']}).run(conn)
            new_key = fa.add_model(model_name="TEST_NAME",
                                   featureset_name="TEST",
                                   featureset_key="123",
                                   model_type="RandomForestClassifier",
                                   model_params={},
                                   projkey="ABC", pid="2")
            entry = rdb.table("models").get(new_key).run(conn)
            npt.assert_equal(entry['name'], "TEST_NAME")
            npt.assert_equal(entry['projkey'], "ABC")
            npt.assert_equal(entry['meta_feats'], ['f1', 'f2'])
            rdb.table("models").get(new_key).delete().run(conn)

    def test_add_prediction(self):
        """Test add prediction entry"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            new_key = fa.add_prediction(project_name="test",
                                        model_key="model_key",
                                        model_name="model_name",
                                        model_type="RandomForestClassifier",
                                        dataset_id="ds1",
                                        pid="2")
            entry = rdb.table("predictions").get(new_key).run(conn)
            npt.assert_equal(entry['project_name'], "test")

    def test_get_projects_associated_files(self):
        """Test get project's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.project_associated_files("test")
            npt.assert_equal(fpaths, [])
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "created": "test",
                                      "featset_key": "test",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "model_name": "test",
                                           "created": "test",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                .run(conn)
            fpaths = fa.project_associated_files("test")
            short_fnames = [os.path.basename(fpath) for fpath in fpaths]
            assert all(fname in short_fnames for fname in
                       ["test.pkl"])

    def test_get_models_associated_files(self):
        """Test get model's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.model_associated_files("test")
            npt.assert_equal(fpaths, [])
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "created": "test",
                                      "featset_key": "test",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            fpaths = fa.model_associated_files("test")
            short_fnames = [os.path.basename(fpath) for fpath in fpaths]
            assert all(fname in short_fnames for fname in
                       ["test.pkl"])

    def test_get_featsets_associated_files(self):
        """Test get feature set's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.featset_associated_files("test")
            npt.assert_equal(fpaths, [])
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            fpaths = fa.featset_associated_files("test")
            short_fnames = [os.path.basename(fpath) for fpath in fpaths]
            assert all(fname in short_fnames for fname in
                       ["ZIPPATH.tar.gz", "HEADPATH.dat"])

    def test_get_prediction_associated_files(self):
        """ ## TO-DO ## Test get prediction's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.prediction_associated_files("test")

    def test_delete_associated_project_data_features(self):
        """Test delete associated project data - features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test_featureset.nc"),
                 "w").close()
            assert os.path.exists(pjoin(cfg['paths']['features_folder'],
                                        "test_featureset.nc"))
            fa.delete_associated_project_data("features", "test")
            count = rdb.table("features").filter({"id":
                                                "test"}).count().run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test_featureset.nc"))

    def test_delete_associated_project_data_models(self):
        """Test delete associated project data - models"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "featset_key": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['models_folder'], "test.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            fa.delete_associated_project_data("models", "test")
            count = rdb.table("models").filter({"id": "test"}).count()\
                                                              .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg['paths']['models_folder'],
                                            "test.pkl"))

    def test_delete_associated_project_data_predictions(self):
        """Test delete associated project data - predictions"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test",
                                           "headerfile_path": "HEADPATH.dat",
                                           "zipfile_path": "ZIPPATH.tar.gz",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            fa.delete_associated_project_data("predictions", "test")
            count = rdb.table("predictions").filter({"id": "test"}).count()\
                                                                   .run(conn)
            npt.assert_equal(count, 0)

    def test_delete_project(self):
        """Test delete project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "featset_key": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test",
                                           "headerfile_path": "HEADPATH.dat",
                                           "zipfile_path": "ZIPPATH.tar.gz",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test_featureset.nc"),
                 "w").close()
            assert os.path.exists(pjoin(cfg['paths']['features_folder'],
                                        "test_featureset.nc"))
            open(pjoin(cfg['paths']['models_folder'], "test.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            # Call the method being tested
            fa.delete_project("test")
            count = rdb.table("projects").filter({"id": "test"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            count = rdb.table("features").filter({"id": "test"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test_featureset.nc"))
            count = rdb.table("models").filter({"id": "test"}).count()\
                                                              .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg['paths']['models_folder'],
                                            "test.pkl"))
            count = rdb.table("predictions").filter({"id": "test"}).count()\
                                                                   .run(conn)
            npt.assert_equal(count, 0)

    def test_get_project_details(self):
        """Test get project details"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("userauth").insert({"id": "test",
                                        "projkey": "test",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("userauth").insert({"id": "test_2",
                                        "projkey": "test",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "featset_key": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test",
                                           "model_name": "test",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "filename": "FNAME.dat",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            proj_info = fa.get_project_details("test")
            rdb.table("userauth").get("test").delete().run(conn)
            rdb.table("userauth").get("test_2").delete().run(conn)
            assert all(email in proj_info["authed_users"] for email in
                       [TEST_EMAIL, "abc@123.com"])
            assert "<table" in proj_info["featuresets"] and "test" in \
                proj_info["featuresets"]
            assert "<table" in proj_info["models"] and "test" in \
                proj_info["models"]
            assert all(x in proj_info["predictions"] for x in
                       ["<table", "RandomForestClassifier", "test",
                        "FNAME.dat"])

    def test_get_project_details_json(self):
        """Test get projects details as JSON"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("userauth").insert({"id": "test",
                                        "projkey": "test",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("userauth").insert({"id": "test_2",
                                        "projkey": "test",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "featset_key": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test",
                                           "model_name": "test",
                                           "model_type":
                                           "RandomForestClassifier",
                                           "filename": "FNAME.dat",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            rv = self.app.post("/get_project_details/test")
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("userauth").get("test").delete().run(conn)
            rdb.table("userauth").get("test_2").delete().run(conn)
        res_dict = json.loads(rv.data.decode())
        npt.assert_equal(res_dict['name'], "test")
        npt.assert_array_equal(sorted(res_dict["authed_users"]),
                               ['abc@123.com', 'testhandle@test.com'])
        assert "FNAME.dat" in res_dict["predictions"]
        assert "test" in res_dict["models"]

    def test_get_authed_users(self):
        """Test get authed users"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("userauth").insert({"id": "test",
                                        "projkey": "test",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("userauth").insert({"id": "test_2",
                                        "projkey": "test",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            authed_users = fa.get_authed_users("test")
            rdb.table("userauth").get("test").delete().run(conn)
            rdb.table("userauth").get("test_2").delete().run(conn)
            npt.assert_array_equal(sorted(authed_users),
                                   sorted([TEST_EMAIL, "abc@123.com"] +
                                          fa.sys_admin_emails))

    def test_project_name_to_key(self):
        """Test project name to key"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test_name"}).run(conn)
            key = fa.project_name_to_key("test_name")
            npt.assert_equal(key, "test")

    def test_featureset_name_to_key(self):
        """Test featureset name to key"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("features").insert({"id": "test",
                                        "name": "test_name",
                                        "projkey": "test"}).run(conn)
            key = fa.featureset_name_to_key("test_name",
                                            project_id="test")
            npt.assert_equal(key, "test")

    def test_featureset_name_to_key_projname(self):
        """Test featureset name to key - with project name"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("features").insert({"id": "test",
                                        "name": "test_name",
                                        "projkey": "test"}).run(conn)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test_name"}).run(conn)
            key = fa.featureset_name_to_key("test_name",
                                            project_name="test_name")
            npt.assert_equal(key, "test")

    def test_update_project_info(self):
        """Test update project info"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            for table_name in ("userauth", "projects"):
                delete_entries_by_table(table_name)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("userauth").insert({"id": "test",
                                        "projkey": "test",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            rdb.table("userauth").insert({"id": "test_2",
                                        "projkey": "test",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            fa.update_project_info("test", "new_name", "DESC!", [])
            proj_dets = fa.get_project_details("new_name")
            npt.assert_equal(
                rdb.table("userauth").filter(
                    {"id": "test_2"}).count().run(conn),
                0)
            npt.assert_equal(proj_dets["description"], "DESC!")

    def test_update_project_info_delete_features(self):
        """Test update project info - delete features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test_featureset.nc"), "w")\
                .close()
            fa.update_project_info("test", "test", "", [],
                                   delete_features_keys=["test"])
            rdb.table("projects").get("test").delete().run(conn)
            npt.assert_equal(rdb.table("features").filter({"id":"test"})\
                             .count().run(conn), 0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test_featureset.nc"))

    def test_update_project_info_delete_models(self):
        """Test update project info - delete models"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            featurize_setup()
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "featset_key": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['models_folder'], "test.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            fa.update_project_info("test", "test", "", [],
                                   delete_model_keys=["test"])
            npt.assert_equal(
                rdb.table("models").filter({"id": "test"}).count().run(conn),
                0)
            assert not os.path.exists(
                pjoin(cfg['paths']['models_folder'], "test.pkl"))

    def test_update_project_info_delete_predictions(self):
        """Test update project info - delete predictions"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test"}).run(conn)
            fa.update_project_info("test", "test", "", [],
                                   delete_prediction_keys=["test"])
            rdb.table("projects").get("test").delete().run(conn)
            npt.assert_equal(
                rdb.table("predictions").filter(
                    {"id": "test"}).count().run(conn),
                0)

    def test_get_all_info_dict(self):
        """Test get all info dict - auth only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            d = fa.get_all_info_dict()
            npt.assert_equal(len(d['list_of_current_projects']), 0)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            d = fa.get_all_info_dict()
            rdb.table("projects").get("test").delete().run(conn)
            npt.assert_equal(len(d['list_of_current_projects']), 0)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("userauth").insert({"id": "test",
                                        "projkey": "test",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            d = fa.get_all_info_dict()
            rdb.table("userauth").get("test").delete().run(conn)
            npt.assert_array_equal(d['list_of_current_projects'], ["test"])

    def test_get_all_info_dict_unauthed(self):
        """Test get all info dict - unauthed"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            d = fa.get_all_info_dict()
            npt.assert_equal(len(d['list_of_current_projects']), 0)
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            d = fa.get_all_info_dict(auth_only=False)
            assert len(d["list_of_current_projects"]) > 0

    def test_get_list_of_available_features(self):
        """Test get list of available features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            featlist = fa.get_list_of_available_features()
            expected = sorted(sft.FEATURES_LIST)
            npt.assert_array_equal(featlist, expected)

    def test_get_list_of_available_features_set2(self):
        """Test get list of available features - set 2"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            featlist = fa.get_list_of_available_features_set2()
            expected = sorted(oft.FEATURES_LIST)
            npt.assert_array_equal(featlist, expected)

    def test_allowed_file(self):
        """Test allowed file type"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            npt.assert_equal(fa.allowed_file("abc.dat"), True)
            npt.assert_equal(fa.allowed_file("abc.csv"), True)
            npt.assert_equal(fa.allowed_file("abc.txt"), True)
            npt.assert_equal(fa.allowed_file("abc.exe"), False)
            npt.assert_equal(fa.allowed_file("abc.sh"), False)

    def test_check_headerfile_and_tsdata_format_pass(self):
        """Test check header file and TS data format - pass"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            npt.assert_equal(
                fa.check_headerfile_and_tsdata_format(
                    pjoin(DATA_DIR, "asas_training_subset_classes.dat"),
                    pjoin(DATA_DIR, "asas_training_subset.tar.gz")),
                False)

    def test_check_headerfile_and_tsdata_format_raisefnameerr(self):
        """Test check header file and TS data format - raise file name error"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            with self.assertRaises(custom_exceptions.TimeSeriesFileNameError):
                fa.check_headerfile_and_tsdata_format(
                    pjoin(DATA_DIR, "asas_training_subset_classes.dat"),
                    pjoin(DATA_DIR, "215153_215176_218272_218934.tar.gz"))

    def test_check_headerfile_and_tsdata_format_header_err(self):
        """Test check header file and TS data format - header file error"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            with self.assertRaises(custom_exceptions.DataFormatError):
                fa.check_headerfile_and_tsdata_format(
                    pjoin(DATA_DIR, "improperlyformattedheader.dat"),
                    pjoin(DATA_DIR, "215153_215176_218272_218934.tar.gz"))

    def test_check_headerfile_and_tsdata_format_tsdata_err(self):
        """Test check header file and TS data format - TS data file error"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            with self.assertRaises(custom_exceptions.DataFormatError):
                fa.check_headerfile_and_tsdata_format(
                    pjoin(DATA_DIR, "improperlyformattedtsdata_header.dat"),
                    pjoin(DATA_DIR, "improperlyformattedtsdata.tar.gz"))

    def test_check_headerfile_and_tsdata_format_tsdata_err2(self):
        """Test check header file and TS data format - TS data file error - 2"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            with self.assertRaises(custom_exceptions.DataFormatError):
                fa.check_headerfile_and_tsdata_format(
                    pjoin(DATA_DIR, "improperlyformattedtsdata2_header.dat"),
                    pjoin(DATA_DIR, "improperlyformattedtsdata2.tar.gz"))
    
    def test_featurize_proc(self):
        """Test featurize process"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            ts_paths, custom_script_path = featurize_setup()
            rdb.table("features").insert({"id": "TEST01", "name": "TEST01"})\
                               .run(conn)
            try:
                fa.featurize_proc(
                    ts_paths=ts_paths,
                    features_to_use=["std_err", "amplitude"],
                    featureset_key="TEST01", is_test=True,
                    custom_script_path=custom_script_path,
                    use_docker=USE_DOCKER)
            finally:
                entry = rdb.table("features").get("TEST01").run(conn)
                rdb.table("features").get("TEST01").delete().run(conn)
            assert(os.path.exists(pjoin(cfg['paths']['features_folder'],
                                        "TEST01_featureset.nc")))
            assert("results_msg" in entry)
            featureset = xr.open_dataset(pjoin(cfg['paths']['features_folder'],
                                                 "TEST01_featureset.nc"))
            assert("std_err" in featureset)
            featurize_teardown()

    def test_build_model_proc(self):
        """Test build model process"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            build_model_setup()
            rdb.table("features").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("models").insert({"id": "test",
                                      "name": "test",
                                      "featureset_name": "test",
                                      "parameters": {}}).run(conn)
            fa.build_model_proc("test", "RandomForestClassifier", {},
                                "test")
            entry = rdb.table("models").get("test").run(conn)
            assert "results_msg" in entry
            assert os.path.exists(pjoin(cfg['paths']['models_folder'],
                                        "test.pkl"))
            model = joblib.load(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            assert hasattr(model, "predict_proba")
            model_and_prediction_teardown()

    def test_prediction_proc(self):
        """Test prediction process"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn

            ts_paths, custom_script_path = prediction_setup()
            rdb.table("predictions").insert({"id": "test"}).run(conn)
            fa.prediction_proc(ts_paths, "test", "test", "test")

            entry = rdb.table("predictions").get("test").run(conn)
            pred_results_dict = entry
            classes = np.array([el[0] for el in
                        pred_results_dict["pred_results_dict"]["dotastro_215153_with_class"]],
                        dtype='U')
            assert all(c in ['class1', 'class2', 'class3'] for c in classes)

            assert all(key in pred_results_dict for key in \
                       ("ts_data_dict", "features_dict"))
            for fpath in [pjoin(cfg['paths']['features_folder'],
                                "test_featureset.nc"),
                          pjoin(cfg['paths']['models_folder'], "test.pkl")]:
                try:
                    os.remove(fpath)
                except Exception as e:
                    print(e)

    @dec.skipif(not USE_DOCKER)
    def test_verify_new_script(self):
        """Test verify new script"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            rv = self.app.post('/verifyNewScript',
                               content_type='multipart/form-data',
                               data={'custom_feat_script_file':
                                     (open(pjoin(APP_DATA_DIR, "testfeature1.py"),
                                           mode='rb'), "testfeature1.py")})
            res_str = str(rv.data)
            assert("The following features have successfully been tested:" in
                   res_str)
            assert("custom_feature_checkbox" in res_str)
            assert("avg_mag" in res_str)

    def test_verify_new_script_nofile(self):
        """Test verify new script - no file"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            rv = self.app.post('/verifyNewScript',
                               content_type='multipart/form-data',
                               data={})
            res_str = str(rv.data)
            assert("No custom features script uploaded. Please try again" in
                   res_str)

    def test_edit_project_form(self):
        """Test edit project form"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "TESTPROJ01",
                                        "name": "TESTPROJ01"}).run(conn)
            rv = self.app.post('/editProjectForm',
                               content_type='multipart/form-data',
                               data={'project_name_orig': 'TESTPROJ01',
                                     'project_name_edit': 'TESTPROJ02',
                                     'project_description_edit': 'new_desc',
                                     'addl_authed_users_edit': ''})
            res_str = str(rv.data)
            entry = rdb.table("projects").get("TESTPROJ01").run(conn)
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            npt.assert_equal(entry["name"], "TESTPROJ02")
            npt.assert_equal(entry["description"], "new_desc")

    def test_edit_project_form_delete_featset(self):
        """Test edit project form - delete single feature set"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test_featureset.nc"),
                 "w").close()
            assert os.path.exists(pjoin(cfg['paths']['features_folder'],
                                        "test_featureset.nc"))
            rv = self.app.post('/editProjectForm',
                               content_type='multipart/form-data',
                               data={'project_name_orig': 'test',
                                     'project_name_edit': 'test4',
                                     'project_description_edit': 'new_desc',
                                     'addl_authed_users_edit': '',
                                     'delete_features_key': 'test'})
            res_str = str(rv.data)
            entry = rdb.table("projects").get("test").run(conn)
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            npt.assert_equal(entry["name"], "test4")
            npt.assert_equal(entry["description"], "new_desc")
            npt.assert_equal(
                rdb.table("features").filter({"id": "test"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test_featureset.nc"))

    def test_edit_project_form_delete_featsets(self):
        """Test edit project form - delete multiple feature sets"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test_featureset.nc"),
                 "w").close()
            rdb.table("features").insert({"id": "test4", "projkey": "test",
                                        "name": "test4", "created": "test4",
                                        "headerfile_path": "HEADPATH4.dat",
                                        "zipfile_path": "ZIPPATH4.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test4_featureset.nc"),
                 "w").close()
            rdb.table("features").insert({"id": "test5", "projkey": "test",
                                        "name": "test5", "created": "test5",
                                        "headerfile_path": "HEADPATH5.dat",
                                        "zipfile_path": "ZIPPATH5.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test5_featureset.nc"),
                 "w").close()
            rv = self.app.post('/editProjectForm',
                               content_type='multipart/form-data',
                               data={'project_name_orig': 'test',
                                     'project_name_edit': 'test4',
                                     'project_description_edit': 'new_desc',
                                     'addl_authed_users_edit': '',
                                     'delete_features_key': ['test',
                                                             'test4',
                                                             'test5']})
            res_str = str(rv.data)
            entry = rdb.table("projects").get("test").run(conn)
            rdb.table("projects").get("test").delete().run(conn)
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            npt.assert_equal(entry["name"], "test4")
            npt.assert_equal(entry["description"], "new_desc")
            npt.assert_equal(
                rdb.table("features").filter({"id": "test"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test_featureset.nc"))
            npt.assert_equal(
                rdb.table("features").filter({"id": "test4"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test4_featureset.nc"))
            npt.assert_equal(
                rdb.table("features").filter({"id": "test5"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test5_featureset.nc"))

    def test_edit_project_form_delete_models(self):
        """Test edit project form - delete multiple models"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "headerfile_path": "HEADPATH.dat",
                                      "zipfile_path": "ZIPPATH.tar.gz",
                                      "featset_key": "test",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "type": "RandomForestClassifier"})\
                             .run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test",
                                        "created": "",
                                        "featlist": ["a", "b"]}).run(conn)
            open(pjoin(cfg['paths']['models_folder'], "test.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            rdb.table("models").insert({"id": "test4", "projkey": "test",
                                      "name": "test4", "created": "test4",
                                      "headerfile_path": "HEADPATH4.dat",
                                      "zipfile_path": "ZIPPATH4.tar.gz",
                                      "featset_key": "test4",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "type": "RandomForestClassifier"})\
                             .run(conn)
            rdb.table("features").insert({"id": "test4", "projkey": "test",
                                        "name": "test4",
                                        "created": "",
                                        "featlist": ["a", "b"]}).run(conn)
            open(pjoin(cfg['paths']['models_folder'], "test4.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test4.pkl"))
            rdb.table("models").insert({"id": "test5", "projkey": "test",
                                      "name": "test5", "created": "test5",
                                      "headerfile_path": "HEADPATH5.dat",
                                      "zipfile_path": "ZIPPATH5.tar.gz",
                                      "featset_key": "test5",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "type": "RandomForestClassifier"})\
                             .run(conn)
            rdb.table("features").insert({"id": "test5", "projkey": "test",
                                        "name": "test5",
                                        "created": "",
                                        "featlist": ["a", "b"]}).run(conn)
            open(pjoin(cfg['paths']['models_folder'], "test5.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test5.pkl"))
            rv = self.app.post('/editProjectForm',
                               content_type='multipart/form-data',
                               data={'project_name_orig': 'test',
                                     'project_name_edit': 'test4',
                                     'project_description_edit': 'new_desc',
                                     'addl_authed_users_edit': '',
                                     'delete_model_key': ['test', 'test4',
                                                          'test5']})
            res_str = str(rv.data)
            rdb.table("features").get_all("test", "test4", "test5")\
                               .delete().run(conn)
            entry = rdb.table("projects").get("test").run(conn)
            rdb.table("projects").get("test").delete().run(conn)
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            npt.assert_equal(entry["name"], "test4")
            npt.assert_equal(entry["description"], "new_desc")
            npt.assert_equal(
                rdb.table("models").filter({"id": "test"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            npt.assert_equal(
                rdb.table("models").filter({"id": "test4"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['models_folder'],
                                            "test4.pkl"))
            npt.assert_equal(
                rdb.table("models").filter({"id": "test5"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg['paths']['models_folder'],
                                            "test5.pkl"))

    def test_edit_project_form_delete_predictions(self):
        """Test edit project form - delete multiple predictions"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test",
                                           "headerfile_path": "HEADPATH.dat",
                                           "zipfile_path": "ZIPPATH.tar.gz",
                                           "featset_key": "test",
                                           "type": "RandomForestClassifier"})\
                                  .run(conn)
            rdb.table("predictions").insert({"id": "test4",
                                           "projkey": "test4",
                                           "name": "test4",
                                           "created": "",
                                           "featlist": ["a", "b"]}).run(conn)
            rv = self.app.post('/editProjectForm',
                               content_type='multipart/form-data',
                               data={'project_name_orig': 'test',
                                     'project_name_edit': 'test4',
                                     'project_description_edit': 'new_desc',
                                     'addl_authed_users_edit': '',
                                     'delete_prediction_key': ['test',
                                                               'test4']})
            res_str = str(rv.data)
            entry = rdb.table("projects").get("test").run(conn)
            rdb.table("projects").get("test").delete().run(conn)
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            npt.assert_equal(entry["name"], "test4")
            npt.assert_equal(entry["description"], "new_desc")
            npt.assert_equal(
                rdb.table("predictions").filter({"id": "test"})\
                .count().run(conn), 0)
            npt.assert_equal(
                rdb.table("predictions").filter({"id": "test4"})\
                .count().run(conn), 0)

    def test_new_project(self):
        """Test new project form submission"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rv = self.app.post('/newProject',
                               content_type='multipart/form-data',
                               data={'new_project_name': 'test',
                                     'project_description': 'desc',
                                     'addl_authed_users': ''})
            res_str = str(rv.data)
            entry = rdb.table("projects").filter({"name": "test"}).run(conn)\
                                                                  .next()
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            assert "successfully created" in res_str
            npt.assert_equal(entry["name"], "test")
            npt.assert_equal(entry["description"], "desc")

    def test_new_project_url(self):
        """Test new project form submission - url"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rv = self.app.get('/newProject/test/desc/None/%s' % TEST_EMAIL)
            res_str = str(rv.data)
            entry = rdb.table("projects").filter({"name": "test"}).run(conn)\
                                                                  .next()
            for e in rdb.table("userauth").filter({"userkey": TEST_EMAIL})\
                                        .run(conn):
                rdb.table("userauth").get(e['id']).delete().run(conn)
            assert "successfully created" in res_str
            npt.assert_equal(entry["name"], "test")
            npt.assert_equal(entry["description"], "desc")

    def test_edit_or_delete_project_form_edit(self):
        """Test edit or delete project form - edit"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rv = self.app.post("/editOrDeleteProject",
                               content_type='multipart/form-data',
                               data={"PROJECT_NAME_TO_EDIT": "test",
                                     'action': 'Edit'})
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict["name"], "test")
            assert("featuresets" in res_dict)
            assert("authed_users" in res_dict)

    def test_edit_or_delete_project_form_delete(self):
        """Test edit or delete project form - delete"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "test", "created": "test",
                                      "featset_key": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("predictions").insert({"id": "test", "projkey": "test",
                                           "name": "test",
                                           "created": "test",
                                           "headerfile_path": "HEADPATH.dat",
                                           "zipfile_path": "ZIPPATH.tar.gz",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg['paths']['features_folder'], "test_featureset.nc"),
                 "w").close()
            assert os.path.exists(pjoin(cfg['paths']['features_folder'],
                                        "test_featureset.nc"))
            open(pjoin(cfg['paths']['models_folder'], "test.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg['paths']['models_folder'], "test.pkl"))
            # Call the method being tested
            rv = self.app.post("/editOrDeleteProject",
                               content_type='multipart/form-data',
                               data={"PROJECT_NAME_TO_EDIT": "test",
                                     'action': 'Delete'})
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict["result"], "Deleted 1 project(s).")
            count = rdb.table("projects").filter({"id": "test"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            count = rdb.table("features").filter({"id": "test"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg['paths']['features_folder'],
                                            "test_featureset.nc"))
            count = rdb.table("models").filter({"id": "test"}).count()\
                                                              .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg['paths']['models_folder'],
                                            "test.pkl"))
            count = rdb.table("predictions").filter({"id": "test"}).count()\
                                                                   .run(conn)
            npt.assert_equal(count, 0)

    def test_edit_or_delete_project_form_invalid(self):
        """Test edit or delete project form - invalid action"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rv = self.app.post("/editOrDeleteProject",
                               content_type='multipart/form-data',
                               data={"PROJECT_NAME_TO_EDIT": "test",
                                     'action': 'Invalid action!'})
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict["error"], "Invalid request action.")

    def test_get_featureset_id_by_projname_and_featsetname(self):
        """Test get feature set id by project name and feature set name"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rv = self.app.get("/get_featureset_id_by_projname_and_featsetname"
                              "/test/test")
            res_id = json.loads(rv.data.decode())["featureset_id"]
            npt.assert_equal(res_id, "test")

    def test_get_list_of_featuresets_by_project(self):
        """Test get list of feature sets by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "test", "projkey": "test",
                                        "name": "test", "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("features").insert({"id": "test_2", "projkey": "test",
                                        "name": "test_2", "created": "abc",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rv = self.app.get("/get_list_of_featuresets_by_project/test")
            featset_list = json.loads(rv.data.decode())["featset_list"]
            npt.assert_array_equal(sorted(featset_list), ["test", "test_2"])

    def test_get_list_of_models_by_project(self):
        """Test get list of models by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("models").insert({"id": "test", "projkey": "test",
                                      "name": "model_1", "created": "test",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "featset1",
                                      "parameters": {},
                                      "zipfile_path": "ZIPPATH.tar.gz",
                                      "featlist": ["a", "b", "c"]}).run(conn)
            rdb.table("models").insert({"id": "test_2", "projkey": "test",
                                      "name": "model_2", "created": "abc",
                                      "type": "RandomForestClassifier",
                                      "featureset_name": "featset1",
                                      "parameters": {},
                                      "zipfile_path": "ZIPPATH.tar.gz",
                                      "featlist": ["a", "b", "c"]}).run(conn)
            rv = self.app.get("/get_list_of_models_by_project/test")
            model_list = [e.split(" (created")[0] for e in
                          json.loads(rv.data.decode())["model_list"]]
            npt.assert_array_equal(
                sorted(model_list),
                ["model_1 - RandomForestClassifier (featset1)",
                 "model_2 - RandomForestClassifier (featset1)"])

    def test_upload_features_form(self):
        """Test upload features form"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            featurize_setup()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rv = self.app.post('/uploadFeaturesForm',
                               content_type='multipart/form-data',
                               data={'features_file':
                                     (open(pjoin(
                                         DATA_DIR,
                                         "test_features_with_targets.csv"),
                                         mode='rb'),
                                      "test_features_with_targets.csv"),
                                     'featuresetname': 'test',
                                     'featureset_projname_select': 'test'})
            new_key = list(rdb.table('features').filter({'name':
                          'test'}).pluck('id').run(conn))[0]['id']
            featureset = xr.open_dataset(pjoin(cfg['paths']['features_folder'],
                                                 "%s_featureset.nc" % new_key))
            assert(all(c in ['class1', 'class2', 'class3'] for
                       c in featureset.target.values.astype('U')))
            npt.assert_array_equal(sorted(featureset.data_vars),
                                   ["amplitude", "meta1", "meta2", "meta3",
                                     "std_err"])
            featurize_teardown()

    def test_transform_data_form(self):
        """Test transform data form"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            featurize_setup()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rv = self.app.post('/transformData',
                               content_type='multipart/form-data',
                               data={'transform_data_dataset_select': 'ds1',
                                     'transform_data_project_name_select': 'test',
                                     'transform_data_transform_select': 'Train/Test Split'})
            all_ts_files = []
            for label in ["train", "test"]:
                ts_files = list(rdb.table('datasets').filter({'name': 'Test dataset '
                    '({})'.format(label)}).pluck('ts_filenames').run(conn))[0]['ts_filenames']
                all_ts_files.extend(ts_files)
            assert len(all_ts_files) == len(TS_FILES)
                

    @dec.skipif(not USE_DOCKER)
    def test_featurize_data(self):
        """Test main upload data to featurize"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            ts_paths, custom_script_path = featurize_setup()
            rv = self.app.post('/FeaturizeData',
                               content_type='multipart/form-data',
                               data={'featureset_dataset_select': 'ds1',
                                     'featureset_name': 'test',
                                     'featureset_project_name_select': 'test',
                                     'features_selected': ['std_err', 'amplitude'],
                                     'custom_script_tested': 'yes',
                                     'custom_feat_script_file':
                                     (open(custom_script_path,
                                           mode='rb'),
                                      "testfeature1.py"),
                                     'custom_feature_checkbox': ['f'],
                                     'is_test': 'True'})
            res_dict = json.loads(rv.data.decode())
            assert "PID" in res_dict
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            time.sleep(1)
            new_key = res_dict['featureset_key']
            npt.assert_equal(res_dict["featureset_name"], "test")
            featureset = xr.open_dataset(pjoin(cfg['paths']['features_folder'],
                                                 "%s_featureset.nc" % new_key))
            assert(all(c in ['class1', 'class2', 'class3']
                       for c in featureset.target.values.astype('U')))
            cols = list(featureset.data_vars)
            npt.assert_array_equal(sorted(cols), ["amplitude", "f", "meta1",
                                                  "meta2", "meta3", "std_err"])
            fpaths = []
            for fpath in [
                    pjoin(cfg['paths']['features_folder'], "%s_featureset.nc" % new_key),
                    pjoin(cfg['paths']['features_folder'],
                          "%s_features_with_targets.csv" % new_key)]:
                if os.path.exists(fpath):
                    fpaths.append(fpath)
            entry_dict = rdb.table("features").get(new_key).run(conn)
            for key in ("headerfile_path", "zipfile_path",
                        "custom_features_script"):
                if entry_dict and key in entry_dict:
                    if entry_dict[key]:
                        fpaths.append(entry_dict[key])
            for fpath in fpaths:
                if os.path.exists(fpath):
                    os.remove(fpath)
            e = rdb.table('features').get(new_key).run(conn)
            rdb.table("features").get(new_key).delete().run(conn)
            rdb.table("projects").get("test").delete().run(conn)
            count = rdb.table("features").filter({"id": new_key}).count()\
                                                               .run(conn)
            npt.assert_equal(count, 0)
            assert "pid" in e
            assert("New feature set files saved successfully" in
                   res_dict["message"])
            npt.assert_equal(e["name"], "test")
            featurize_teardown()

    def test_featurize_data_no_custom(self):
        """Test main upload data to featurize (no custom feature script)"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            ts_paths, custom_script_path = featurize_setup()
            rv = self.app.post('/FeaturizeData',
                               content_type='multipart/form-data',
                               data={'featureset_dataset_select': 'ds1',
                                     'featureset_name': 'test',
                                     'featureset_project_name_select': 'test',
                                     'features_selected': ['std_err', 'amplitude'],
                                     'custom_script_tested': 'no',
                                     'is_test': 'True'})
            res_dict = json.loads(rv.data.decode())
            assert "PID" in res_dict
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            time.sleep(1)
            new_key = res_dict['featureset_key']
            npt.assert_equal(res_dict["featureset_name"], "test")
            featureset = xr.open_dataset(pjoin(cfg['paths']['features_folder'],
                                                 "%s_featureset.nc" % new_key))
            assert(all(c in ['class1', 'class2', 'class3']
                       for c in featureset.target.values.astype('U')))
            cols = list(featureset.data_vars)
            npt.assert_array_equal(sorted(cols), ["amplitude", "meta1",
                                                  "meta2", "meta3", "std_err"])
            fpaths = []
            for fpath in [
                    pjoin(cfg['paths']['features_folder'], "%s_featureset.nc" % new_key),
                    pjoin(cfg['paths']['features_folder'],
                          "%s_features_with_targets.csv" % new_key)]:
                if os.path.exists(fpath):
                    fpaths.append(fpath)
            entry_dict = rdb.table("features").get(new_key).run(conn)
            for key in ("headerfile_path", "zipfile_path"):
                if entry_dict and key in entry_dict:
                    if entry_dict[key]:
                        fpaths.append(entry_dict[key])
            for fpath in fpaths:
                if os.path.exists(fpath):
                    os.remove(fpath)
            e = rdb.table('features').get(new_key).run(conn)
            rdb.table("features").get(new_key).delete().run(conn)
            rdb.table("projects").get("test").delete().run(conn)
            count = rdb.table("features").filter({"id": new_key}).count()\
                                                               .run(conn)
            npt.assert_equal(count, 0)
            assert "pid" in e
            assert("New feature set files saved successfully" in
                   res_dict["message"])
            npt.assert_equal(e["name"], "test")
            featurize_teardown()

    @dec.skipif(not USE_DOCKER)
    def test_featurization_page(self):
        """Test main featurization function"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            ts_paths, custom_script_path = featurize_setup()
            rv = fa.featurizationPage(
                featureset_name="test", project_name="test",
                dataset_id="ds1", featlist=["avg_mag", "std_err"],
                is_test=True, email_user=False, already_featurized=False,
                custom_script_path=custom_script_path)
            res_dict = json.loads(rv.data.decode())
            assert "PID" in res_dict
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            new_key = res_dict['featureset_key']
            npt.assert_equal(res_dict["featureset_name"], "test")
            featureset = xr.open_dataset(pjoin(cfg['paths']['features_folder'],
                                                 "%s_featureset.nc" % new_key))
            assert(all(c in ['class1', 'class2']
                       for c in featureset['target'].values.astype('U')))
            npt.assert_array_equal(sorted(list(featureset.data_vars)),
                                   ['avg_mag', 'meta1', 'meta2', 'meta3',
                                    'std_err'])

    def test_featurization_page_already_featurized(self):
        """Test main featurization function - pre-featurized data"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            shutil.copy(pjoin(DATA_DIR, "test_features_with_targets.csv"),
                        cfg['paths']['upload_folder'])
            headerfile_name = "test_features_with_targets.csv"
            ts_paths, custom_script_path = featurize_setup()
            rv = fa.featurizationPage(featureset_name="test", project_name="test",
                dataset_id='ds1', featlist=["std_err", "amplitude"], is_test=True,
                email_user=False, already_featurized=True)
            res_dict = json.loads(rv.data.decode())
            assert "PID" in res_dict
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            new_key = res_dict['featureset_key']
            npt.assert_equal(res_dict["featureset_name"], "test")
            featureset = xr.open_dataset(pjoin(cfg['paths']['features_folder'],
                                                 "%s_featureset.nc" % new_key))
            assert(all(c in ["class1", "class2", "class3"]
                       for c in featureset['target'].values.astype('U')))
            npt.assert_array_equal(sorted(list(featureset.data_vars)),
                                   ['amplitude', 'meta1', 'meta2', 'meta3',
                                    'std_err'])
            assert("New feature set files saved successfully" in
                   res_dict["message"])

    def test_build_model(self):
        """Test main model building function"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            build_model_setup()
            conn = fa.g.rdb_conn
            rdb.table("projects").insert({"id": "test",
                                        "name": "test"}).run(conn)
            rdb.table("features").insert({"id": "asas_training_subset",
                                        "projkey": "test",
                                        "name": "asas_training_subset",
                                        "created": "test",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            rv = fa.buildModel(model_name="NEW_MODEL_NAME",
                               project_name="test",
                               featureset_name="asas_training_subset",
                               model_type="RandomForestClassifier",
                               model_params={},
                               params_to_optimize={"n_estimators":
                                                   [10, 50, 100]})
            res_dict = json.loads(rv.data.decode())
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            new_model_key = res_dict["new_model_key"]
            entry = rdb.table("models").get(new_model_key).run(conn)
            assert "results_msg" in entry
            model = joblib.load(pjoin(cfg['paths']['models_folder'],
                                      "{}.pkl".format(new_model_key)))
            assert hasattr(model, "predict_proba")
            model_and_prediction_teardown()
            rdb.table("models").get(new_model_key).delete().run(conn)

    def test_predict_data(self):
        """Test predict data"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            ts_paths, custom_script_path = prediction_setup()
            rv = self.app.post('/PredictData',
                               content_type='multipart/form-data',
                               data={'prediction_dataset_select': 'ds1',
                                     'prediction_project_name': 'test',
                                     'prediction_model_name_and_type':
                                     'test - RandomForestClassifier'})
            res_dict = json.loads(rv.data.decode())
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            new_key = res_dict["prediction_entry_key"]
            entry = rdb.table('predictions').get(new_key).run(conn)
            model_and_prediction_teardown()
            pred_results = entry["pred_results_dict"]
            feats_dict = entry["features_dict"]
            classes = np.array([el[0] for fname in pred_results
                                for el in pred_results[fname]], dtype='U')
            assert all(c in ['class1', 'class2', 'class3'] for c in classes)
            assert "std_err" in feats_dict["dotastro_215153_with_class"]

    def test_prediction_page(self):
        """Test main prediction function"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            ts_paths, custom_script_path = prediction_setup()
            rv = fa.predictionPage(dataset_id='ds1',
                                   project_name="test",
                                   model_key="test",
                                   model_name="test",
                                   model_type="RandomForestClassifier")
            res_dict = json.loads(rv.data.decode())
            while "currently running" in fa.check_job_status(res_dict["PID"]):
                time.sleep(1)
            time.sleep(1)
            new_key = res_dict["prediction_entry_key"]
            entry = rdb.table('predictions').get(new_key).run(conn)
            model_and_prediction_teardown()
            pred_results = entry["pred_results_dict"]
            feats_dict = entry["features_dict"]
            classes = np.array([el[0] for fname in pred_results
                                for el in pred_results[fname]], dtype='U')
            assert all(c in ['class1', 'class2', 'class3'] for c in classes)
            assert "std_err" in feats_dict["dotastro_215153_with_class"]

    def test_load_source_data(self):
        """Test load source data"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('predictions').insert({'id': 'test',
                                           'pred_results_dict': {'a': 1},
                                           'features_dict': {'a': 1},
                                           'ts_data_dict': {'a': 1}}).run(conn)
            rv = fa.load_source_data('test', 'a')
            res_dict = json.loads(rv.data.decode())
            for k in ["pred_results", "features_dict", "ts_data"]:
                npt.assert_equal(res_dict[k], 1)

    def test_load_source_data_url(self):
        """Test load source data - url"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('predictions').insert({'id': 'test',
                                           'pred_results_dict': {'a': 1},
                                           'features_dict': {'a': 1},
                                           'ts_data_dict': {'a': 1}}).run(conn)
            rv = self.app.get("/load_source_data/test/a")
            res_dict = json.loads(rv.data.decode())
            for k in ["pred_results", "features_dict", "ts_data"]:
                npt.assert_equal(res_dict[k], 1)

    def test_load_prediction_results(self):
        """Test load prediction results"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('predictions').insert({'id': 'test',
                                           'pred_results_dict': {'a': 1},
                                           'features_dict': {'a': 1},
                                           'ts_data_dict': {'a': 1},
                                           "results_str_html": "a"}).run(conn)
            rv = fa.load_prediction_results('test')
            res_dict = json.loads(rv.data.decode())
            npt.assert_array_equal(res_dict, {'id': 'test',
                                              'pred_results_dict': {'a': 1},
                                              'features_dict': {'a': 1},
                                              'ts_data_dict': {'a': 1},
                                              "results_str_html": "a"})

    def test_load_prediction_results_url(self):
        """Test load prediction results - url"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('predictions').insert({'id': 'test',
                                           'pred_results_dict': {'a': 1},
                                           'features_dict': {'a': 1},
                                           'ts_data_dict': {'a': 1},
                                           "results_str_html": "a"}).run(conn)
            rv = self.app.get("/load_prediction_results/test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "results_str_html": "a"})

    def test_load_model_build_results(self):
        """Test load model build results"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('models').insert({'id': 'test',
                                      'pred_results_dict': {'a': 1},
                                      'features_dict': {'a': 1},
                                      'ts_data_dict': {'a': 1},
                                      "results_msg": "results_msg",
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "results_str_html": "a"}).run(conn)
            rv = fa.load_model_build_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "results_msg": "results_msg",
                                        "featureset_name": "test",
                                        "parameters": {},
                                        "results_str_html": "a"})

    def test_load_model_build_results_no_match(self):
        """Test load model build results - no matching entry"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rv = fa.load_model_build_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {"results_msg":
                                        ("No status message could be found for "
                                         "this process.")})

    def test_load_model_build_results_errmsg(self):
        """Test load model build results - error message"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('models').insert({'id': 'test',
                                      'pred_results_dict': {'a': 1},
                                      'features_dict': {'a': 1},
                                      'ts_data_dict': {'a': 1},
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "results_msg": "Error occurred",
                                      "results_str_html": "a"}).run(conn)
            rv = fa.load_model_build_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(
                rdb.table("models").filter({"id": "test"}).count().run(conn),
                0)
            npt.assert_equal(res_dict, {'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "featureset_name": "test",
                                        "parameters": {},
                                        "results_msg": "Error occurred",
                                        "results_str_html": "a"})

    def test_load_model_build_results_url(self):
        """Test load model build results - url"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('models').insert({'id': 'test',
                                      'pred_results_dict': {'a': 1},
                                      'features_dict': {'a': 1},
                                      'ts_data_dict': {'a': 1},
                                      "featureset_name": "test",
                                      "parameters": {},
                                      "results_msg": "results_msg",
                                      "results_str_html": "a"}).run(conn)
            rv = self.app.get("/load_model_build_results/test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "featureset_name": "test",
                                        "parameters": {},
                                        "results_msg": "results_msg",
                                        "results_str_html": "a"})

    def test_load_featurization_results(self):
        """Test load featurization results"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('features').insert({'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "results_msg": "results_msg",
                                        "results_str_html": "a"}).run(conn)
            rv = fa.load_featurization_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "results_msg": "results_msg",
                                        "results_str_html": "a"})

    def test_load_featurization_results_no_status_msg(self):
        """Test load featurization results - no status message"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rdb.table('features').insert({'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        "results_str_html": "a"}).run(conn)
            rv = fa.load_featurization_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {"results_msg":
                                        ("No status message could be found for "
                                         "this process.")})

    def test_load_featurization_results_no_matching_entry(self):
        """Test load featurization results - no matching entry"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            rv = fa.load_featurization_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(res_dict, {"results_msg":
                                        ("No status message could be found for "
                                         "this process.")})

    def test_load_featurization_results_error(self):
        """Test load featurization results - error msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            tmp_files = []
            for i in range(3):
                tmp_files.append(os.path.join("/tmp",
                                              "%s.dat" % str(uuid.uuid4())[:8]))
                open(tmp_files[-1], "w").close()
            rdb.table('features').insert({'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        'headerfile_path': tmp_files[0],
                                        'zipfile_path': tmp_files[1],
                                        'custom_features_script': tmp_files[2],
                                        "results_msg": "Error occurred",
                                        "results_str_html": "a"}).run(conn)
            rv = fa.load_featurization_results("test")
            res_dict = json.loads(rv.data.decode())
            npt.assert_equal(
                rdb.table("features").filter({"id": "test"}).count().run(conn),
                0)
            npt.assert_equal(res_dict, {'id': 'test',
                                        'pred_results_dict': {'a': 1},
                                        'features_dict': {'a': 1},
                                        'ts_data_dict': {'a': 1},
                                        'headerfile_path': tmp_files[0],
                                        'zipfile_path': tmp_files[1],
                                        'custom_features_script': tmp_files[2],
                                        "results_msg": "Error occurred",
                                        "results_str_html": "a"})
            assert(all(not os.path.exists(tmp_file) for tmp_file in tmp_files))
