from mltsp import build_model
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
from subprocess import call


def test_csv_parser():
    """Test CSV file parsing."""
    colnames, data_rows = build_model.read_data_from_csv_file(
        os.path.join(os.path.dirname(__file__), "Data/csv_test_data.csv"))
    npt.assert_equal(colnames[0], "col1")
    npt.assert_equal(colnames[-1], "col4")
    npt.assert_equal(len(data_rows[0]), 4)
    npt.assert_equal(len(data_rows[-1]), 4)
    npt.assert_equal(data_rows[0][-1], "4")
