from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib
import os
from mltsp import cfg
from mltsp import custom_exceptions
import numpy as np
import csv


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
        ("/tmp" if in_docker_container else cfg.MODELS_FOLDER),
        "%s_%s.pkl" % (featureset_key, model_type))
    joblib.dump(rf_fit, foutname, compress=3)
    print(foutname, "created.")
    return foutname


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
    tuple of list
        Two-element tuple whose first element is a list of the column
        names in the file, and whose second element is a list of lists,
        each list containing the values in each row in the file.

    """
    with open(fname) as f:
        r = csv.reader(f)
        all_rows = list(r)[skip_lines:]
    colnames = all_rows[0]
    data_rows = all_rows[1:]
    data_rows = [[el if el != '?' else '0.0'for el in row] for row in data_rows]
    return colnames, data_rows


def clean_up_data_dict(data_dict):
    """Remove any empty lines from data (modifies dict in place).

    Parameters
    ----------
    data_dict : dict
        Dictionary containing features data w/ key 'features'.

    """
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
    indices_for_deletion.sort(reverse=True)
    for index in indices_for_deletion:
        del data_dict['features'][index]
        del data_dict['classes'][index]
    return


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


def parse_ts_data(filepath, sep=","):
    """
    """
    with open(filepath) as f:
        ts_data = np.loadtxt(f, delimiter=sep)
    ts_data = ts_data[:,:3] # Only using T, M, E
    for row in ts_data:
        if len(row) < 2:
            raise custom_exceptions.DataFormatError(
                "Incomplete or improperly formatted time "
                "series data file provided.")
    return ts_data.T
