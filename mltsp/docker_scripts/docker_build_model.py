# to be run from INSIDE a docker container

from __future__ import print_function
from .. import build_model as BM

import pickle
import os


def build_model(data_path):
    """Load pickled parameters and call `build_model.build_model`.

    To be called from inside a Docker container. Pickles model which
    will later be copied to host machine.

    Returns
    -------
    str
        Human readable message indicating successful completion.

    """
    # load pickled ts_data and known features
    with open(os.path.join(data_path, "function_args.pkl"), "rb") as f:
        function_args = pickle.load(f)

    results_str = BM.build_model(
        featureset_name=function_args["featureset_name"],
        featureset_key=function_args["featureset_key"],
        model_type=function_args["model_type"],
        in_docker_container=True)

    return results_str


if __name__ == "__main__":
    results_str = build_model()
    print(results_str)
