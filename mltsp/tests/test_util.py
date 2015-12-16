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


def test_cast_model_params():
    """Test util.cast_model_params"""
    model_type = "Random Forest Classifier"
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
    util.cast_model_params(model_type, params)
    npt.assert_equal(params, expected)

    model_type = "Random Forest Classifier"
    params = {"max_features": 150}
    expected = {"max_features": 150}
    util.cast_model_params(model_type, params)
    npt.assert_equal(params, expected)

    model_type = "Random Forest Classifier"
    params = {"max_features": "150.3"}
    expected = {"max_features": 150.3}
    util.cast_model_params(model_type, params)
    npt.assert_equal(params, expected)

    model_type = "Linear SGD Classifier"
    params = {"class_weight": "{'a': 0.2, 'b': 0.8}",
              "average": "False"}
    expected = {"class_weight": {'a': 0.2, 'b': 0.8},
                "average": False}
    util.cast_model_params(model_type, params)
    npt.assert_equal(params, expected)

    model_type = "Linear SGD Classifier"
    params = {"class_weight": "some_str",
              "average": "2"}
    expected = {"class_weight": "some_str",
                "average": 2}
    util.cast_model_params(model_type, params)
    npt.assert_equal(params, expected)

    model_type = "Ridge Classifier CV"
    params = {"alphas": "[0.1, 2.1, 6.2]"}
    expected = {"alphas": [0.1, 2.1, 6.2]}
    util.cast_model_params(model_type, params)
    npt.assert_equal(params, expected)

    npt.assert_raises(ValueError, util.cast_model_params, "wrong_name", {})


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

