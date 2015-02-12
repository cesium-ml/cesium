from mltsp.Flask import flask_app as fa
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
import shutil
import ntpath

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
    npt.assert_equal(fa.is_running(999999), "False")
    assert(fa.is_running(1) != "False")


def test_db_init():
    """Test RethinkDB init"""
