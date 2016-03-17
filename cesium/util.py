import ast
import contextlib
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


__all__ = ['make_list', 'shorten_fname', 'get_docker_client',
           'docker_images_available', 'is_running_in_docker',
           'check_model_param_types', 'remove_files', 'extract_time_series',
           'robust_literal_eval', 'warn_defaultdict']


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


def check_model_param_types(model_type, model_params, all_as_lists=False):
    """Cast model parameter strings to expected types.

    Modifies `model_params` dict in place.

    Parameters
    ----------
    model_type : str
        Name of model.
    model_params : dict
        Dictionary containing model parameters to be checked against expected
        types.
    all_as_lists : bool, optional
        Boolean indicating whether `model_params` values are wrapped in lists,
        as in the case of parameter grids for optimization.

    Raises
    ------
    ValueError
        Raises ValueError if parameter(s) are not of expected type.

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
    # Iterate through params and check against expected types
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
        if not all_as_lists:
            v = [v,]
        if all(type(x) in dest_types_list or x is None for x in v):
            break
        else:
            raise ValueError("Model parameter is not of expected type "
                             "(parameter {} ({}) is of type {}, which is not "
                             "in list of expected types ({}).".format(
                                 param_entry["name"], v, type(v),
                                 dest_types_list))


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


@contextlib.contextmanager
def extract_time_series(data_path, cleanup_archive=True, cleanup_files=False,
                        extract_dir=None):
    """Extract zip- or tarfile of time series file and return file paths.

    If the given file is not a tar- or zipfile then it is treated as a single
    time series filepath.

    Parameters
    ----------
    data_path : str
        Path to data archive or single data file.

    cleanup_archive : bool, optional
        Boolean specifying whether to delete the original archive (if
        applicable). Defaults to True.

    cleanup_files : bool, optional
        Boolean specifying whether to delete the extracted files when exiting
        the given context. Defaults to False.

    extract_dir : str, optional
        Directory into which files are to be extracted (if applicable). If
        None, a temporary directory is created.

    Yields
    ------
    list of str
        List of full paths to time series files.
    """
    if extract_dir is None:
        extract_dir = tempfile.mkdtemp()

    if tarfile.is_tarfile(data_path):
        archive = tarfile.open(data_path)
        archive.extractall(path=extract_dir)
        all_paths = [os.path.join(extract_dir, f) for f in archive.getnames()]
    elif zipfile.is_zipfile(data_path):
        archive = zipfile.ZipFile(data_path)
        archive.extractall(path=extract_dir)
        all_paths = [os.path.join(extract_dir, f) for f in archive.namelist()]
    else:
        archive = None
        all_paths = [data_path]

    if archive:
        archive.close()
        if cleanup_archive:
            remove_files(data_path)

    file_paths = [f for f in all_paths if not os.path.isdir(f)]
    try:
        yield file_paths
    finally:
        if cleanup_files:
            remove_files(file_paths)


def robust_literal_eval(val):
    """Call `ast.literal_eval` without raising `ValueError`.

    Parameters
    ----------
    val : str
        String literal to be evaluated.

    Returns
    -------
    Output of `ast.literal_eval(val)', or `val` if `ValueError` was raised.

    """
    try:
        return ast.literal_eval(val)
    except ValueError:
        return val


class warn_defaultdict(dict):
    """
    A recursive `collections.defaultdict`, but with printed warnings when
    an item is not found.

    >>> d = warn_defaultdict({1: 2})
    >>> d[2][3][4]
    [config] WARNING: non-existent key "2" requested
    [config] WARNING: non-existent key "3" requested
    [config] WARNING: non-existent key "4" requested

    >>> d = warn_defaultdict({'sub': {'a': 'b'}})
    >>> print(d['sub']['foo'])
    [config] WARNING: non-existent key "foo" requested
    {}

    """
    def update(self, other):
        for k, v in other.items():
            self.__setitem__(k, v)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = warn_defaultdict(value)

        dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if not key in self.keys():
            print('[config] WARNING: non-existent '
                  'key "{}" requested'.format(key))

            self.__setitem__(key, warn_defaultdict())

        return dict.__getitem__(self, key)
