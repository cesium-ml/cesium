import os
from mltsp import util
from mltsp.ext.sklearn_models import model_descriptions
import numpy.testing as npt
try:
    import docker
    dockerpy_installed = True
except ImportError:
    dockerpy_installed = False


def test_shorten_fname():
    """Test util.shorten_fname"""
    npt.assert_equal(util.shorten_fname("/a/b/c/name.ext"), "name")
    npt.assert_equal(util.shorten_fname("path/to/fname.name2.ext2"),
                     "fname.name2")
    npt.assert_equal(util.shorten_fname("fname.ext"), "fname")
    npt.assert_equal(util.shorten_fname("fname"), "fname")


def test_get_docker_client():
    """Test util.get_docker_client"""
    if not dockerpy_installed:
        npt.assert_raises(RuntimeError, util.get_docker_client)
    else:
        try:
            assert isinstance(util.get_docker_client(), docker.Client)
        except RuntimeError:
            pass


def test_docker_images_available():
    """Test util.docker_images_available"""
    assert isinstance(util.docker_images_available(), bool)


def test_robust_literal_eval_dict():
    """Test util.robust_literal_eval_dict"""
    params = {"n_estimators": "1000",
              "max_features": "auto",
              "min_weight_fraction_leaf": "0.34",
              "bootstrap": "True",
              "class_weight": "{'a': 0.2, 'b': 0.8}"}
    expected = {"n_estimators": 1000,
                "max_features": "auto",
                "min_weight_fraction_leaf": 0.34,
                "bootstrap": True,
                "class_weight": {'a': 0.2, 'b': 0.8}}
    util.robust_literal_eval_dict(params)
    npt.assert_equal(params, expected)

    params = {"max_features": 150}
    expected = {"max_features": 150}
    util.robust_literal_eval_dict(params)
    npt.assert_equal(params, expected)

    params = {"max_features": "150.3"}
    expected = {"max_features": 150.3}
    util.robust_literal_eval_dict(params)
    npt.assert_equal(params, expected)

    params = {"class_weight": "{'a': 0.2, 'b': 0.8}",
              "average": "False"}
    expected = {"class_weight": {'a': 0.2, 'b': 0.8},
                "average": False}
    util.robust_literal_eval_dict(params)
    npt.assert_equal(params, expected)

    params = {"class_weight": "some_str",
              "average": "2"}
    expected = {"class_weight": "some_str",
                "average": 2}
    util.robust_literal_eval_dict(params)
    npt.assert_equal(params, expected)

    params = {"alphas": "[0.1, 2.1, 6.2]"}
    expected = {"alphas": [0.1, 2.1, 6.2]}
    util.robust_literal_eval_dict(params)
    npt.assert_equal(params, expected)

    # Test parameter grid for optimization input
    params_to_optimize = {"max_features": "[150.3, 20, 'auto']"}
    expected = {"max_features": [150.3, 20, "auto"]}
    util.robust_literal_eval_dict(params_to_optimize)
    npt.assert_equal(params_to_optimize, expected)


def test_check_model_param_types():
    """Test util.check_model_param_types"""
    model_type = "RandomForestClassifier"
    params = {"n_estimators": 1000,
                "max_features": "auto",
                "min_weight_fraction_leaf": 0.34,
                "bootstrap": True,
                "class_weight": {'a': 0.2, 'b': 0.8}}
    util.check_model_param_types(model_type, params)

    model_type = "RandomForestClassifier"
    params = {"max_features": 150}
    util.check_model_param_types(model_type, params)

    model_type = "RandomForestClassifier"
    params = {"max_features": 150.3}
    util.check_model_param_types(model_type, params)

    model_type = "LinearSGDClassifier"
    params = {"class_weight": {'a': 0.2, 'b': 0.8},
                "average": False}
    util.check_model_param_types(model_type, params)

    model_type = "LinearSGDClassifier"
    params = {"class_weight": "some_str",
                "average": 2}
    util.check_model_param_types(model_type, params)

    model_type = "RidgeClassifierCV"
    params = {"alphas": [0.1, 2.1, 6.2]}
    util.check_model_param_types(model_type, params)

    # Test parameter grid for optimization input
    model_type = "RandomForestClassifier"
    params_to_optimize = {"max_features": [150.3, 20, "auto"]}
    util.check_model_param_types(model_type, params_to_optimize,
                                        all_as_lists=True)


def test_make_list():
    """Test util.make_list"""
    npt.assert_equal(util.make_list(1), [1])
    npt.assert_equal(util.make_list([1]), [1])


def test_remove_files():
    """Test util.remove_files"""
    # Pass in single path (non-list)
    fpath = "/tmp/mltsp.temp.test"
    f = open(fpath, "w").close()
    assert os.path.exists(fpath)
    util.remove_files(fpath)
    assert not os.path.exists(fpath)

    # Pass in list of paths
    f = open(fpath, "w").close()
    assert os.path.exists(fpath)
    util.remove_files([fpath])
    assert not os.path.exists(fpath)

    # File does not exist, should not raise exception
    util.remove_files(fpath)

