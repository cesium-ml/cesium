# to be run from INSIDE a docker container

import subprocess
import sys
import os
from .. import featurize
import time

from subprocess import Popen, PIPE, call
import pickle


def do_featurization():
    """Load pickled parameters and call `featurize.featurize`.

    To be run from inside a Docker container.

    Returns
    -------
    str
        Human readable message indicating completion of feature
        generation.

    """
    '''process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if "stopped" in str(stdout):
        print("Disco is stopped - attempting to start Disco...")
        status_code = call(["/disco/bin/disco","nodaemon"])
        print("Status code for Disco command:", status_code)
        time.sleep(2)
        process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        if "stopped" in str(stdout):
            print("Disco is stopped - attempting to start Disco...")
            status_code = call(["disco","start"])
            print("Status code for Disco command:", status_code)
            time.sleep(2)
            process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            if "stopped" in str(stdout):
                print("Disco still stopped... Will featurize without Disco.")
                disco_running = False
            else:
                disco_running = True
        else:
            disco_running = True
    else:
        disco_running = True
    '''
    disco_running = False # Just for now til we get it working
    # load pickled ts_data and known features
    with open("/home/mltsp/copied_data_files/function_args.pkl","rb") as f:
        function_args = pickle.load(f)
    # ensure required files successfully copied into container:
    if "headerfile_path" in function_args:
        headerfile_path = str(function_args['headerfile_path'])
        if os.path.isfile(headerfile_path):
            pass
        else:
            raise Exception(("ERROR - IN DOCKER CONTAINER featurize - " +
                            "headerfile_path = %s is not a file currently " +
                            "on disk.") % headerfile_path)
    else:
        raise Exception("ERROR - IN DOCKER CONTAINER featurize - " +
                        "headerfile_path not in function args.")
    if "zipfile_path" in function_args:
        zipfile_path = str(function_args['zipfile_path'])
        if os.path.isfile(zipfile_path):
            pass
        else:
            raise Exception(("ERROR - (IN DOCKER CONTAINER) featurize - "
                             "zipfile_path = %s is not a file currently on "
                             "disk.")%zipfile_path)
    elif ("already_featurized" in function_args and
          function_args["already_featurized"] == False):
        raise Exception("ERROR - IN DOCKER CONTAINER featurize - zipfile_path "
                        "not in function args.")
    elif ("already_featurized" in function_args and
          function_args["already_featurized"] == True):
        pass
    results_str = featurize.featurize(
        function_args["headerfile_path"],
        function_args["zipfile_path"],
        features_to_use=function_args["features_to_use"],
        featureset_id=function_args["featureset_key"],
        is_test=function_args["is_test"],
        USE_DISCO=disco_running,
        already_featurized=function_args["already_featurized"],
        custom_script_path=function_args["custom_script_path"],
        in_docker_container=True)
    return results_str


if __name__=="__main__":
    results_str = do_featurization()
    print(results_str)
