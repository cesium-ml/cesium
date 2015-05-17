# to be run from INSIDE a docker container

from __future__ import print_function
import os
from .. import featurize
from .. import util

import pickle
import time


def do_featurization(data_path):
    """Load pickled parameters and call `featurize.featurize`.

    To be run from inside a Docker container.

    Returns
    -------
    str
        Human readable message indicating completion of feature
        generation.

    """
    # Load pickled ts_data and known features
    with open(os.path.join(data_path, "function_args.pkl"), "rb") as f:
        function_args = pickle.load(f)
    # Ensure required files successfully copied into container:
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
                             "disk.") % zipfile_path)
    elif ("already_featurized" in function_args and
          function_args["already_featurized"] == False):
        raise Exception("ERROR - IN DOCKER CONTAINER featurize - zipfile_path "
                        "not in function args.")
    elif ("already_featurized" in function_args and
          function_args["already_featurized"] == True):
        pass
    disco_running = util.check_disco_running()
    results_str = featurize.featurize(
        function_args["headerfile_path"],
        function_args["zipfile_path"],
        features_to_use=function_args["features_to_use"],
        featureset_id=function_args["featureset_key"],
        is_test=function_args["is_test"],
        USE_DISCO=False,
        already_featurized=function_args["already_featurized"],
        custom_script_path=function_args["custom_script_path"],
        in_docker_container=True)
    return results_str


if __name__ == "__main__":
    results_str = do_featurization()
    print(results_str)
