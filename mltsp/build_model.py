#!/usr/bin/python
# build_model.py

from __future__ import print_function
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
import os
import numpy as np
import pickle
from . import cfg
from mltsp.celery_fit import fit_model


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

    Parameters
    ----------
    classes : list of str
        List of classes

    Returns
    ------
    tuple
        Two-element tuple consisting of a dict whose keys are class names
        and values are number of occurrences, and a (sorted) list of unique
        class names.

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
    """Remove any empty lines from data (modifies dict in place).

    Parameters
    ----------
    data_dict : dict
        Dictionary containing features data w/ key 'features'.

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
    return


#@celery_app.task
def fit_model_orig(data_dict):
    """
    """
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
    return rf_fit


def reduce(iter, params):
    """
    """
    from sklearn.ensemble import RandomForestClassifier as RFC

    data_dict = params["data_dict"]
    for x in range(1):
        ntrees = 1000
        njobs = -1
        rf_fit = RFC(n_estimators=ntrees, max_features='auto', n_jobs=njobs)
        print("Model initialized.")

        # Fit the model to training data:
        print("Fitting the model...")
        rf_fit.fit(data_dict['features'], data_dict['classes'])
        print("Done.")
        yield rf_fit, "string"


def fit_model_disco(data_dict, featureset_key, model_type):
    """
    """
    from disco.core import Job, result_iterator
    params = {"data_dict": data_dict,
              "featureset_key": featureset_key,
              "model_type": model_type}
    input_list = [("placeholder")]
    job = Job('with_modules').run(
        input=input_list,
        reduce=reduce,
        params=params,
        required_modules=[("mltsp",
                           os.path.dirname(os.path.dirname(__file__))),
                          "sklearn"])
    result_iter = result_iterator(job.wait(show=True))
    rf_fit = None
    for rf_obj, dummy_str in result_iter:
        rf_fit = rf_obj
    return rf_fit


def create_and_pickle_model(data_dict, featureset_key, model_type,
                            in_docker_container):
    """Create scikit-learn RFC model object and save it to disk.

    Parameters
    ----------
    data_dict : dict
        Dictionary containing features data (key 'features') and
        class list (key 'classes').
    featureset_key : str
        RethinkDB ID of associated feature set.
    model_type : str
        Abbreviation of the type of classifier to be created.
    in_docker_container : bool
        Boolean indicating whether function is being called from within
        a Docker container.

    """
    # Fit the model
    rf_fit_pkl = fit_model.delay(data_dict)
    rf_fit_pkl = rf_fit_pkl.get(timeout=2)
    rf_fit = pickle.loads(rf_fit_pkl)

    # Store the model:
    print("Pickling model...")
    foutname = os.path.join(
        ("/tmp" if in_docker_container else cfg.MODELS_FOLDER),
        "%s_%s.pkl" % (featureset_key, model_type))
    joblib.dump(rf_fit, foutname, compress=3)
    print(foutname, "created.")


def read_features_data_from_disk(featureset_key):
    """Read features & class data from local CSV and return it as dict.

    Parameters
    ----------
    featureset_key : str
        RethinkDB ID of associated feature set.

    Returns
    -------
    dict
        Dictionary with 'features' key whose value is a list of
        lists containing features data, and 'classes' whose
        associated value is a list of the classes associated with
        each row of features data.

    """
    features_filename = os.path.join(
        cfg.FEATURES_FOLDER, "%s_features.csv" % featureset_key)
    # Read in feature data and class list
    features_extracted, all_data = read_data_from_csv_file(features_filename)
    classes = list(np.load(features_filename.replace("_features.csv",
                                                     "_classes.npy")))

    # Put data and class list into dictionary
    data_dict = {}
    data_dict['features'] = all_data
    data_dict['classes'] = classes
    # Modifies in-place:
    clean_up_data_dict(data_dict)

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
    data_dict = read_features_data_from_disk(featureset_key)

    # class_count, sorted_class_list = count_classes(data_dict["classes"])

    create_and_pickle_model(data_dict, featureset_key, model_type,
                            in_docker_container)

    print("DONE!")
    return ("New model successfully created. Click the Predict tab to "
            "start using it.")
