#!/usr/bin/env python

# docker_featurize.py

# to be run from INSIDE a docker container


from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import *
import subprocess
import sys
import os
sys.path.append("/home/mltsp/mltsp")
#import featurize
from subprocess import Popen, PIPE, call
import time

# ----
from disco.core import Job, result_iterator

def map(line, params):
    for word in line.split():
        yield word, 1


def reduce(iter, params):
    from disco.util import kvgroup
    for word, counts in kvgroup(sorted(iter)):
        yield word, sum(counts)


def disco_word_count():
    job = Job().run(input=["http://discoproject.org/media/text/chekhov.txt"],
                    map=map,
                    reduce=reduce)
    for word, count in result_iterator(job.wait(show=True)):
        print(word, count)
#----


def disco_test():
    print("*" * 80)
    print("Disco Test")
    print("*" * 80)

    process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print("-> disco status", stdout, stderr)

    time.sleep(2)

    if "stopped" in str(stdout):
        print("Error: disco not running")
        sys.exit(-1)

    elif "running" in str(stdout):
        disco_word_count()
        results_str = 'OK'
        ## results_str = featurize.featurize(
        ##     "/Data/sample_lcs/asas_training_set_classes.dat",
        ##     "/Data/sample_lcs/asas_training_set.tar.gz",
        ##     features_to_use=[],
        ##     featureset_id="JUST_A_TEST_FEATSET",
        ##     is_test=True,
        ##     USE_DISCO=True,
        ##     already_featurized=False,
        ##     custom_script_path=None,
        ##     in_docker_container=True)

        return results_str


if __name__=="__main__":
    results_str = disco_test()
    print(results_str)
