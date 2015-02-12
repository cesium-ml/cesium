from subprocess import Popen, PIPE, call, check_call
import uuid
import pickle
import shutil
#import dockerpy
import uuid
import sys
import os
import rethinkdb as r
import ntpath

from . import cfg


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
    arguments = locals()
    # unique name for docker container for later cp and rm commands:
    container_name = str(uuid.uuid4())[:10]
    path_to_tmp_dir = os.path.join("/tmp", container_name)
    os.mkdir(path_to_tmp_dir)
    copied_data_dir = os.path.join(cfg.PROJECT_PATH, "copied_data_files")
    tmp_files = []

    # copy relevant data files into temp directory on host to be mounted
    # into container:
    if os.path.isfile(str(headerfile_path)):
        copied_headerfile_path = os.path.join(
            copied_data_dir, ntpath.basename(headerfile_path))
        tmp_files.append(copied_headerfile_path)
        shutil.copy(headerfile_path, copied_headerfile_path)
        arguments["headerfile_path"] = os.path.join(
            "/home/mltsp/copied_data_files", ntpath.basename(headerfile_path))
    if os.path.isfile(str(zipfile_path)):
        copied_zipfile_path = os.path.join(copied_data_dir,
                                           ntpath.basename(zipfile_path))
        tmp_files.append(copied_zipfile_path)
        shutil.copy(zipfile_path, copied_zipfile_path)
        arguments["zipfile_path"] = os.path.join(
            "/home/mltsp/copied_data_files", ntpath.basename(zipfile_path))
    if os.path.isfile(str(custom_script_path)):
        copied_custom_script_path = os.path.join(
            os.path.join(
                cfg.MLTSP_PACKAGE_PATH, "custom_feature_scripts"),
            "custom_feature_defs.py")
        tmp_files.append(copied_custom_script_path)
        shutil.copy(custom_script_path, copied_custom_script_path)
        arguments["custom_script_path"] = ("/home/mltsp/mltsp/"
                                           "custom_feature_scripts/"
                                           "custom_feature_defs.py")

    arguments["path_map"] = {copied_data_dir,"/home/mltsp/copied_data_files"}
    function_args_path = os.path.join(copied_data_dir, "function_args.pkl")
    tmp_files.append(function_args_path)
    with open(function_args_path, "wb") as f:
        pickle.dump(arguments, f, protocol=2)
    try:
        # run the docker container
        cmd = ["docker", "run",
                "-v", "%s:/home/mltsp" % cfg.PROJECT_PATH,
                "-v", "%s:%s" % (cfg.FEATURES_FOLDER, "/Data/features"),
                "-v", "%s:%s" % (cfg.UPLOAD_FOLDER, "/Data/flask_uploads"),
                "-v", "%s:%s" % (cfg.MODELS_FOLDER, "/Data/models"),
                "--name=%s" % container_name,
                "mltsp/featurize"]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print("\n\ndocker container stdout:\n\n", stdout, \
            "\n\ndocker container stderr:\n\n", stderr, "\n\n")

        # copy all necessary files produced in docker container to host
        for file_suffix in [
            "features.csv", "features_with_classes.csv", "classes.pkl"]:
            cmd = [
                "docker", "cp", "%s:/tmp/%s_%s" %
                    (container_name, featureset_key, file_suffix),
                cfg.FEATURES_FOLDER]
            status_code = call(cmd, stdout=PIPE, stderr=PIPE)
            print((
                os.path.join(
                    cfg.FEATURES_FOLDER,"%s_%s"%(featureset_key, file_suffix)),
                "copied to host machine - status code %s" % str(status_code)))

        shutil.copy2(
            os.path.join(
                cfg.FEATURES_FOLDER,
                "%s_features_with_classes.csv"%featureset_key),
            os.path.join(cfg.MLTSP_PACKAGE_PATH,"Flask/static/data"))
        os.remove(os.path.join(
            cfg.FEATURES_FOLDER,
            "%s_features_with_classes.csv"%featureset_key))
        print("Process complete.")
    except:
        raise
    finally:
        # delete temp directory and its contents
        shutil.rmtree(path_to_tmp_dir, ignore_errors=True)
        for tmp_file_path in tmp_files:
            try:
                os.remove(tmp_file_path)
            except Exception as e:
                print(e)
        # kill and remove the container
        cmd = ["docker", "rm", "-f", container_name]
        status_code = call(cmd)#, stdout=PIPE, stderr=PIPE)
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
    arguments = locals()
    #unique name for docker container for later cp and rm commands
    container_name = str(uuid.uuid4())[:10]
    path_to_tmp_dir = os.path.join("/tmp", container_name)
    os.mkdir(path_to_tmp_dir)
    copied_data_dir = os.path.join(cfg.PROJECT_PATH, "copied_data_files")

    # copy relevant data files into docker temp directory
    # on host to be mounted into container:
    tmp_files = []
    arguments["path_map"] = {copied_data_dir,"/home/mltsp/copied_data_files"}
    function_args_path = os.path.join(copied_data_dir, "function_args.pkl")
    tmp_files.append(function_args_path)
    with open(function_args_path, "wb") as f:
        pickle.dump(arguments, f, protocol=2)
    try:
        # run the docker container
        cmd = ["docker", "run",
                "-v", "%s:/home/mltsp" % cfg.PROJECT_PATH,
                "-v", "%s:%s" % (cfg.FEATURES_FOLDER, "/Data/features"),
                "-v", "%s:%s" % (cfg.UPLOAD_FOLDER, "/Data/flask_uploads"),
                "-v", "%s:%s" % (cfg.MODELS_FOLDER, "/Data/models"),
                "--name=%s" % container_name,
                "mltsp/build_model"]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print("\n\ndocker container stdout:\n\n", stdout, \
              "\n\ndocker container stderr:\n\n", stderr, "\n\n")

        # copy all necessary files produced in Docker container to host
        cmd = [
            "docker", "cp",
            "%s:/tmp/%s_%s.pkl" % (container_name, featureset_key, model_type),
            cfg.MODELS_FOLDER]
        #status_code = call(cmd, stdout=PIPE, stderr=PIPE)
        #print os.path.join(
        #    cfg.MODELS_FOLDER,"%s_%s.pkl"%(featureset_key, model_type)),
        #    "copied to host machine - status code %s" % str(status_code)
        check_call(cmd)
        print(os.path.join(
            cfg.MODELS_FOLDER,
            "%s_%s.pkl"%(featureset_key,model_type)), "copied to host machine.")
        print("Process complete.")
    except:
        raise
    finally:
        # delete temp directory and its contents on host machine
        shutil.rmtree(path_to_tmp_dir, ignore_errors=True)
        for tmp_file in tmp_files:
            try:
                os.remove(tmp_file)
            except Exception as e:
                print(e)
        # kill and remove the container
        cmd = ["docker", "rm", "-f", container_name]
        status_code = call(cmd)#, stdout=PIPE, stderr=PIPE)
        print("Docker container deleted.")

    return "Model creation complete. Click the Predict tab to start using it."


def predict_in_docker_container(
    newpred_file_path, project_name, model_name, model_type,
    prediction_entry_key, featset_key, sep=",", n_cols_html_table=5,
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
    project_name : str
        Name of the project associated with the model to be used.
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
    arguments = locals()
    container_name = str(uuid.uuid4())[:10]
    path_to_tmp_dir = os.path.join("/tmp", container_name)
    os.mkdir(path_to_tmp_dir)
    copied_data_dir = os.path.join(cfg.PROJECT_PATH, "copied_data_files")
    tmp_files = []
    # copy relevant data files into docker temp directory
    if os.path.isfile(str(newpred_file_path)):
        copied_newpred_file_path = os.path.join(
            copied_data_dir, ntpath.basename(newpred_file_path))
        tmp_files.append(copied_newpred_file_path)
        shutil.copy(newpred_file_path, copied_newpred_file_path)
        arguments["newpred_file_path"] = os.path.join(
            "/home/mltsp/copied_data_files", ntpath.basename(newpred_file_path))
    if os.path.isfile(str(custom_features_script)):
        copied_custom_script_path = os.path.join(
            os.path.join(cfg.MLTSP_PACKAGE_PATH,"custom_feature_scripts"),
            "custom_feature_defs.py")
        tmp_files.append(copied_custom_script_path)
        shutil.copy(custom_features_script, copied_custom_script_path)
        arguments["custom_features_script"] = ("/home/mltsp/mltsp/"
                                               "custom_feature_scripts/"
                                               "custom_feature_defs.py")
    if os.path.isfile(str(metadata_file)):
        copied_metadata_file_path = os.path.join(
            copied_data_dir, ntpath.basename(metadata_file))
        tmp_files.append(copied_metadata_file_path)
        shutil.copy(metadata_file, copied_metadata_file_path)
        arguments["metadata_file"] = os.path.join(
            "/home/mltsp/copied_data_files", ntpath.basename(metadata_file))

    arguments["path_map"] = {copied_data_dir,"/home/mltsp/copied_data_files"}
    function_args_path = os.path.join(copied_data_dir, "function_args.pkl")
    tmp_files.append(function_args_path)
    with open(function_args_path, "wb") as f:
        pickle.dump(arguments, f, protocol=2)
    try:
        cmd = ["docker", "run",
                "-v", "%s:/home/mltsp"%cfg.PROJECT_PATH,
                "-v", "%s:%s"%(cfg.FEATURES_FOLDER,"/Data/features"),
                "-v", "%s:%s"%(cfg.UPLOAD_FOLDER,"/Data/flask_uploads"),
                "-v", "%s:%s"%(cfg.MODELS_FOLDER,"/Data/models"),
                "--name=%s"%container_name,
                "mltsp/predict"]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print("\n\ndocker container stdout:\n\n", stdout, \
              "\n\ndocker container stderr:\n\n", stderr, "\n\n")

        # copy all necessary files produced in docker container to host
        cmd = [
            "docker", "cp",
            (
                "%s:/tmp/%s_pred_results.pkl" %
                (container_name, prediction_entry_key)),
            "/tmp"]
        status_code = call(cmd, stdout=PIPE, stderr=PIPE)
        print("/tmp/%s_pred_results.pkl"%prediction_entry_key, \
              "copied to host machine - status code %s" % str(status_code))
        with open("/tmp/%s_pred_results.pkl"%prediction_entry_key, "rb") as f:
            pred_results_dict = pickle.load(f)
        if type(pred_results_dict) != dict:
            print(("run_in_docker_container.predict_in_docker_container() - " +
                   "type(pred_results_dict) ="), type(pred_results_dict))
            print("pred_results_dict:", pred_results_dict)
            raise Exception("run_in_docker_container.predict_in_docker_" +
                            "container() error message - " +
                            "type(pred_results_dict) != dict (%s)" % \
                            str(type(pred_results_dict)))
        print("Process complete.")
    except:
        raise
    finally:
        # delete temp directory and its contents
        shutil.rmtree(path_to_tmp_dir, ignore_errors=True)
        for tmp_file in tmp_files:
            try:
                os.remove(tmp_file)
            except Exception as e:
                print(e)
        cmd = ["docker", "rm", "-f", container_name]
        status_code = call(cmd)#, stdout=PIPE, stderr=PIPE)
        print("Docker container deleted.")

    return pred_results_dict


def disco_test():
    """Test Disco functionality inside Docker container.

    """
    #unique name for docker container for later cp and rm commands
    container_name = str(uuid.uuid4())[:10]

    try:
        # run the docker container
        cmd = ["docker", "run",
                "-v", "%s:/home/mltsp" % cfg.PROJECT_PATH,
                "--name=%s" % container_name,
                "disco_test"]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print("\n\ndocker container stdout:\n\n", stdout, "\n\ndocker container stderr:\n\n", stderr, "\n\n")
        print("Process complete.")
    except:
        raise
    finally:

        # kill and remove the container
        cmd = ["docker", "rm", "-f", container_name]
        status_code = call(cmd)#, stdout=PIPE, stderr=PIPE)
        print("Docker container deleted.")

    return "Test complete."
