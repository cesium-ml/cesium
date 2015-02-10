# to be run from INSIDE a docker container

from .. import custom_feature_tools as cft

try:
    import cPickle as pickle
except:
    import pickle

def extract_custom_feats():
    """Load pickled parameters and generate custom features.

    To be run from inside a Docker container. Pickles the extracted
    features for later copying from container to host machine.

    Returns
    -------
    int
        Returns 0.

    """
    # load pickled ts_data and known features
    with open(
        "/home/mltsp/copied_data_files/features_already_known_list.pkl",
        "rb") as f:
        features_already_known_list = pickle.load(f)

    # script has been copied to the following location:
    script_fpath = ("/home/mltsp/mltsp/custom_feature_scripts/"
                    "custom_feature_defs.py")

    # extract features
    all_feats = cft.execute_functions_in_order(
        features_already_known=features_already_known_list,
        script_fpath=script_fpath)

    with open("/tmp/results_list_of_dict.pkl", "wb") as f:
        pickle.dump(all_feats, f, protocol=2)

    print("Created /tmp/results_list_of_dict.pkl in docker container.")
    return 0


if __name__ == "__main__":
    all_feats = extract_custom_feats()
    print(all_feats)
