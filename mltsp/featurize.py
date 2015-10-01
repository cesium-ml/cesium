#!/usr/bin/python
# featurize.py

from __future__ import print_function
import shutil
import tempfile
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
from random import shuffle
import os
import tarfile
import numpy as np

from . import cfg
from . import custom_feature_tools as cft
from . import util
from . import custom_exceptions
from .celery_tasks import featurize_ts_data as featurize_celery_task


# TODO use this everywhere?
def shorten_fname(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]
    
def parse_prefeaturized_csv_data(features_file_path):
    """Parse CSV file containing features.

    Parameters
    ----------
    features_file_path : str
        Path to CSV file containing features.

    Returns
    -------
    list of dict
        Returns list of dictionaries containing features - feature
        names as keys, corresponding values as dict values.

    """
    objects = []
    with open(features_file_path) as f:
        # First line contains column titles
        keys = f.readline().strip().split(',')
        for line in f:
            vals = line.strip().split(",")
            if len(vals) != len(keys):
                continue
            else:
                objects.append({})
                for i in range(len(keys)):
                    objects[-1][keys[i]] = vals[i]
    return objects


def parse_headerfile(headerfile_path, features_to_use):
    """Parse header file.

    Parameters
    ----------
    headerfile_path : str
        Path to header file.

    features_to_use : list of str
        List of feature names to be generated.

    Returns
    -------
    tuple

    """
    with open(headerfile_path, 'r') as headerfile:
        fname_class_dict = {}
        fname_class_science_features_dict = {}
        fname_metadata_dict = {}
        # Write IDs and classnames to dict
        line_no = 0
        other_metadata_labels = []
        for line in headerfile:
            if line_no == 0:
                els = line.strip().split(',')
                fname, class_name = els[:2]
                other_metadata_labels = els[2:]
                features_to_use += other_metadata_labels
            else:
                if len(line) > 1 and line[0] not in ["#", "\n"]:
                    if len(line.split(',')) == 2:
                        fname, class_name = line.strip('\n').split(',')
                        fname_class_dict[fname] = class_name
                        fname_class_science_features_dict[fname] = {
                            'class': class_name}
                    elif len(line.split(',')) > 2:
                        els = line.strip().split(',')
                        fname, class_name = els[:2]
                        other_metadata = els[2:]
                        # Convert to floats, if applicable:
                        for i in range(len(other_metadata)):
                            try:
                                other_metadata[i] = float(
                                    other_metadata[i])
                            except ValueError:
                                pass
                        fname_class_dict[fname] = class_name
                        fname_class_science_features_dict[fname] = {
                            'class': class_name}
                        fname_metadata_dict[fname] = dict(
                            list(zip(other_metadata_labels,
                                     other_metadata)))
            line_no += 1
    return (features_to_use, fname_class_dict,
            fname_class_science_features_dict,
            fname_metadata_dict)


def generate_featurize_input_params_list(features_to_use, fname_class_dict,
                                         fname_class_science_features_dict,
                                         fname_metadata_dict, zipfile_path,
                                         custom_script_path, is_test):
    """
    """
    input_params_list = []

    zipfile = tarfile.open(zipfile_path)
    unzip_dir = tempfile.mkdtemp()
    zipfile.extractall(path=unzip_dir)
    all_fnames = zipfile.getnames()
    num_objs = len(fname_class_dict)

    for fname in all_fnames:
        if is_test and len(input_params_list) >= 3:
            break
        short_fname = shorten_fname(fname)
        if os.path.isfile(fname):
            ts_path = fname
        elif os.path.isfile(os.path.join(unzip_dir, fname)):
            ts_path = os.path.join(unzip_dir, fname)
        else:
            continue
        input_params_list.append((ts_path, custom_script_path,
                                  fname_class_dict[short_fname],
                                  features_to_use))
    return input_params_list


def generate_features(headerfile_path, zipfile_path, features_to_use,
                      custom_script_path, is_test, already_featurized,
                      in_docker_container):
    """Generate features for provided time-series data."""
    if already_featurized:
        # Read in features from CSV file
        objects = parse_prefeaturized_csv_data(headerfile_path)
    else:
        # Parse header file
        (features_to_use, fname_class_dict, fname_class_science_features_dict,
         fname_metadata_dict) = parse_headerfile(headerfile_path,
                                                 features_to_use)
        input_params_list = generate_featurize_input_params_list(
            features_to_use, fname_class_dict,
            fname_class_science_features_dict, fname_metadata_dict,
            zipfile_path, custom_script_path, is_test)
        # TO-DO: Determine number of cores in cluster:
        res = featurize_celery_task.chunks(input_params_list,
                                           cfg.N_CORES).delay()
        res_list = res.get(timeout=100)
        objects = []
        for line in res_list:
            for el in line:
                short_fname, new_feats = el
                if short_fname in fname_metadata_dict:
                    all_features = dict(
                        list(new_feats.items()) +
                        list(fname_metadata_dict[short_fname].items()))
                else:
                    all_features = new_feats
                objects.append(all_features)
    return objects


def determine_feats_to_plot(features_extracted):
    """
    """
    if len(set(cfg.features_to_plot) & set(features_extracted)) < 4:
        features_extracted_copy = features_extracted[:]
        shuffle(features_extracted_copy)
        features_to_plot = features_extracted_copy[:5]
    else:
        features_to_plot = cfg.features_to_plot
    return features_to_plot


def write_column_titles(f, f2, features_extracted, features_to_use,
                        features_to_plot):
    """

    """
    line = []
    line2 = ['class']
    for feat in sorted(features_extracted):
        if feat in features_to_use:
            print("Using feature", feat)
            line.append(feat)
            if feat in features_to_plot:
                line2.append(feat)
    f.write(','.join(line) + '\n')
    f2.write(','.join(line2) + '\n')


def count_classes(objects):
    """

    """
    class_count = {}
    num_used = {}
    num_held_back = {}
    # count up total num of objects per class
    for obj in objects:
        if str(obj['class']) not in class_count:
            class_count[str(obj['class'])] = 1
            num_used[str(obj['class'])] = 0
            num_held_back[str(obj['class'])] = 0
        else:
            class_count[str(obj['class'])] += 1
    return (class_count, num_used, num_held_back)


def write_features_to_disk(objects, featureset_id, features_to_use,
                           in_docker_container):
    """

    """
    if objects is None:
        raise Exception("featurize.write_features_to_disk - `objects` is None")
    if len(objects) > 0:
        features_extracted = list(objects[-1].keys())
    else:
        features_extracted = []
        return
    if "class" in features_extracted:
        features_extracted.remove("class")
    features_to_plot = determine_feats_to_plot(features_extracted)

    with open(os.path.join(
            cfg.FEATURES_FOLDER, "%s_features.csv" % featureset_id),
              'w') as f, open(os.path.join(
                  cfg.FEATURES_FOLDER,
                  "%s_features_with_classes.csv" % featureset_id), 'w') as f2:
        write_column_titles(f, f2, features_extracted, features_to_use,
                            features_to_plot)
        class_count, num_used, num_held_back = count_classes(objects)
        classes = []
        cv_objs = []
        numobjs = 0
        print("Writing object features to file...")
        for obj in objects:
            # total number of lcs for given class encountered < 70% total num lcs
            # if (num_used[str(obj['class'])] + num_held_back[str(obj['class'])]
            #   < 0.7*class_count[str(obj['class'])]):
            # overriding above line that held back 30% of objects from model
            # creation for CV purposes :
            if 1:
                line = []
                line2 = [obj['class']]
                for feat in sorted(features_extracted):
                    if feat in features_to_use:
                        try:
                            if isinstance(obj[feat], (str, type(u''))) and \
                               obj[feat] not in ["None", u"None"]:
                                line.append(str(obj[feat]))
                            elif obj[feat] is None or obj[feat] in ["None",
                                                                    u"None"]:
                                line.append(str(0.0))
                            else:
                                line.append(str(obj[feat]))
                            if feat in features_to_plot and numobjs < 300:
                                if isinstance(obj[feat], (str, type(u''))) and \
                                   obj[feat] not in ["None", u"None"]:
                                    line2.append(str(obj[feat]))
                                elif (obj[feat] is None
                                      or obj[feat] in ["None", u"None"]):
                                    line2.append(str(0.0))
                                else:
                                    line2.append(str(obj[feat]))
                        except KeyError:
                            print(feat, "NOT IN DICT KEYS!!!! SKIPPING...")
                f.write(','.join(line) + '\n')
                if numobjs < 300:
                    f2.write(','.join(line2) + '\n')
                classes.append(str(obj['class']))
                num_used[str(obj['class'])] += 1
            else:
                cv_objs.append(obj)
                num_held_back[str(obj['class'])] += 1
            numobjs += 1
    if not in_docker_container:
        shutil.copy2(
            f2.name, os.path.join(cfg.MLTSP_PACKAGE_PATH, "Flask/static/data"))
    np.save(os.path.join(
        ("/tmp" if in_docker_container else cfg.FEATURES_FOLDER),
        "%s_classes.npy" % featureset_id), classes)
    print("Done.")


def featurize(
        headerfile_path, zipfile_path, features_to_use=[],
        featureset_id="unknown", is_test=False, already_featurized=False,
        custom_script_path=None, in_docker_container=False):
    """Generate features for labeled time series data.

    Features are saved to the file given by
    ``"%s_features.csv" % featureset_id``
    and a list of corresponding classes is saved to the file given by
    ``"%s_classes.npy" % featureset_id``
    in the directory `cfg.FEATURES_FOLDER` (or is later copied there if
    generated inside a Docker container).

    Parameters
    ----------
    headerfile_path : str
        Path to header file containing file names, class names, and
        metadata.
    zipfile_path : str
        Path to the tarball of individual time series files to be used
        for feature generation.
    features_to_use : list of str, optional
        List of feature names to be generated. Defaults to an empty
        list, which results in all available features being used.
    featureset_id : str, optional
        RethinkDB ID of the new feature set entry. Defaults to
        "unknown".
    is_test : bool, optional
        Boolean indicating whether to do a test run of only the first
        five time-series files. Defaults to False.
    already_featurized : bool, optional
        Boolean indicating whether `headerfile_path` points to a file
        containing pre-generated features, in which case `zipfile_path`
        must be None. Defaults to False.
    custom_script_path : str, optional
        Path to Python script containing function definitions for the
        generation of any custom features. Defaults to None.
    in_docker_container : bool, optional
        Boolean indicating whether function is being called from inside
        a Docker container. Defaults to False.

    Returns
    -------
    str
        Human-readable message indicating successful completion.

    """
    # Generate features for each TS object
    features = generate_features(
        headerfile_path, zipfile_path, features_to_use,
        custom_script_path, is_test, already_featurized, in_docker_container)

    write_features_to_disk(features, featureset_id, features_to_use,
                           in_docker_container)
    # Clean up
    if not in_docker_container:
        os.remove(os.path.join(
            cfg.FEATURES_FOLDER, "%s_features_with_classes.csv" % featureset_id))
        os.remove(headerfile_path)
        if zipfile_path is not None:
            os.remove(zipfile_path)
    return "Featurization of timeseries data complete."
