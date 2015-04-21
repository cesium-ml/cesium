from __future__ import print_function
from subprocess import Popen, PIPE, call, check_call
import uuid
import pickle
import shutil
import uuid
import sys
import os
import rethinkdb as r
import ntpath
from docker import Client
from . import cfg
import io
import tarfile
import tempfile


def docker_copy(docker_client, container_id, path, target="."):
    """Copy file from docker container to host machine.

    Parameters
    ----------
    docker_client : docker.Client object
        The connected Docker client.
    container_id : str
        ID of the container to copy from.
    path : str
        Path to the file in the container.
    target : str
        Folder where to put the file.

    """
    response = docker_client.copy(container_id, path)
    buffer = io.BytesIO()
    buffer.write(response.data)
    buffer.seek(0)
    tar = tarfile.open(fileobj=buffer, mode='r|')
    tar.extractall(path=target)


def copy_data_files_featurize_prep(args_dict):
    """Copy needed files into expected location for featurization.

    Parameters
    ----------
    args_dict : dict
        Dictionary of local variable names and associated values (produced
        by calling the built-in method `locals()`).

    Returns
    -------
    list of str
        List of paths (strings) to all copied/created temporary files to
        be removed upon completion of featurization.

    """
    tmp_files = []
    if os.path.isfile(str(args_dict['headerfile_path'])):
        copied_headerfile_path = os.path.join(
            args_dict['copied_data_dir'],
            ntpath.basename(args_dict['headerfile_path']))
        tmp_files.append(copied_headerfile_path)
        shutil.copy(args_dict['headerfile_path'], copied_headerfile_path)
        args_dict["headerfile_path"] = os.path.join(
            "/home/copied_data_files",
            ntpath.basename(args_dict['headerfile_path']))
    if os.path.isfile(str(args_dict['zipfile_path'])):
        copied_zipfile_path = os.path.join(
            args_dict['copied_data_dir'],
            ntpath.basename(args_dict['zipfile_path']))
        tmp_files.append(copied_zipfile_path)
        shutil.copy(args_dict['zipfile_path'], copied_zipfile_path)
        args_dict["zipfile_path"] = os.path.join(
            "/home/copied_data_files",
            ntpath.basename(args_dict['zipfile_path']))
    if os.path.isfile(str(args_dict['custom_script_path'])):
        copied_custom_script_path = os.path.join(
            args_dict['copied_data_dir'], "custom_feature_defs.py")
        tmp_files.append(copied_custom_script_path)
        shutil.copy(args_dict['custom_script_path'], copied_custom_script_path)
        args_dict["custom_script_path"] = os.path.join(
            "/home/copied_data_files", "custom_feature_defs.py")
        # Create __init__.py file so that custom feats script can be imported
        open(os.path.join(args_dict['copied_data_dir'], "__init__.py"),
             "w").close()
    args_dict["path_map"] = {args_dict['copied_data_dir']:
                             "/home/copied_data_files"}
    function_args_path = os.path.join(args_dict['copied_data_dir'],
                                      "function_args.pkl")
    tmp_files.append(function_args_path)
    with open(function_args_path, "wb") as f:
        pickle.dump(args_dict, f, protocol=2)

    return tmp_files


def spin_up_and_run_container(image_name, tmp_data_dir):
    """Spin up and run a Docker container.

    Parameters
    ----------
    image_name : str
        Name/tag of the Docker image to be used, e.g. "mltsp/featurize".
    tmp_dir : str
        Path to directory containing data files to be mounted into
        container.

    Returns
    -------
    tuple
       Two-element tuple containing docker.Client object, and the ID of
       the newly-created container (str).

    """
    # Instantiate Docker client
    client = Client(base_url='unix://var/run/docker.sock',
                    version='1.14')
    # Create container
    cont_id = client.create_container(
        image_name,
        volumes={"/home/mltsp": "",
                 "/home/copied_data_files": ""})["Id"]
    # Start container
    client.start(cont_id,
                 binds={cfg.PROJECT_PATH: {"bind": "/home/mltsp", "ro": True},
                        tmp_data_dir: {"bind": "/home/copied_data_files",
                                       "ro": True}})
    # Wait for process to complete
    client.wait(cont_id)
    stdout = client.logs(container=cont_id, stdout=True)
    stderr = client.logs(container=cont_id, stderr=True)
    print("\n\ndocker container stdout:\n\n", str(stdout),
          "\n\ndocker container stderr:\n\n", str(stderr), "\n\n")
    # Clean up unwanted copied files
    for fname in ["custom_feature_defs.py", "custom_feature_defs.pyc",
                  "__init__.pyc"]:
        fpath = os.path.join(cfg.TMP_CUSTOM_FEATS_FOLDER, fname)
        if os.path.exists(fpath):
            os.remove(fpath)
    return (client, cont_id)


def copy_results_files_featurize(featureset_key, client, cont_id):
    """Copy features results files from Docker container to host machine.

    Parameters
    ----------
    featureset_key : str
        Key/ID identifying the relevant feature set.
    client : docker.Client object
        docker.Client object
    cont_id : str
        ID of the relevant container.

    """
    # Copy resulting data files from container to host machine
    for file_suffix in ["features.csv", "features_with_classes.csv",
                        "classes.npy"]:
        path = "/tmp/%s_%s" % (featureset_key, file_suffix)
        docker_copy(client, cont_id, path, target=cfg.FEATURES_FOLDER)
        print(
            os.path.join(
                cfg.FEATURES_FOLDER,"%s_%s" % (featureset_key,
                                               file_suffix)),
            "copied to host machine.")
    # Move plot data file from features folder to Flask data folder
    shutil.copy2(
        os.path.join(
            cfg.FEATURES_FOLDER,
            "%s_features_with_classes.csv" % featureset_key),
        os.path.join(cfg.MLTSP_PACKAGE_PATH, "Flask/static/data"))
    os.remove(os.path.join(
        cfg.FEATURES_FOLDER,
        "%s_features_with_classes.csv" % featureset_key))


def featurize_in_docker_container(
        headerfile_path, zipfile_path, features_to_use, featureset_key,
        is_test, already_featurized, custom_script_path):
    """Generate TS data features inside a Docker container.

    Spins up a Docker container in which the
    featurize.featurize() method is called, and the resulting
    files are then copied to the host machine.

    Parameters
    ----------
    headerfile_path : str
        Path to the header file associated with TS data to be
        used for feature generation.
    zipfile_path : str
        Path to the tarball containing the individual time-series data
        files to be used for feature generation.
    features_to_use : list of str
        List of names of features to generate.
    featureset_key : str
        Feature set ID/RethinkDB entry key.
    is_test : bool
        Boolean indicating whether to run as a test, in which case only
        a small subset of the time-series data files will be used for
        feature generation.
    already_featurized : bool
        Boolean indicating whether `headerfile_path` already contains
        all of the features to be included in new feature set, in
        which case no feature generation is performed and no TS data
        files are required.
    custom_script_path : str
        Path to custom feature definitions script, or None.

    Returns
    -------
    str
        Human-readable success message.

    """
    copied_data_dir = tempfile.mkdtemp()
    args_dict = locals()
    tmp_files = copy_data_files_featurize_prep(args_dict)
    try:
        client, cont_id = spin_up_and_run_container("mltsp/featurize",
                                                    copied_data_dir)
        copy_results_files_featurize(featureset_key, client, cont_id)
        print("Process complete.")
    except Exception as e:
        cont_id = None
        raise(e)
    finally:
        # Delete temporary files
        for tmp_file_path in tmp_files:
            try:
                os.remove(tmp_file_path)
            except Exception as e:
                print(e)
        shutil.rmtree(copied_data_dir, ignore_errors=True)
        # Kill and remove Docker container
        if cont_id and cont_id is not None:
            client.remove_container(container=cont_id, force=True)
        else:
            print('Docker instance never started successfully')

        print("Docker container deleted.")
    return "Featurization complete."


def build_model_in_docker_container(
    featureset_name, featureset_key, model_type):
    """Build classification model inside a Docker container.

    Spins up a Docker container in which the
    build_model.build_model() routine is called, and the resulting
    model is then copied to the host machine.

    Parameters
    ----------
    featureset_name : str
        Name of the feature set from which to create the new model.
    featureset_key : str
        Feature set key/ID, also the RethinkDB 'features' table entry
        key associated with the feature set to be used.
    model_type : str
        Abbreviation of type of model to create (e.g. "RF").

    Returns
    -------
    str
        Human-readable success message.

    """
    copied_data_dir = tempfile.mkdtemp()
    args_dict = locals()

    tmp_files = []
    args_dict["path_map"] = {copied_data_dir, "/home/copied_data_files"}
    function_args_path = os.path.join(copied_data_dir, "function_args.pkl")
    tmp_files.append(function_args_path)
    with open(function_args_path, "wb") as f:
        pickle.dump(args_dict, f, protocol=2)
    try:
        client, cont_id = spin_up_and_run_container("mltsp/build_model",
                                                    copied_data_dir)
        # copy model object produced in Docker container to host
        path = "/tmp/%s_%s.pkl" % (featureset_key, model_type)
        docker_copy(client, cont_id, path, target=cfg.MODELS_FOLDER)
        print("Process complete.")
    except:
        raise
    finally:
        # delete temp files
        for tmp_file in tmp_files:
            try:
                os.remove(tmp_file)
            except Exception as e:
                print(e)
        shutil.rmtree(copied_data_dir, ignore_errors=True)
        # Kill and remove the container
        client.remove_container(container=cont_id, force=True)

    return "Model creation complete. Click the Predict tab to start using it."


def copy_data_files_predict_prep(args_dict):
    """Copy needed files into expected location for prediction.

    Parameters
    ----------
    args_dict : dict
        Dictionary of local variable names and associated values (produced
        by calling the built-in method `locals()`).

    Returns
    -------
    list of str
        List of paths (strings) to all copied/created temporary files to
        be removed upon completion of prediction.

    """
    tmp_files = []
    if os.path.isfile(str(args_dict["newpred_file_path"])):
        copied_newpred_file_path = os.path.join(
            args_dict["copied_data_dir"],
            ntpath.basename(args_dict["newpred_file_path"]))
        tmp_files.append(copied_newpred_file_path)
        shutil.copy(args_dict["newpred_file_path"], copied_newpred_file_path)
        args_dict["newpred_file_path"] = os.path.join(
            "/home/copied_data_files",
            ntpath.basename(args_dict["newpred_file_path"]))
    if os.path.isfile(str(args_dict["custom_features_script"])):
        copied_custom_script_path = os.path.join(
            args_dict["copied_data_dir"], "custom_feature_defs.py")
        tmp_files.append(copied_custom_script_path)
        shutil.copy(args_dict["custom_features_script"],
                    copied_custom_script_path)
        args_dict["custom_features_script"] = os.path.join(
            "/home/copied_data_files", "custom_feature_defs.py")
        # Create __init__.py file so that custom feats script can be imported
        open(os.path.join(args_dict['copied_data_dir'], "__init__.py"),
             "w").close()
    if os.path.isfile(str(args_dict["metadata_file"])):
        copied_metadata_file_path = os.path.join(
            args_dict["copied_data_dir"],
            ntpath.basename(args_dict["metadata_file"]))
        tmp_files.append(copied_metadata_file_path)
        shutil.copy(args_dict["metadata_file"], copied_metadata_file_path)
        args_dict["metadata_file"] = os.path.join(
            "/home/copied_data_files",
            ntpath.basename(args_dict["metadata_file"]))

    args_dict["path_map"] = {args_dict["copied_data_dir"]:
                             "/home/copied_data_files"}
    function_args_path = os.path.join(args_dict["copied_data_dir"],
                                      "function_args.pkl")
    tmp_files.append(function_args_path)
    with open(function_args_path, "wb") as f:
        pickle.dump(args_dict, f, protocol=2)
    return tmp_files


def predict_in_docker_container(
        newpred_file_path, model_name, model_type, prediction_entry_key,
        featset_key, sep=",", n_cols_html_table=5,
        features_already_extracted=None, metadata_file=None,
        custom_features_script=None):
    """Generate features and perform classification in Docker container.

    Spins up a Docker container in which the
    predict_class.predict() method is called, and the resulting
    files are then copied to the host machine.

    Parameters
    ----------
    newpred_file_path : str
        Path to file containing time series data for featurization and
        prediction.
    model_name : str
        Name of the model to be used.
    model_type : str
        Abbreviation of the model type (e.g. "RF").
    prediction_entry_key : str
        Prediction entry RethinkDB key.
    featset_key : str
        ID of feature set/model to use in prediction.
    sep : str, optional
        Delimiting character in time series data files. Defaults to
        comma ",".
    n_cols_html_table : int, optional
        Number of most probable predicted classes to include in HTML
        table output. Defaults to 5.
    features_already_extracted : dict, optional
        Dictionary of previously-generated features. Defaults to None.
    metadata_file : str, optional
        Path to associated metadata file, if any. Defaults to None.

    Returns
    -------
    dict
        Dictionary containing prediction results.

    """
    copied_data_dir = tempfile.mkdtemp()
    args_dict = locals()
    tmp_files = copy_data_files_predict_prep(args_dict)
    try:
        client, cont_id = spin_up_and_run_container("mltsp/predict",
                                                    copied_data_dir)
        # copy all necessary files produced in docker container to host
        path = "/tmp/%s_pred_results.pkl" % prediction_entry_key
        docker_copy(client, cont_id, path, target="/tmp")
        with open("/tmp/%s_pred_results.pkl" % prediction_entry_key, "rb") as f:
            pred_results_dict = pickle.load(f)
        if type(pred_results_dict) != dict:
            raise Exception("run_in_docker_container.predict_in_docker_" +
                            "container() error message - " +
                            "type(pred_results_dict) != dict (%s)" % \
                            str(type(pred_results_dict)))
    except:
        raise
    finally:
        # delete temp files
        for tmp_file in tmp_files:
            try:
                os.remove(tmp_file)
            except Exception as e:
                print(e)
        shutil.rmtree(copied_data_dir, ignore_errors=True)
        # Kill and remove the container
        client.remove_container(container=cont_id, force=True)
        print("Docker container deleted.")

    return pred_results_dict


def disco_test():
    """Test Disco functionality inside Docker container.

    """
    try:
        # Instantiate Docker client
        client = Client(base_url='unix://var/run/docker.sock',
                        version='1.14')
        # Create container
        cont_id = client.create_container(
            "disco_test",
            volumes={"/home/mltsp": ""})["Id"]
        print(cont_id)
        # Start container
        client.start(cont_id,
                     binds={cfg.PROJECT_PATH: {"bind": "/home/mltsp",
                                               "ro": True}})
        # Wait for process to complete
        client.wait(cont_id)
        stdouterr = client.logs(container=cont_id, stdout=True, stderr=True)
        print("\n\ndocker container stdout/err:\n\n", str(stdouterr), "\n\n")
        print("Process complete.")
    except:
        raise
    finally:
        # Kill and remove the container
        client.remove_container(container=cont_id, force=True)
        print("Docker container deleted.")

    return "Test complete."
