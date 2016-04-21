# Meant to be run from INSIDE a docker containe
from __future__ import print_function

import os
from os.path import join as pjoin
import sys
import json

# Add cesium to path
sys.path.insert(0, pjoin(os.path.dirname(__file__), '..'))

from cesium_app import custom_feature_tools as cft


def extract_custom_feats(tmp_dir):
    """Load pickled parameters and generate custom features.

    To be run from inside a Docker container. Pickles the extracted
    features for later copying from container to host machine.

    Returns
    -------
    int
        Returns 0.

    """
    # load ts_data and known features
    with open(os.path.join(tmp_dir, "features_already_known.json"), "r") as f:
        features_already_known = json.load(f)

    script_fpath = os.path.join(tmp_dir, "custom_feature_defs.py")

    # extract features
    all_feats = cft.execute_functions_in_order(
        features_already_known=features_already_known,
        script_fpath=script_fpath)

    with open("/tmp/results_dict.json", "w") as f:
        json.dump(all_feats, f)

    print("Created /tmp/results_dict.json in docker container.")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='cesium Docker scripts')
    parser.add_argument('--tmp_dir', dest='tmp_dir', action='store', type=str)
    args = parser.parse_args()

    features = extract_custom_feats(args.tmp_dir)
    print(features)
