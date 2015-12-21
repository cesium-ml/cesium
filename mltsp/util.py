import ast
import errno
import os
import subprocess
import tarfile
import tempfile
import zipfile

import numpy as np

try:
    import docker
    dockerpy_installed = True
except ImportError:
    dockerpy_installed = False
import requests


def make_list(x):
    import collections
    if isinstance(x, collections.Iterable) and not isinstance(x, str):
        return x
    else:
        return [x,]


def shorten_fname(file_path):
    """Extract the name of a file (omitting directory names and extensions)."""
    return os.path.splitext(os.path.basename(file_path))[0]


def get_docker_client(version='1.14'):
    """Connect to Docker if available and return a client.

    Parameters
    ----------
    version : str, optional
        Protocol version.

    Returns
    -------
    docker.Client
        Docker client.

    Raises
    ------
    RuntimeError
        If Docker cannot be contacted or contains no images.
    """
    docker_socks = ['/var/run/docker.sock', '/docker.sock']

    if not dockerpy_installed:
        raise RuntimeError('docker-py required for docker operations')

    # First try to auto detect docker parameters from environment
    try:
        args = docker.utils.kwargs_from_env(assert_hostname=False)
        args.update(dict(version=version))
        cli = docker.Client(**args)
        cli.info()
        return cli
    except requests.exceptions.ConnectionError:
        pass

    for sock in docker_socks:
        if os.path.exists(sock):
            try:
                cli = docker.Client(base_url='unix://{}'.format(sock), version=version)
                cli.info()
                return cli
            except requests.exceptions.ConnectionError:
                pass

    raise RuntimeError('Could not locate a usable docker socket')


def docker_images_available():
    """Return boolean indicating whether Docker images are present."""
    if not dockerpy_installed:
        return False

    try:
        cli = get_docker_client()
        img_ids = cli.images(quiet=True)
    except RuntimeError:
        return False

    return len(img_ids) > 0


def is_running_in_docker():
    """Return bool indicating whether running in a Docker container."""
    if not os.path.exists("/proc/1/cgroup"):
        return False
    proc = subprocess.Popen(["cat", "/proc/1/cgroup"], stdout=subprocess.PIPE)
    output = proc.stdout.read()
    if "/docker/" in str(output):
        in_docker_container = True
    else:
        in_docker_container = False
    return in_docker_container


def cast_model_params(model_type, model_params, params_to_optimize=None):
    """Cast model parameter strings to expected types.

    Modifies `model_params` dict in place.

    Parameters
    ----------
    model_type : str
        Name of model.
    model_params : dict
        Dictionary whose keys are model parameter names and values are
        string representations of corresponding values, which will be cast
        to desired types in place, as specified in `sklearn_models` module.
    params_to_optimize : list of str, optional
        List of parameter names that are formatted for hyperparameter
        optimization.

    """
    from .ext.sklearn_models import model_descriptions
    # Find relevant model description
    for entry in model_descriptions:
        if entry["name"] == model_type:
            params_list = entry["params"]
            break
    try:
        params_list
    except NameError:
        raise ValueError("model_type not in list of allowable models.")
    # Iterate through params from HTML form and cast to expected types
    for k, v in model_params.items():
        # Empty string or "None" goes to `None`
        if v in ["None", ""]:
            model_params[k] = None
            continue
        # Find relevant parameter description
        for p in params_list:
            if p["name"] == k:
                param_entry = p
                break
        dest_types_list = make_list(param_entry["type"])
        for dest_type in dest_types_list:
            if dest_type is not str:
                try:
                    if isinstance(ast.literal_eval(model_params[k]),
                                  dest_type) or \
                        (params_to_optimize and k in params_to_optimize and \
                         isinstance(ast.literal_eval(model_params[k]), list) \
                         and (type(x) in dest_types_list for x in \
                              ast.literal_eval(model_params[k]))):
                        model_params[k] = ast.literal_eval(model_params[k])
                        break
                except ValueError:
                    pass
        if isinstance(model_params[k], str) and str not in dest_types_list:
            raise(ValueError("Model parameter cannot be cast to expected "
                             "type."))


def remove_files(paths):
    """Remove specified files from disk."""
    paths = make_list(paths)
    for path in paths:
        try:
            os.remove(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            else:
                pass


def extract_data_archive(archive_path, extract_dir=None):
    """Extract zip- or tarfile of time series file and return file paths.
    
    Parameters
    ----------
    archive_path : str
        Path to archive to be extracted.

    extract_dir : str, optional
        Directory into which files are to be extracted. If None, a temporary
        directory is created.

    Returns
    -------
    list of str
        List of full paths to extracted files.
    """
    if extract_dir is None:
        extract_dir = tempfile.mkdtemp()

    if tarfile.is_tarfile(archive_path):
        archive = tarfile.open(archive_path)
        archive.extractall(path=extract_dir)
        all_paths = [os.path.join(extract_dir, f) for f in archive.getnames()]
    elif zipfile.is_zipfile(archive_path):
        archive = zipfile.ZipFile(archive_path)
        archive.extractall(path=extract_dir)
        all_paths = [os.path.join(extract_dir, f) for f in archive.namelist()]
    else:
        raise ValueError('{} is not a valid zip- or '
                         'tarfile.'.format(archive_path))
    file_paths = [f for f in all_paths if not os.path.isdir(f)]
    archive.close()
    return file_paths
