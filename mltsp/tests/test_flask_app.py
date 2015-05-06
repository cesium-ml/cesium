import os
os.environ["DEBUG_LOGIN"] = "1"
from mltsp.Flask import flask_app as fa
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
import ntpath
import uuid
import rethinkdb as r
import unittest
import json

DATA_DIR = pjoin(os.path.dirname(__file__), "data")
TEST_EMAIL = "testhandle@test.com"
TEST_PASSWORD = "TestPass15"


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        fa.app.testing = True
        fa.app.config['DEBUG'] = True
        fa.app.config['WTF_CSRF_ENABLED'] = False
        self.app = fa.app.test_client()
        self.login()
        self.app.post('/check_user_table')

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
        npt.assert_equal(fa.is_running(99999), "False")  # Greater than max PID
        assert(fa.is_running(1) != "False")  # The init process

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
                npt.assert_equal(r.table(table_name).count().run(connection),
                                 0)
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
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            N = r.table('users').filter({'email': TEST_EMAIL}).count()\
                                                              .run(conn)
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
            ts_data = {"fname": [1, 2, 3]}
            results = {"fname": ['c1', 1.0]}
            fa.update_prediction_entry_with_results(key, html_str,
                                                    features_dict,
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
            ts_data = {"fname": [1, 2, 3]}
            results = {"fname": ['c1', 1.0]}
            fa.update_prediction_entry_with_results(key, html_str,
                                                    features_dict,
                                                    ts_data, results,
                                                    "err_msg")
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
            r.table("userauth").get_all(*keys).delete().run(conn)
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
                r.table("userauth").insert({"projkey": key, "id": key,
                                            "userkey": "testhandle@gmail.com",
                                            "active": "y"}).run(conn)
            authed_projkeys = fa.get_authed_projkeys("testhandle2@gmail.com")
            r.table("userauth").get_all(*keys).delete().run(conn)
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
                r.table("userauth").insert({"projkey": key, "id": key,
                                            "userkey": "testhandle@gmail.com",
                                            "active": "n"}).run(conn)
            authed_projkeys = fa.get_authed_projkeys("testhandle@gmail.com")
            r.table("userauth").get_all(*keys).delete().run(conn)
            npt.assert_equal(len(authed_projkeys), 0)
            assert all(key not in authed_projkeys for key in keys)

    def test_list_featuresets_authed(self):
        """Test list featuresets - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("features").insert({"id": "111", "projkey": "111",
                                        "name": "111", "created": "111",
                                        "featlist": [1, 2]}).run(conn)
            featsets = fa.list_featuresets()
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("features").get("abc123").delete().run(conn)
            r.table("features").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            npt.assert_equal(len(featsets), 1)
            assert "created" in featsets[0] and "abc123" in featsets[0]

    def test_list_featuresets_all(self):
        """Test list featuresets - all featsets and name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("features").insert({"id": "111", "projkey": "111",
                                        "name": "111", "created": "111",
                                        "featlist": [1, 2]}).run(conn)
            featsets = fa.list_featuresets(auth_only=False, name_only=True)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("features").get("abc123").delete().run(conn)
            r.table("features").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            assert len(featsets) > 1
            assert all("created" not in featset for featset in featsets)

    def test_list_featuresets_html(self):
        """Test list featuresets - as HTML and by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("userauth").insert({"projkey": "111", "id": "111",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("features").insert({"id": "111", "projkey": "111",
                                        "name": "111", "created": "111",
                                        "featlist": [1, 2]}).run(conn)
            featsets = fa.list_featuresets(auth_only=True, by_project="abc123",
                                           as_html_table_string=True)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("features").get("abc123").delete().run(conn)
            r.table("features").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            r.table("userauth").get("111").delete().run(conn)
            assert isinstance(featsets, (str, unicode))
            assert "table id" in featsets and "abc123" in featsets

    def test_list_models_authed(self):
        """Test list models - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "type": "RF",
                                      "created": "abc123",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("models").insert({"id": "111", "projkey": "111",
                                      "type": "RF",
                                      "name": "111", "created": "111",
                                      "meta_feats": ["1", "2"]}).run(conn)
            models = fa.list_models()
            npt.assert_equal(len(models), 1)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("models").get("abc123").delete().run(conn)
            r.table("models").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            assert "created" in models[0] and "abc123" in models[0]

    def test_list_models_all(self):
        """Test list models - all models and name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "type": "RF",
                                      "created": "abc123",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("models").insert({"id": "111", "projkey": "111",
                                      "type": "RF",
                                      "name": "111", "created": "111",
                                      "meta_feats": ["1", "2"]}).run(conn)
            results = fa.list_models(auth_only=False, name_only=True)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("models").get("abc123").delete().run(conn)
            r.table("models").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            assert len(results) > 1
            assert all("created" not in result for result in results)

    def test_list_models_html(self):
        """Test list models - as HTML and by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("userauth").insert({"projkey": "111", "id": "111",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "type": "RF",
                                      "created": "abc123",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("models").insert({"id": "111", "projkey": "111",
                                      "type": "RF",
                                      "name": "111", "created": "111",
                                      "meta_feats": ["1", "2"]}).run(conn)
            results = fa.list_models(auth_only=True, by_project="abc123",
                                     as_html_table_string=True)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("models").get("abc123").delete().run(conn)
            r.table("models").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            r.table("userauth").get("111").delete().run(conn)
            assert isinstance(results, (str, unicode))
            assert "table id" in results and "abc123" in results

    def test_list_preds_authed(self):
        """Test list predictions - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "model_type": "RF",
                                           "model_name": "MODEL_NAME",
                                           "created": "abc123",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                                  .run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("predictions").insert({"id": "111", "projkey": "111",
                                           "name": "111", "model_type": "RF",
                                           "model_name": "MODEL_NAME",
                                           "created": "111",
                                           "filename": "111.txt",
                                           "results_str_html": "111HTML"})\
                                  .run(conn)
            results = fa.list_predictions(auth_only=True)
            print(results)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("predictions").get("abc123").delete().run(conn)
            r.table("predictions").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            npt.assert_equal(len(results), 1)
            assert "MODEL_NAME" in results[0]

    def test_list_predictions_all(self):
        """Test list predictions - all predictions, name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "model_type": "RF",
                                           "model_name": "MODEL_NAME",
                                           "created": "abc123",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                                  .run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("predictions").insert({"id": "111", "projkey": "111",
                                           "name": "111", "model_type": "RF",
                                           "model_name": "MODEL_NAME",
                                           "created": "111",
                                           "filename": "111.txt",
                                           "results_str_html": "111HTML"})\
                                  .run(conn)
            results = fa.list_predictions(auth_only=False, detailed=False)
            print(results)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("predictions").get("abc123").delete().run(conn)
            r.table("predictions").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            assert len(results) > 1
            assert all("created" not in result for result in results)

    def test_list_predictions_html(self):
        """Test list predictions - as HTML and by project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("users").insert({"email": TEST_EMAIL, "id": TEST_EMAIL})\
                            .run(conn)
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("userauth").insert({"projkey": "111", "id": "111",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "model_type": "RF",
                                           "model_name": "MODEL_NAME",
                                           "created": "abc123",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                                  .run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            r.table("predictions").insert({"id": "111", "projkey": "111",
                                           "name": "111", "model_type": "RF",
                                           "model_name": "MODEL_NAME",
                                           "created": "111",
                                           "filename": "111.txt",
                                           "results_str_html": "111HTML"})\
                                  .run(conn)
            results = fa.list_predictions(by_project="abc123",
                                          as_html_table_string=True)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("predictions").get("abc123").delete().run(conn)
            r.table("predictions").get("111").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            r.table("userauth").get("111").delete().run(conn)
            assert isinstance(results, (str, unicode))
            assert "table id" in results and "abc123" in results

    def test_get_list_of_projects(self):
        """Test get list of projects"""
        conn = fa.rdb_conn
        r.table("projects").insert({"id": "abc123",
                                    "name": "abc123"}).run(conn)
        r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                    "userkey": TEST_EMAIL,
                                    "email": TEST_EMAIL,
                                    "active": "y"}).run(conn)
        rv = self.app.get('/get_list_of_projects')
        r.table("projects").get("abc123").delete().run(conn)
        r.table("userauth").get("abc123").delete().run(conn)
        print(rv.data)
        assert '{' in rv.data
        assert isinstance(eval(rv.data), dict)
        assert "abc123" in eval(rv.data)["list"]

    def test_list_projects_authed(self):
        """Test list projects - authed only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            results = fa.list_projects()
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            npt.assert_equal(len(results), 1)
            assert "abc123" in results[0]

    def test_list_projects_all(self):
        """Test list projects - all and name only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("userauth").insert({"projkey": "abc123", "id": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "email": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("projects").insert({"id": "111",
                                        "name": "111"}).run(conn)
            results = fa.list_projects(auth_only=False, name_only=True)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("projects").get("111").delete().run(conn)
            assert len(results) >= 2
            assert all("created" not in res for res in results)

    def test_add_project(self):
        """Test add project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_projkey = fa.add_project(name="TEST")
            entry = r.table("projects").get(new_projkey).run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['description'], "")
            cur = r.table("userauth").filter({"projkey": new_projkey})\
                                     .run(conn)
            auth_entries = []
            for e in cur:
                auth_entries.append(e)
            r.table("projects").get(new_projkey).delete().run(conn)
            r.table("userauth").get(auth_entries[0]["id"]).delete().run(conn)
            npt.assert_equal(len(auth_entries), 1)
            npt.assert_equal(auth_entries[0]["active"], "y")

    def test_add_project_addl_users(self):
        """Test add project - addl users"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_projkey = fa.add_project(name="TEST",
                                         addl_authed_users=["1@2.com"])
            entry = r.table("projects").get(new_projkey).run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['description'], "")
            cur = r.table("userauth").filter({"projkey": new_projkey})\
                                     .run(conn)
            auth_entries = []
            for e in cur:
                auth_entries.append(e)
            r.table("projects").get(new_projkey).delete().run(conn)
            r.table("userauth").get(auth_entries[0]["id"]).delete().run(conn)
            r.table("userauth").get(auth_entries[1]["id"]).delete().run(conn)
            npt.assert_equal(len(auth_entries), 2)
            npt.assert_equal(auth_entries[0]["active"], "y")

    def test_add_featureset(self):
        """Test add feature set"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_featset_key = fa.add_featureset(name="TEST", projkey="abc",
                                                pid="2", featlist=['f1', 'f2'])
            entry = r.table("features").get(new_featset_key).run(conn)
            r.table("features").get(new_featset_key).delete().run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['featlist'], ['f1', 'f2'])

    def test_add_model(self):
        """Test add model"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            new_key = fa.add_model(featureset_name="TEST",
                                   featureset_key="123",
                                   model_type="RF", projkey="ABC", pid="2")
            entry = r.table("models").get(new_key).run(conn)
            r.table("models").get(new_key).delete().run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['projkey'], "ABC")

    def test_add_model_meta_feats(self):
        """Test add model - with meta features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("features").insert({"id": "123",
                                        "meta_feats": ['f1', 'f2']}).run(conn)
            new_key = fa.add_model(featureset_name="TEST",
                                   featureset_key="123",
                                   model_type="RF", projkey="ABC", pid="2")
            entry = r.table("models").get(new_key).run(conn)
            r.table("models").get(new_key).delete().run(conn)
            r.table("features").get("123").delete().run(conn)
            npt.assert_equal(entry['name'], "TEST")
            npt.assert_equal(entry['projkey'], "ABC")
            npt.assert_equal(entry['meta_feats'], ['f1', 'f2'])

    def test_add_prediction(self):
        """Test add prediction entry"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            new_key = fa.add_prediction(project_name="abc123",
                                        model_name="model_name",
                                        model_type="RF",
                                        pred_filename="test.dat",
                                        pid="2")
            entry = r.table("predictions").get(new_key).run(conn)
            r.table("predictions").get(new_key).delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            npt.assert_equal(entry['project_name'], "abc123")
            npt.assert_equal(entry['metadata_file'], "None")

    def test_get_projects_associated_files(self):
        """Test get project's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.project_associated_files("abc123")
            npt.assert_equal(fpaths, [])
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "type": "RF",
                                      "created": "abc123",
                                      "featset_key": "abc123",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "model_type": "RF",
                                           "model_name": "abc123",
                                           "created": "abc123",
                                           "filename": "abc.txt",
                                           "results_str_html": "abcHTML"})\
                                  .run(conn)
            fpaths = fa.project_associated_files("abc123")
            r.table("features").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("models").get("abc123").delete().run(conn)
            r.table("predictions").get("abc123").delete().run(conn)
            short_fnames = [ntpath.basename(fpath) for fpath in fpaths]
            assert all(fname in short_fnames for fname in
                       ["abc123_RF.pkl"])

    def test_get_models_associated_files(self):
        """Test get model's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.model_associated_files("abc123")
            npt.assert_equal(fpaths, [])
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "type": "RF",
                                      "created": "abc123",
                                      "featset_key": "abc123",
                                      "meta_feats": ["a", "b", "c"]}).run(conn)
            fpaths = fa.model_associated_files("abc123")
            r.table("models").get("abc123").delete().run(conn)
            short_fnames = [ntpath.basename(fpath) for fpath in fpaths]
            assert all(fname in short_fnames for fname in
                       ["abc123_RF.pkl"])

    def test_get_featsets_associated_files(self):
        """Test get feature set's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.featset_associated_files("abc123")
            npt.assert_equal(fpaths, [])
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            fpaths = fa.featset_associated_files("abc123")
            r.table("features").get("abc123").delete().run(conn)
            short_fnames = [ntpath.basename(fpath) for fpath in fpaths]
            print(short_fnames)
            assert all(fname in short_fnames for fname in
                       ["ZIPPATH.tar.gz", "HEADPATH.dat"])

    def test_get_prediction_associated_files(self):
        """ ## TO-DO ## Test get prediction's associated files"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            fpaths = fa.prediction_associated_files("abc123")

    def test_delete_associated_project_data_features(self):
        """Test delete associated project data - features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg.FEATURES_FOLDER, "abc123_features.csv"),
                 "w").close()
            assert os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                        "abc123_features.csv"))
            fa.delete_associated_project_data("features", "abc123")
            count = r.table("features").filter({"id": "abc123"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                            "abc123_features.csv"))

    def test_delete_associated_project_data_models(self):
        """Test delete associated project data - models"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "created": "abc123",
                                      "featset_key": "abc123",
                                      "type": "RF",
                                      "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"))
            fa.delete_associated_project_data("models", "abc123")
            count = r.table("models").filter({"id": "abc123"}).count()\
                                                              .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                            "abc123_RF.pkl"))

    def test_delete_associated_project_data_predictions(self):
        """Test delete associated project data - predictions"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "created": "abc123",
                                           "headerfile_path": "HEADPATH.dat",
                                           "zipfile_path": "ZIPPATH.tar.gz",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            fa.delete_associated_project_data("predictions", "abc123")
            count = r.table("predictions").filter({"id": "abc123"}).count()\
                                                                   .run(conn)
            npt.assert_equal(count, 0)

    def test_delete_project(self):
        """Test delete project"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "created": "abc123",
                                      "featset_key": "abc123",
                                      "type": "RF",
                                      "featlist": ["a", "b", "c"]}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "created": "abc123",
                                           "headerfile_path": "HEADPATH.dat",
                                           "zipfile_path": "ZIPPATH.tar.gz",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg.FEATURES_FOLDER, "abc123_features.csv"),
                 "w").close()
            assert os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                        "abc123_features.csv"))
            open(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"))
            # Call the method being tested
            fa.delete_project("abc123")
            count = r.table("projects").filter({"id": "abc123"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            count = r.table("features").filter({"id": "abc123"}).count()\
                                                                .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                            "abc123_features.csv"))
            count = r.table("models").filter({"id": "abc123"}).count()\
                                                              .run(conn)
            npt.assert_equal(count, 0)
            assert not os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                            "abc123_RF.pkl"))
            count = r.table("predictions").filter({"id": "abc123"}).count()\
                                                                   .run(conn)
            npt.assert_equal(count, 0)

    def test_get_project_details(self):
        """Test get project details"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("userauth").insert({"id": "abc123",
                                        "projkey": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("userauth").insert({"id": "abc123_2",
                                        "projkey": "abc123",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "created": "abc123",
                                      "featset_key": "abc123",
                                      "type": "RF",
                                      "featlist": ["a", "b", "c"]}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "created": "abc123",
                                           "model_name": "abc123",
                                           "model_type": "RF",
                                           "filename": "FNAME.dat",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            proj_info = fa.get_project_details("abc123")
            r.table("features").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("models").get("abc123").delete().run(conn)
            r.table("predictions").get("abc123").delete().run(conn)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("userauth").get("abc123_2").delete().run(conn)
            print(proj_info)
            assert all(email in proj_info["authed_users"] for email in
                       [TEST_EMAIL, "abc@123.com"])
            assert "<table" in proj_info["featuresets"] and "abc123" in \
                proj_info["featuresets"]
            assert "<table" in proj_info["models"] and "abc123" in \
                proj_info["models"]
            assert all(x in proj_info["predictions"] for x in
                       ["<table", "RF", "abc123", "FNAME.dat"])

    def test_get_project_details_json(self):
        """Test get projects details as JSON"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("userauth").insert({"id": "abc123",
                                        "projkey": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("userauth").insert({"id": "abc123_2",
                                        "projkey": "abc123",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "created": "abc123",
                                      "featset_key": "abc123",
                                      "type": "RF",
                                      "featlist": ["a", "b", "c"]}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "created": "abc123",
                                           "model_name": "abc123",
                                           "model_type": "RF",
                                           "filename": "FNAME.dat",
                                           "featlist":
                                           ["a", "b", "c"]}).run(conn)
            rv = self.app.post("/get_project_details/abc123")
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("features").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            r.table("models").get("abc123").delete().run(conn)
            r.table("predictions").get("abc123").delete().run(conn)
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("userauth").get("abc123_2").delete().run(conn)
        res_dict = json.loads(rv.data)
        npt.assert_equal(res_dict['name'], "abc123")
        npt.assert_array_equal(sorted(res_dict["authed_users"]),
                               ['abc@123.com', 'testhandle@test.com'])
        assert "FNAME.dat" in res_dict["predictions"]
        assert "abc123" in res_dict["models"]

    def test_get_authed_users(self):
        """Test get authed users"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("userauth").insert({"id": "abc123",
                                        "projkey": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("userauth").insert({"id": "abc123_2",
                                        "projkey": "abc123",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            authed_users = fa.get_authed_users("abc123")
            r.table("userauth").get("abc123").delete().run(conn)
            r.table("userauth").get("abc123_2").delete().run(conn)
            npt.assert_array_equal(sorted(authed_users),
                                   sorted([TEST_EMAIL, "abc@123.com"] +
                                          fa.sys_admin_emails))

    def test_project_name_to_key(self):
        """Test project name to key"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123_name"}).run(conn)
            key = fa.project_name_to_key("abc123_name")
            r.table("projects").get("abc123").delete().run(conn)
            npt.assert_equal(key, "abc123")

    def test_featureset_name_to_key(self):
        """Test featureset name to key"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("features").insert({"id": "abc123",
                                        "name": "abc123_name",
                                        "projkey": "abc123"}).run(conn)
            key = fa.featureset_name_to_key("abc123_name",
                                            project_id="abc123")
            r.table("features").get("abc123").delete().run(conn)
            npt.assert_equal(key, "abc123")

    def test_featureset_name_to_key_projname(self):
        """Test featureset name to key - with project name"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("features").insert({"id": "abc123",
                                        "name": "abc123_name",
                                        "projkey": "abc123"}).run(conn)
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123_name"}).run(conn)
            key = fa.featureset_name_to_key("abc123_name",
                                            project_name="abc123_name")
            r.table("features").get("abc123").delete().run(conn)
            r.table("projects").get("abc123").delete().run(conn)
            npt.assert_equal(key, "abc123")

    def test_update_project_info(self):
        """Test update project info"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("userauth").insert({"id": "abc123",
                                        "projkey": "abc123",
                                        "userkey": TEST_EMAIL,
                                        "active": "y"}).run(conn)
            r.table("userauth").insert({"id": "abc123_2",
                                        "projkey": "abc123",
                                        "userkey": "abc@123.com",
                                        "active": "y"}).run(conn)
            fa.update_project_info("abc123", "new_name", "DESC!", [])
            proj_dets = fa.get_project_details("new_name")
            r.table("projects").get("abc123").delete().run(conn)
            r.table("userauth").get("abc123").delete().run(conn)
            npt.assert_equal(
                r.table("userauth").filter({"id": "abc123_2"}).count().run(conn),
                0)
            npt.assert_equal(proj_dets["description"], "DESC!")

    def test_update_project_info_delete_features(self):
        """Test update project info - delete features"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg.FEATURES_FOLDER, "abc123_features.csv"),
                 "w").close()
            open(pjoin(cfg.FEATURES_FOLDER, "abc123_classes.npy"), "w").close()
            assert os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                        "abc123_features.csv"))
            fa.update_project_info("abc123", "abc123", "", [],
                                   delete_features_keys=["abc123"])
            r.table("projects").get("abc123").delete().run(conn)
            npt.assert_equal(
                r.table("features").filter({"id": "abc123"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                            "abc123_features.csv"))
            assert not os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                            "abc123_classes.npy"))

    def test_update_project_info_delete_models(self):
        """Test update project info - delete models"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("models").insert({"id": "abc123", "projkey": "abc123",
                                      "name": "abc123", "created": "abc123",
                                      "type": "RF",
                                      "featset_key": "abc123"}).run(conn)
            r.table("features").insert({"id": "abc123", "projkey": "abc123",
                                        "name": "abc123", "created": "abc123",
                                        "headerfile_path": "HEADPATH.dat",
                                        "zipfile_path": "ZIPPATH.tar.gz",
                                        "featlist": ["a", "b", "c"]}).run(conn)
            open(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"), "w").close()
            assert os.path.exists(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"))
            fa.update_project_info("abc123", "abc123", "", [],
                                   delete_model_keys=["abc123"])
            r.table("projects").get("abc123").delete().run(conn)
            r.table("features").get("abc123").delete().run(conn)
            npt.assert_equal(
                r.table("models").filter({"id": "abc123"}).count().run(conn),
                0)
            assert not os.path.exists(pjoin(cfg.MODELS_FOLDER, "abc123_RF.pkl"))

    def test_update_project_info_delete_predictions(self):
        """Test update project info - delete predictions"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            r.table("projects").insert({"id": "abc123",
                                        "name": "abc123"}).run(conn)
            r.table("predictions").insert({"id": "abc123", "projkey": "abc123",
                                           "name": "abc123",
                                           "created": "abc123"}).run(conn)
            fa.update_project_info("abc123", "abc123", "", [],
                                   delete_prediction_keys=["abc123"])
            r.table("projects").get("abc123").delete().run(conn)
            npt.assert_equal(
                r.table("predictions").filter({"id": "abc123"}).count().run(conn),
                0)

    def test_get_all_info_dict(self):
        """Test get all info dict - auth only"""
        with fa.app.test_request_context():
            fa.app.preprocess_request()
            conn = fa.g.rdb_conn
            d = fa.get_all_info_dict()
            print(d)
