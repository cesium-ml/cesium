from mltsp import run_in_docker_container as ridc
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
import shutil


def test_featurize_in_docker_container():
    """Test main featurize in docker container function"""
