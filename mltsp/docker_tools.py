import os

try:
    from docker import Client
    dockerpy_installed = True
except ImportError:
    dockerpy_installed = False


def get_client(version='1.14'):
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

    for sock in docker_socks:
        if os.path.exists(sock):
            try:
                cli = Client(base_url='unix://{}'.format(sock), version=version)
                cli.info()
                return cli
            except ConnectionError:
                pass

    raise RuntimeError('Could not locate a usable docker socket')


def docker_images_available():
    """Return boolean indicating whether Docker images are present."""
    if not dockerpy_installed:
        return False

    try:
        cli = get_client()
        img_ids = cli.images(quiet=True)
    except RuntimeError:
        return False

    return len(img_ids) > 0


def is_running_in_docker():
    """Return bool indicating whether running in a Docker container."""
    import subprocess
    proc = subprocess.Popen(["cat", "/proc/1/cgroup"], stdout=subprocess.PIPE)
    output = proc.stdout.read()

    if "/docker/" in str(output):
        in_docker_container = True
    else:
        in_docker_container = False

    return in_docker_container
