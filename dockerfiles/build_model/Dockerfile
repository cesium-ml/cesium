FROM mltsp/base

MAINTAINER Ari Crellin-Quick, a.crellinquick@gmail.com

RUN cat /proc/1/cgroup
RUN pip install future
ENTRYPOINT ["python", "/home/mltsp/run_script_in_container.py", "--build_model"]
