#!/usr/bin/env python

# to be run from INSIDE a docker container

import sys
sys.path.append("/home/mltsp/mltsp")
#import featurize
from subprocess import Popen, PIPE
import time

# TODO: This script should not be loaded when not inside a docker container
#       E.g., disco needn't be installed on the server.  For now, we simply
#       ignore the import error.
try:
    from disco.core import Job, result_iterator
except:
    pass

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
        ##     "/home/mltsp/mltsp/Data/sample_lcs/asas_training_set_classes.dat",
        ##     "/home/mltsp/mltsp/Data/sample_lcs/asas_training_set.tar.gz",
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
