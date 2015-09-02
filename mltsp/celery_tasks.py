from sklearn.ensemble import RandomForestClassifier as RFC
from celery import Celery
import os
import sys
import pickle
import numpy as np
import uuid
from mltsp import custom_feature_tools as cft
from mltsp import cfg
from mltsp import lc_tools
from mltsp import custom_exceptions
from copy import deepcopy
import uuid
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib


sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "ext"))
os.environ['CELERY_CONFIG_MODULE'] = 'celeryconfig'
celery_app = Celery('celery_fit', broker='amqp://guest@localhost//')


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
    ts_data = ts_data[:, :3].tolist()  # Only using T, M, E; convert to list
    for row in ts_data:
        if len(row) < 2:
            raise custom_exceptions.DataFormatError(
                "Incomplete or improperly formatted time "
                "series data file provided.")
    return ts_data


@celery_app.task(name='celery_tasks.fit_model')
def fit_and_store_model(featureset_name, featureset_key, model_type,
                        in_docker_container):
    """
    """
    data_dict = read_features_data_from_disk(featureset_key)

    created_file_name = create_and_pickle_model(
        data_dict, featureset_key, model_type, in_docker_container)
    return created_file_name


@celery_app.task(name="celery_tasks.pred_featurize_single")
def pred_featurize_single(ts_data, features_to_use, custom_features_script,
                          meta_features, short_fname, sep):
    """
    """
    big_features_and_tsdata_dict = {}
    # Generate features:
    if len(list(set(features_to_use) & set(cfg.features_list))) > 0:
        timeseries_features = lc_tools.generate_timeseries_features(
            deepcopy(ts_data), sep=sep, ts_data_passed_directly=True)
    else:
        timeseries_features = {}
    if len(list(set(features_to_use) &
                set(cfg.features_list_science))) > 0:
        from mltsp.TCP.Software.ingest_tools import generate_science_features
        science_features = generate_science_features.generate(
            ts_data=deepcopy(ts_data))
    else:
        science_features = {}
    if custom_features_script is not None:
        fname = os.path.join("/tmp", str(uuid.uuid4())[:10] + ".py")
        with open(fname, "w") as f:
            f.writelines(custom_features_script)
        custom_features_script = fname
        custom_features = cft.generate_custom_features(
            custom_script_path=custom_features_script, path_to_csv=None,
            features_already_known=dict(
                list(timeseries_features.items()) + list(science_features.items()) +
                (
                    list(meta_features[short_fname].items()) if short_fname in
                    meta_features else list({}.items()))), ts_data=ts_data)
        if (isinstance(custom_features, list) and
                len(custom_features) == 1):
            custom_features = custom_features[0]
        elif (isinstance(custom_features, list) and
              len(custom_features) == 0):
            custom_features = {}
        elif (isinstance(custom_features, list) and
              len(custom_features) > 1):
            raise("len(custom_features) > 1 for single TS data obj")
        elif not isinstance(custom_features, (list, dict)):
            raise("custom_features ret by cft module is of an invalid type")
    else:
        custom_features = {}
    features_dict = dict(
        list(timeseries_features.items()) + list(science_features.items()) +
        list(custom_features.items()) +
        (list(meta_features[short_fname].items()) if short_fname
         in meta_features else list({}.items())))
    big_features_and_tsdata_dict[short_fname] = {
        "features_dict": features_dict, "ts_data": ts_data}
    return big_features_and_tsdata_dict


@celery_app.task(name="celery_tasks.featurize_ts_data")
def featurize_ts_data(ts_data_file_path, short_fname, custom_script_path,
                      object_class, features_to_use):
    """

    """
    ts_data = parse_ts_data(ts_data_file_path)
    # Generate general/cadence-related TS features, if to be used
    if len(set(features_to_use) & set(cfg.features_list)) > 0:
        timeseries_features = (
            lc_tools.generate_timeseries_features(
                deepcopy(ts_data),
                classname=object_class,
                sep=',', ts_data_passed_directly=True))
    else:
        timeseries_features = {}
    # Generate TCP TS features, if to be used
    if len(
            set(features_to_use) &
            set(cfg.features_list_science)) > 0:
        from mltsp.TCP.Software.ingest_tools import \
            generate_science_features
        science_features = generate_science_features.generate(
            ts_data=ts_data)
    else:
        science_features = {}
    # Generate custom features, if any
    if custom_script_path:
        custom_features = cft.generate_custom_features(
            custom_script_path=custom_script_path,
            path_to_csv=None,
            features_already_known=dict(
                list(timeseries_features.items()) +
                list(science_features.items())),
            ts_data=deepcopy(ts_data))[0]
    else:
        custom_features = {}
    # Combine all features into single dict
    all_features = dict(
        list(timeseries_features.items()) +
        list(science_features.items()) +
        list(custom_features.items()))
    all_features['class'] = object_class
    return (short_fname, all_features)
