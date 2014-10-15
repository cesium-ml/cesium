###


# using the ubuntu image
FROM ubuntu

MAINTAINER Ari Crellin-Quick, a.crellinquick@gmail.com

RUN apt-get update
RUN apt-get -y upgrade

RUN apt-get install -y python-pip python-numpy python-scipy python-matplotlib wget

RUN pip install beautifulsoup4 parse scikit-learn

#RUN wget http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-2.1.0-Linux-x86_64.sh

#bash Anaconda-2.1.0-Linux-x86_64.sh

#RUN rm Anaconda-2.1.0-Linux-x86_64.sh

RUN cat /proc/1/cgroup 

ENTRYPOINT ["python","/home/mltp/docker_scripts/docker_predict.py"]

