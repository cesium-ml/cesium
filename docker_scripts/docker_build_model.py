from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import *
# docker_build_model.py

# to be run from INSIDE a docker container

import subprocess
import sys
import os
from .. import build_rf_model

from subprocess import Popen, PIPE, call
import pickle


def build_model():
    """Load pickled parameters and call `build_rf_model.build_model`.
    
    To be called from inside a Docker container. Pickles model which 
    will later be copied to host machine.
    
    Returns
    -------
    str
        Human readable message indicating successful completion.
    
    """
    # load pickled ts_data and known features
    with open("/home/mltsp/mltsp/copied_data_files/function_args.pkl","rb") as f:
        function_args = pickle.load(f)
    
    results_str = build_rf_model.build_model(
        featureset_name=function_args["featureset_name"],
        featureset_key=function_args["featureset_key"],
        model_type=function_args["model_type"],
        in_docker_container=True)
    
    return results_str


if __name__=="__main__":
    results_str = build_model()
    print(results_str)
