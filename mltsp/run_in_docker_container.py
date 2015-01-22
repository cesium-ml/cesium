from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import *
from subprocess import Popen, PIPE, call, check_call
import uuid
import pickle
import shutil
#import dockerpy
import uuid
import sys
import os
import rethinkdb as r

from . import cfg


def featurize_in_docker_container(
        headerfile_path, zipfile_path, features_to_use, featureset_key, 
        is_test, already_featurized, custom_script_path):
    """Generate TS data features inside a Docker container.
    
    Spins up a Docker container in which the 
    build_rf_model.featurize() method is called, and the resulting 
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
    #unique name for docker container for later cp and rm commands
    container_name = str(uuid.uuid4())[:10]
    path_to_tmp_dir = os.path.join("/tmp", container_name)
    os.mkdir(path_to_tmp_dir)
    
    # copy relevant data files into temp directory on host to be mounted 
    # into container:
    if os.path.isfile(str(headerfile_path)):
        status_code = call(
            ["cp", headerfile_path, "%s/%s" % 
                (path_to_tmp_dir, headerfile_path.split("/")[-1])])
        arguments["headerfile_path"] = os.path.join(
            "/home/mltsp/copied_data_files", headerfile_path.split("/")[-1])
    if os.path.isfile(str(zipfile_path)):
        status_code = call(
            ["cp", zipfile_path, "%s/%s" % 
                (path_to_tmp_dir, zipfile_path.split("/")[-1])])
        arguments["zipfile_path"] = os.path.join(
            "/home/mltsp/copied_data_files", zipfile_path.split("/")[-1])
    if os.path.isfile(str(custom_script_path)):
        status_code = call(
            ["cp", custom_script_path, "%s/%s" %
                (path_to_tmp_dir, custom_script_path.split("/")[-1])])
        arguments["custom_script_path"] = os.path.join(
            "/home/mltsp/copied_data_files", custom_script_path.split("/")[-1])

    arguments["path_map"] = {path_to_tmp_dir,"/home/mltsp/copied_data_files"}
    with open("%s/function_args.pkl"%path_to_tmp_dir, "wb") as f:
        pickle.dump(arguments,f)

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
        # kill and remove the container
        cmd = ["docker", "rm", "-f", container_name]
        status_code = call(cmd)#, stdout=PIPE, stderr=PIPE)
        print("Docker container deleted.")
    return "Featurization complete."


def build_model_in_docker_container(
    featureset_name, featureset_key, model_type):
    """Build classification model inside a Docker container.

    Spins up a Docker container in which the
    build_rf_model.build_model() routine is called, and the resulting
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

    # copy relevant data files into docker temp directory
    # on host to be mounted into container:
    arguments["path_map"] = {path_to_tmp_dir,"/home/mltsp/copied_data_files"}
    with open("%s/function_args.pkl"%path_to_tmp_dir, "wb") as f:
        pickle.dump(arguments,f)
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
            ("docker", "cp", "%s:/tmp/%s_%s.pkl"
                % (container_name, featureset_key, model_type)),
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
    
    # copy relevant data files into docker temp directory
    if os.path.isfile(str(newpred_file_path)):
        status_code = call(
            ["cp", newpred_file_path, 
                "%s/%s" % (path_to_tmp_dir, newpred_file_path.split("/")[-1])])
        arguments["newpred_file_path"] = os.path.join(
            "/home/mltsp/copied_data_files", newpred_file_path.split("/")[-1])
    if os.path.isfile(str(custom_features_script)):
        status_code = call(
            [
                "cp", custom_features_script, 
                "%s/%s" % (path_to_tmp_dir, 
                custom_features_script.split("/")[-1])])
        arguments["custom_features_script"] = os.path.join(
            "/home/mltsp/copied_data_files", 
            custom_features_script.split("/")[-1])
    if os.path.isfile(str(metadata_file)):
        status_code = call(
            [
                "cp", metadata_file, 
                "%s/%s" % (path_to_tmp_dir, metadata_file.split("/")[-1])])
        arguments["metadata_file"] = os.path.join(
            "/home/mltsp/copied_data_files", metadata_file.split("/")[-1])
    
    arguments["path_map"] = {path_to_tmp_dir,"/home/mltsp/copied_data_files"}
    with open("%s/function_args.pkl"%path_to_tmp_dir, "wb") as f:
        pickle.dump(arguments,f)
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
                            "type(pred_results_dict) != dict")
        print("Process complete.")
    except:
        raise
    finally:
        # delete temp directory and its contents
        shutil.rmtree(path_to_tmp_dir, ignore_errors=True)
        os.remove("/tmp/%s_pred_results.pkl"%prediction_entry_key)
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
