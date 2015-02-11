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
