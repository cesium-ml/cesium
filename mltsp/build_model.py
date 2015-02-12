#!/usr/bin/python
# build_model.py

from operator import itemgetter
import shutil
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
from random import shuffle
import sys
import os

from . import cfg
from . import lc_tools
from . import custom_feature_tools as cft


def read_data_from_csv_file(fname, sep=',', skip_lines=0):
    """Parse CSV file and return data in list form.

    Parameters
    ----------
    fname : str
        Path to the CSV file.
    sep : str, optional
        Delimiting character in CSV file. Defaults to ",".
    skip_lines : int, optional
        Number of leading lines to skip in file. Defaults to 0.

    Returns
    -------
    list of list
        Two-element list whose first element is a list of the column
        names in the file, and whose second element is a list of lists,
        each list containing the values in each row in the file.

    """
    f = open(fname)
    linecount = 0
    data_rows = []
    all_rows = []
    for line in f:
        if linecount >= skip_lines:
            if linecount == 0:
                colnames = line.strip('\n').split(sep)
                all_rows.append(colnames)
            else:
                data_rows.append(line.strip('\n').split(sep))
                all_rows.append(line.strip('\n').split(sep))
                if "?" in line:
                    # Replace missing values with 0.0
                    data_rows[-1] = [el if el != "?" else "0.0"
                                     for el in data_rows[-1]]
                    all_rows[-1] = [el if el != "?" else "0.0"
                                    for el in all_rows[-1]]
        linecount += 1

    try:
        colnames
    except NameError:
        return [[], []]
    for i in range(len(colnames)):
        colnames[i] = colnames[i].strip('"')
    print(linecount - 1, "lines of data successfully read.")
    f.close()
    # return all_rows
    return [colnames, data_rows]


def count_classes(classes):
    """Count total number of objects per class.

    """
    # Count up total num of objects per class
    class_count = {}
    class_list = []
    for classname in classes:
        if classname not in class_list:
            class_list.append(classname)
            class_count[classname] = 1
        else:
            class_count[classname] += 1
    print("class_count:", class_count)
    sorted_class_list = sorted(class_list)
    return (class_count, sorted_class_list)


def clean_up_data_dict(data_dict):
    """Remove any empty lines from data.

    """
    print("\n\n")
    line_lens = []
    indices_for_deletion = []
    line_no = 0
    for i in range(len(data_dict['features'])):
        line = data_dict['features'][i]
        if len(line) not in line_lens:
            line_lens.append(len(line))
            if len(line) == 1:
                indices_for_deletion.append(i)
        line_no += 1
    print(line_no, "total lines in features csv.")
    print(len(data_dict['features']))
    if len(indices_for_deletion) == 1:
        del data_dict['features'][indices_for_deletion[0]]
        del data_dict['classes'][indices_for_deletion[0]]
    print(len(data_dict['features']))
    print("\n\n")


def create_and_pickle_model(data_dict, featureset_key, model_type,
                            in_docker_container, models_folder):
    """
    """
    # Build the model:
    # Initialize
    ntrees = 1000
    njobs = -1
    rf_fit = RFC(n_estimators=ntrees, max_features='auto', n_jobs=njobs)
    print("Model initialized.")

    # Fit the model to training data:
    print("Fitting the model...")
    rf_fit.fit(data_dict['features'], data_dict['classes'])
    print("Done.")
    del data_dict

    # Store the model:
    print("Pickling model...")
    foutname = os.path.join(
        ("/tmp" if in_docker_container else models_folder),
        "%s_%s.pkl" % (featureset_key, model_type))
    joblib.dump(rf_fit, foutname, compress=3)
    print(foutname, "created.")


def read_features_data_from_disk(featureset_key, features_folder):
    """
    """
    features_filename = os.path.join(
        features_folder, "%s_features.csv" % featureset_key)
    # Read in feature data and class list
    features_extracted, all_data = read_data_from_csv_file(features_filename)
    classes = joblib.load(
        features_filename.replace("_features.csv", "_classes.pkl"))

    # Put data and class list into dictionary
    data_dict = {}
    data_dict['features'] = all_data
    data_dict['classes'] = classes
    return data_dict


def build_model(
        featureset_name, featureset_key, model_type="RF",
        in_docker_container=False):
    """Build a `scikit-learn` classifier.

    Builds the specified model and pickles it in the file
    whose name is given by
    ``"%s_%s.pkl" % (featureset_key, model_type)``
    in the directory `cfg.MODELS_FOLDER` (or is later copied there
    from within the Docker container if `in_docker_container` is True.

    Parameters
    ----------
    featureset_name : str
        Name of the feature set to build the model upon (will also
        become the model name).
    featureset_key: str
        RethinkDB ID of the associated feature set from which to build
        the model, which will also become the ID/key for the model.
    model_type : str
        Abbreviation of the type of classifier to be created. Defaults
        to "RF".
    in_docker_container : bool, optional
        Boolean indicating whether function is being called from within
        a Docker container.

    Returns
    -------
    str
        Human-readable message indicating successful completion.

    """
    # Determine which directory paths to use
    if in_docker_container:
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER

    data_dict = read_features_data_from_disk(featureset_key, features_folder)

    class_count, sorted_class_list = count_classes(data_dict["classes"])

    clean_up_data_dict(data_dict)

    create_and_pickle_model(data_dict, featureset_key, model_type,
                            in_docker_container, models_folder)

    print("DONE!")
    return ("New model successfully created. Click the Predict tab to "
            "start using it.")
