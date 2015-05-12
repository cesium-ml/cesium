import subprocess
from subprocess import Popen, PIPE


def currently_running_in_docker_container():
    """Return bool indicating whether running in a Docker container."""
    import subprocess
    proc = subprocess.Popen(["cat", "/proc/1/cgroup"], stdout=subprocess.PIPE)
    output = proc.stdout.read()
    if "/docker/" in str(output):
        in_docker_container = True
    else:
        in_docker_container = False
    return in_docker_container


def check_disco_running():
    # Check if Disco is running
    try:
        process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        disco_running = "running" in stdout
    except OSError:
        disco_running = False
    return disco_running
