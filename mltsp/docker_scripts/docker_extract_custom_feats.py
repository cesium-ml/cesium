# to be run from INSIDE a docker container

from __future__ import print_function
from .. import custom_feature_tools as cft

import os
import json

def extract_custom_feats(data_path):
    """Load pickled parameters and generate custom features.

    To be run from inside a Docker container. Pickles the extracted
    features for later copying from container to host machine.

    Returns
    -------
    int
        Returns 0.

    """
    # load ts_data and known features
    with open(os.path.join(data_path, "features_already_known.json"), "r") \
            as f:
        features_already_known = json.load(f)

    script_fpath = os.path.join(data_path, "custom_feature_defs.py")
    # extract features
    all_feats = cft.execute_functions_in_order(
        features_already_known=features_already_known,
        script_fpath=script_fpath)

    with open("/tmp/results_dict.json", "w") as f:
        json.dump(all_feats, f)

    print("Created /tmp/results_dict.json in docker container.")
    return 0


if __name__ == "__main__":
    all_feats = extract_custom_feats()
    print(all_feats)
