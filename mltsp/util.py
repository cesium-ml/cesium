import subprocess
import os
import numpy as np

try:
    import docker
    dockerpy_installed = True
except ImportError:
    dockerpy_installed = False
import requests



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
    import subprocess
    if not os.path.exists("/proc/1/cgroup"):
        return False
    proc = subprocess.Popen(["cat", "/proc/1/cgroup"], stdout=subprocess.PIPE)
    output = proc.stdout.read()
    if "/docker/" in str(output):
        in_docker_container = True
    else:
        in_docker_container = False
    return in_docker_container


def cast_model_params(model_type, model_params):
    """Cast model parameter strings to expected types."""
    from .ext.sklearn_models import model_descriptions
    # Find relevant model description
    for entry in model_descriptions:
        if entry["abbr"] == model_type:
            params_list = entry["params"]
            break
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
        # If type description is a single type and not of type list, do cast
        if type(param_entry["type"]) == type and param_entry["type"] != list:
            dest_type = param_entry["type"]
            model_params[k] = dest_type(v)
        # Parse string describing list correctly, eschewing `eval`
        elif param_entry["type"] == list:
            model_params[k] = model_params[k].replace("[", "").replace("]", "")\
                                                              .replace(" ", "")\
                                                              .split(",")
            for i in range(len(model_params[k])):
                if "." in model_params[k][i]:
                    model_params[k][i] = float(model_params[k][i])
                elif model_params[k][i].isdigit():
                    model_params[k][i] = int(model_params[k][i])
        # Type description is a list of types
        elif type(param_entry["type"]) == list:
            dest_types_list = param_entry["type"]
            for dest_type in dest_types_list:
                if dest_type != str:
                    try:
                        model_params[k] = dest_type(v)
                        break
                    except:
                        continue
            if type(model_params[k]) == str and str not in dest_types_list:
                raise(ValueError("Model parameter cannot be cast to expected "
                                 "type."))
