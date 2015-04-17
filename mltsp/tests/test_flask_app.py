import os
os.environ["flask_testing"] = "True"
from mltsp.Flask import flask_app as fa
from mltsp import cfg
import numpy.testing as npt
import pandas as pd
import shutil
import ntpath
import uuid
import rethinkdb as r
from flask.ext.stormpath import User, user
from flask.ext.stormpath.context_processors import user_context_processor
import unittest
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_EMAIL = "testhandle@test.com"
TEST_PASSWORD = "TestPass15"

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        fa.app.testing = True
        fa.app.config['DEBUG'] = True
        fa.app.config['WTF_CSRF_ENABLED'] = False
        self.app = fa.app.test_client()
        self.login()

    def login(self, username=TEST_EMAIL, password=TEST_PASSWORD, app=None):
        if app is None:
            app = self.app
        return app.post('/login', data=dict(
            login=username,
            password=password
        ), follow_redirects=True)

    def test_num_lines(self):
        """Test line counting"""
        num_lines = fa.num_lines(os.path.join(DATA_DIR, "dotastro_215153.dat"))
        npt.assert_equal(num_lines, 170)

    def test_check_job_status(self):
        """Test check job status"""
        rv = self.app.post('/check_job_status/?PID=999999')
        print(rv.data)
        assert 'finished' in rv.data
        rv = self.app.post('/check_job_status/?PID=1')
        assert 'currently running' in rv.data

    def test_is_running(self):
        """Test is_running()"""
        npt.assert_equal(fa.is_running(99999), "False") # Greater than max PID
        assert(fa.is_running(1) != "False") # The init process

    def test_db_init(self):
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

    def test_add_user(self):
        """Test add user"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            fa.add_user()
            N = r.table("users").filter({"email": TEST_EMAIL})\
                                .count().run(fa.g.rdb_conn)
            npt.assert_equal(N, 1)
            r.table('users').get(TEST_EMAIL).delete().run(fa.g.rdb_conn)
            N = r.table("users").filter({"email": TEST_EMAIL})\
                                .count().run(fa.g.rdb_conn)
            npt.assert_equal(N, 0)

    def test_check_user_table(self):
        """Test check user table"""
        with fa.app.test_request_context() as trq:
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            N = r.table('users').filter({'email': TEST_EMAIL}).count().run(conn)
            if N > 0:
                r.table("users").get(TEST_EMAIL).delete().run(conn)
                N = r.table('users').filter({'email': TEST_EMAIL}).count()\
                                                                  .run(conn)
                npt.assert_equal(N, 0)

            fa.check_user_table()
            N = r.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 1)
            r.table("users").get(TEST_EMAIL).delete().run(conn)
            r.table("users").insert({"id": TEST_EMAIL,
                                     "email": TEST_EMAIL})\
                            .run(conn)
            N = r.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 1)
            fa.check_user_table()
            N = r.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 1)
            r.table("users").get(TEST_EMAIL).delete().run(conn)
            N = r.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
            npt.assert_equal(N, 0)

    def test_update_model_entry_with_pid(self):
        """Test update model entry with PID"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            model_key = str(uuid.uuid4())[:10]
            r.table("models").insert({"id": model_key}).run(conn)
            fa.update_model_entry_with_pid(model_key, 9999)
            entry_dict = r.table("models").get(model_key).run(conn)
            npt.assert_equal(entry_dict["pid"], "9999")
            r.table("models").get(model_key).delete().run(conn)
            npt.assert_equal(r.table("models").get(model_key).run(conn), None)

    def test_update_featset_entry_with_pid(self):
        """Test update featset entry with PID"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            feat_key = str(uuid.uuid4())[:10]
            r.table("features").insert({"id": feat_key}).run(conn)
            fa.update_featset_entry_with_pid(feat_key, 9999)
            entry_dict = r.table("features").get(feat_key).run(conn)
            npt.assert_equal(entry_dict["pid"], "9999")
            r.table("features").get(feat_key).delete().run(conn)
            npt.assert_equal(r.table("features").get(feat_key).run(conn), None)

    def test_update_prediction_entry_with_pid(self):
        """Test update prediction entry with PID"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            r.table("predictions").insert({"id": key}).run(conn)
            fa.update_prediction_entry_with_pid(key, 9999)
            entry_dict = r.table("predictions").get(key).run(conn)
            npt.assert_equal(entry_dict["pid"], "9999")
            r.table("predictions").get(key).delete().run(conn)
            npt.assert_equal(r.table("predictions").get(key).run(conn), None)

    def test_update_prediction_entry_with_results(self):
        """Test update prediction entry with results"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
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

    def test_update_prediction_entry_with_results_err(self):
        """Test update prediction entry with results - w/ err msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
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

    def test_update_model_entry_with_results_msg(self):
        """Test update model entry with results msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            r.table("models").insert({"id": key}).run(conn)
            fa.update_model_entry_with_results_msg(key, "MSG")
            entry_dict = r.table("models").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")
            r.table("models").get(key).delete().run(conn)

    def test_update_model_entry_with_results_msg_err(self):
        """Test update model entry with results - w/ err msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            r.table("models").insert({"id": key}).run(conn)
            fa.update_model_entry_with_results_msg(key, "MSG", err="ERR_MSG")
            entry_dict = r.table("models").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")
            npt.assert_equal(entry_dict["err_msg"], "ERR_MSG")
            r.table("models").get(key).delete().run(conn)

    def test_update_featset_entry_with_results_msg(self):
        """Test update featset entry with results msg"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            r.table("features").insert({"id": key}).run(conn)
            fa.update_featset_entry_with_results_msg(key, "MSG")
            entry_dict = r.table("features").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")
            r.table("features").get(key).delete().run(conn)

    def test_update_featset_entry_with_results_msg_err(self):
        """Test update featset entry with results msg - err"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            key = str(uuid.uuid4())[:10]
            r.table("features").insert({"id": key}).run(conn)
            fa.update_featset_entry_with_results_msg(key, "MSG", "ERR_MSG")
            entry_dict = r.table("features").get(key).run(conn)
            npt.assert_equal(entry_dict["results_msg"], "MSG")
            npt.assert_equal(entry_dict["err_msg"], "ERR_MSG")
            r.table("features").get(key).delete().run(conn)

    def test_get_current_userkey(self):
        """Test get current user key"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"id": TEST_EMAIL, "email": TEST_EMAIL})\
                            .run(conn)
            result = fa.get_current_userkey()
            r.table("users").get(TEST_EMAIL).delete().run(conn)
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
                r.table("projects").insert({"id": key}).run(conn)
            all_projkeys = fa.get_all_projkeys()
            assert all(key in all_projkeys for key in keys)
            r.table("projects").get_all(*keys).delete().run(conn)

    def test_get_authed_projkeys(self):
        """Test get authed project keys"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
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

    def test_get_authed_projkeys_not_authed(self):
        """Test get authed project keys - not authorized"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
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

    def test_get_authed_projkeys_inactive(self):
        """Test get authed project keys - inactive"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
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

    def test_list_featuresets(self):
        """Test list featuresets"""

