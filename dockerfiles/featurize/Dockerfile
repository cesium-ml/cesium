###

## using the ubuntu image
FROM ubuntu

MAINTAINER Ari Crellin-Quick, a.crellinquick@gmail.com

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get -y upgrade

## install requirements
RUN apt-get install -y python-pip python-numpy python-scipy python-matplotlib
RUN apt-get install -y wget curl erlang git make python openssh-server supervisor
RUN pip install beautifulsoup4 parse scikit-learn

## add user for disco
RUN adduser --system disco --shell /bin/sh

## setup ssh for disco
RUN echo root:disco | chpasswd
RUN mkdir -p /var/run/sshd

## passwordless login for docker 
RUN mkdir -p /home/disco/.ssh
RUN ssh-keygen -N '' -f /home/disco/.ssh/id_dsa
RUN cat /home/disco/.ssh/id_dsa.pub >> /home/disco/.ssh/authorized_keys
RUN echo -n "localhost" > /home/disco/.ssh/known_hosts
RUN cat /etc/ssh/ssh_host_rsa_key.pub >> /home/disco/.ssh/known_hosts
RUN chown disco -R /home/disco/.ssh

## install disco
RUN git clone https://github.com/discoproject/disco.git /disco
RUN cd /disco &&  make install
RUN chown -R disco /usr/var/disco

## add disco install location to pythonpath
#RUN PYTHONPATH=$PYTHONPATH:/disco/lib
#RUN export $PYTHONPATH
ENV PYTHONPATH /disco/lib

## configure the supervisor which will start ssh & docker
ADD supervisor.conf /etc/supervisor/conf.d/disco.conf
EXPOSE 22
EXPOSE 8990
EXPOSE 8989
CMD ["/usr/bin/supervisord"]

RUN /disco/bin/disco nodaemon

RUN disco status

ENTRYPOINT ["python","/home/mltp/docker_scripts/docker_featurize.py"]

