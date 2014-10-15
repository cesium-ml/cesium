###


# using the ubuntu image
FROM ubuntu

MAINTAINER Ari Crellin-Quick, a.crellinquick@gmail.com

RUN apt-get update
RUN apt-get -y upgrade

RUN apt-get install -y python-pip python-numpy python-scipy python-matplotlib

RUN pip install beautifulsoup4 parse scikit-learn

RUN cat /proc/1/cgroup 

RUN mkdir -p /tmp

ENTRYPOINT ["python","/home/mltp/docker_scripts/docker_build_model.py"]

