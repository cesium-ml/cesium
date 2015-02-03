#!/usr/bin/python
# featurize.py

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import open
from builtins import range
from builtins import dict
from builtins import str
from builtins import zip
from future import standard_library
standard_library.install_aliases()
from builtins import *
from operator import itemgetter
import shutil
from sklearn.externals import joblib
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
from random import shuffle
import sys
import os
import tarfile
try:
    from disco.core import Job, result_iterator
    from disco.util import kvgroup
    DISCO_INSTALLED = True
except ImportError as theError:
    DISCO_INSTALLED = False
if DISCO_INSTALLED:
    from . import parallel_processing

from . import cfg
from . import lc_tools
from . import custom_feature_tools as cft


def shorten_fname(fname):
    """Return shortened file name without full path and suffix.

    """
    return fname.split("/")[-1].replace(
        ("." + fname.split(".")[-1] if "." in fname.split("/")[-1] else ""), "")


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
        List of feature names to be generated. Defaults to an empty
        list, which results in all available features being used.

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


def generate_features(headerfile_path, zipfile_path, features_to_use,
                      custom_script_path, is_test, USE_DISCO,
                      already_featurized, in_docker_container, uploads_folder):
    """Generate features for provided time-series data.

    """
    all_features_list = cfg.features_list[:] + cfg.features_list_science[:]
    if len(features_to_use) == 0:
        features_to_use = all_features_list

    if already_featurized:
        # Read in features from CSV file
        objects = parse_prefeaturized_csv_data(headerfile_path)
        return objects
    else:
        # Parse header file
        (features_to_use, fname_class_dict, fname_class_science_features_dict,
         fname_metadata_dict) = parse_headerfile(headerfile_path,
                                                 features_to_use)
        # Generate the features
        if DISCO_INSTALLED and USE_DISCO:
            # Featurize in parallel
            print("FEATURIZING - USING DISCO")
            fname_features_data_dict = (
                parallel_processing.featurize_in_parallel(
                    headerfile_path=headerfile_path, zipfile_path=zipfile_path,
                    features_to_use=features_to_use, is_test=is_test,
                    custom_script_path=custom_script_path,
                    meta_features=fname_metadata_dict))
            objects = []
            for k, v in fname_features_data_dict.items():
                if k in fname_metadata_dict:
                    v = dict(list(v.items()) +
                             list(fname_metadata_dict[k].items()))
                objects.append(v)
        else:
            # Featurize serially
            print("FEATURIZING - NOT USING DISCO")
            objects = extract_serial(
                headerfile_path, zipfile_path, features_to_use,
                custom_script_path, is_test, USE_DISCO,
                already_featurized, in_docker_container, uploads_folder,
                fname_class_dict, fname_class_science_features_dict,
                fname_metadata_dict)
            return objects


def featurize_tsdata_object(path_to_csv, short_fname, custom_script_path,
                            fname_class_dict, fname_metadata_dict,
                            features_to_use):
    """

    """
    # Generate general/cadence-related TS features, if to be used
    if len(set(features_to_use) & set(cfg.features_list)) > 0:
        timeseries_features = (
            lc_tools.generate_timeseries_features(
                path_to_csv,
                classname=fname_class_dict[short_fname],
                sep=','))
    else:
        timeseries_features = {}
    # Generate TCP TS features, if to be used
    if len(
            set(features_to_use) &
            set(cfg.features_list_science)) > 0:
        from .TCP.Software.ingest_tools import \
            generate_science_features
        science_features = generate_science_features.generate(
            path_to_csv=path_to_csv)
    else:
        science_features = {}
    # Generate custom features, if any
    if custom_script_path not in (None, "None",
                                  False, "False"):
        custom_features = cft.generate_custom_features(
            custom_script_path=custom_script_path,
            path_to_csv=path_to_csv,
            features_already_known=dict(
                list(timeseries_features.items()) +
                list(science_features.items())))[0]
    else:
        custom_features = {}
    # Combine all features into single dict
    all_features = dict(
        list(timeseries_features.items()) +
        list(science_features.items()) +
        list(custom_features.items()))
    return all_features


def remove_unzipped_files(all_fnames, directory):
    """

    """
    for fname in all_fnames:
        path_to_csv = os.path.join(
            directory, os.path.join("unzipped", fname))
        if os.path.isfile(path_to_csv):
            os.remove(path_to_csv)


def extract_serial(headerfile_path, zipfile_path, features_to_use,
                   custom_script_path, is_test, USE_DISCO,
                   already_featurized, in_docker_container, uploads_folder,
                   fname_class_dict, fname_class_science_features_dict,
                   fname_metadata_dict):
    """Generate TS features serially.

    """
    objects = []
    zipfile = tarfile.open(zipfile_path)
    zipfile.extractall(path=os.path.join(uploads_folder, "unzipped"))
    all_fnames = zipfile.getnames()
    num_objs = len(fname_class_dict)
    zipfile_name = zipfile_path.split("/")[-1]
    count = 0
    print("Generating science features...")
    # Loop through time-series files and generate features for each
    for fname in sorted(all_fnames):
        short_fname = shorten_fname(fname)
        path_to_csv = os.path.join(
            uploads_folder, os.path.join("unzipped", fname))
        if os.path.isfile(path_to_csv):
            print("Extracting features for", fname, "-", count,
                  "of", num_objs)
            all_features = featurize_tsdata_object(
                path_to_csv, short_fname, custom_script_path, fname_class_dict,
                fname_metadata_dict,  features_to_use)
            # Add any meta features from header file
            if short_fname in fname_metadata_dict:
                all_features = dict(
                    list(all_features.items()) +
                    list(fname_metadata_dict[short_fname].items()))
            fname_class_science_features_dict[
                short_fname]['features'] = all_features
            objects.append(
                fname_class_science_features_dict[
                    short_fname]['features'])
            objects[-1]['class'] = fname_class_dict[short_fname]
            count += 1
            if is_test and count > 2:
                break
        else:
            pass
    print("Done.")
    remove_unzipped_files(all_fnames, uploads_folder)
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


def write_features_to_disk(objects, featureset_id, features_folder,
                           features_to_use, in_docker_container):
    """

    """
    features_extracted = list(objects[-1].keys())
    if "class" in features_extracted: features_extracted.remove("class")
    features_to_plot = determine_feats_to_plot(features_extracted)

    with open(os.path.join(
        ("/tmp" if in_docker_container else features_folder),
        "%s_features.csv" % featureset_id), 'w') as f, open(os.path.join(
        ("/tmp" if in_docker_container else features_folder),
        "%s_features_with_classes.csv" % featureset_id), 'w') as f2:
        write_column_titles(f, f2, features_extracted, features_to_use,
                            features_to_plot)
        class_count, num_used, num_held_back = count_classes(objects)
        print("class_count:", class_count)
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
                            if type(obj[feat]) == str and obj[feat] != "None":
                                line.append(obj[feat])
                            elif (type(obj[feat]) == type(None)
                                  or obj[feat] == "None"):
                                line.append(str(0.0))
                            else:
                                line.append(str(obj[feat]))
                            if feat in features_to_plot and numobjs < 300:
                                if type(obj[feat]) == str and obj[feat] != "None":
                                    line2.append(obj[feat])
                                elif (type(obj[feat]) == type(None)
                                      or obj[feat] == "None"):
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
    joblib.dump(classes, os.path.join(
        ("/tmp" if in_docker_container else features_folder),
        "%s_classes.pkl" % featureset_id), compress=3)
    print("Done.")


def featurize(
        headerfile_path, zipfile_path, features_to_use=[],
        featureset_id="unknown", is_test=False, USE_DISCO=True,
        already_featurized=False, custom_script_path=None,
        in_docker_container=False):
    """Generate features for labeled time series data.

    Features are saved to the file given by
    ``"%s_features.csv" % featureset_id``
    and a list of corresponding classes is saved to the file given by
    ``"%s_classes.pkl" % featureset_id``
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
    USE_DISCO : bool, optional
        Boolean indicating whether to featurize in parallel using Disco.
        Defaults to True.
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
    # Set appropriate directory paths
    if in_docker_container:
        features_folder = "/Data/features/"
        uploads_folder = "/Data/flask_uploads/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER

    # Generate features for each TS object
    objects = generate_features(
        headerfile_path, zipfile_path, features_to_use,
        custom_script_path, is_test, USE_DISCO, already_featurized,
        in_docker_container, uploads_folder)

    write_features_to_disk(objects, featureset_id, features_folder,
                           features_to_use, in_docker_container)
    # Clean up
    if not in_docker_container:
        os.remove(os.path.join(
            features_folder, "%s_features_with_classes.csv" % featureset_id))
    os.remove(headerfile_path)
    if zipfile_path is not None:
        os.remove(zipfile_path)
    return "Featurization of timeseries data complete."
