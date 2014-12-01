# docker_featurize.py

# to be run from INSIDE a docker container

import subprocess
import sys
import os
sys.path.append("/home/mltp")
import build_rf_model
from subprocess import Popen, PIPE, call
import cPickle
import time


def disco_test():
    print "*" * 80
    print "Disco Test"
    print "*" * 80

    process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print "-> disco status", stdout, stderr

    if "stopped" in str(stdout):
        print "Error: disco not running"

    elif "running" in str(stdout):
        results_str = build_rf_model.featurize(
            "/Data/sample_lcs/asas_training_set_classes.dat",
            "/Data/sample_lcs/asas_training_set.tar.gz",
            features_to_use=[],
            featureset_id="JUST_A_TEST_FEATSET",
            is_test=True,
            USE_DISCO=True,
            already_featurized=False,
            custom_script_path=None,
            in_docker_container=True)

        return results_str


if __name__=="__main__":
    results_str = disco_test()
    print results_str
