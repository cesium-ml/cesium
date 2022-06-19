import os
from cesium import util
import numpy.testing as npt


def test_shorten_fname():
    """Test util.shorten_fname"""
    npt.assert_equal(util.shorten_fname("/a/b/c/name.ext"), "name")
    npt.assert_equal(util.shorten_fname("path/to/fname.name2.ext2"), "fname.name2")
    npt.assert_equal(util.shorten_fname("fname.ext"), "fname")
    npt.assert_equal(util.shorten_fname("fname"), "fname")


def test_remove_files(tmpdir):
    """Test util.remove_files"""
    # Pass in single path (non-list)
    fpath = os.path.join(str(tmpdir), "cesium.test")
    open(fpath, "w").close()
    assert os.path.exists(fpath)
    util.remove_files(fpath)
    assert not os.path.exists(fpath)

    # Pass in list of paths
    open(fpath, "w").close()
    assert os.path.exists(fpath)
    util.remove_files([fpath])
    assert not os.path.exists(fpath)

    # File does not exist, should not raise exception
    util.remove_files(fpath)
