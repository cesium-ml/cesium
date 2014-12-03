FROM mltsp/base

MAINTAINER Ari Crellin-Quick, a.crellinquick@gmail.com

ENV DEBIAN_FRONTEND noninteractive

## install requirements
RUN apt-get install -y wget curl erlang git make openssh-server supervisor

## add user for disco
RUN adduser --system disco --shell /bin/sh

## setup ssh for disco
RUN echo root:disco | chpasswd
RUN mkdir -p /var/run/sshd

## passwordless login for disco
RUN mkdir -p /home/disco/.ssh
RUN ssh-keygen -N '' -f /home/disco/.ssh/id_dsa
RUN cat /home/disco/.ssh/id_dsa.pub >> /home/disco/.ssh/authorized_keys
RUN echo -n "localhost" > /home/disco/.ssh/known_hosts
RUN ssh-keyscan -H localhost >> /home/disco/.ssh/known_hosts
RUN chown disco -R /home/disco/.ssh

## install disco
RUN git clone --depth 1 https://github.com/discoproject/disco.git /disco
RUN cd /disco &&  make install
RUN chown -R disco /usr/var/disco

ADD disco_8989.config /disco/root/disco_8989.config

## add disco install location to pythonpath
ENV PYTHONPATH /disco/lib

## configure the supervisor which will start ssh, docker & disco
ADD supervisor.conf /etc/supervisor/conf.d/disco.conf
EXPOSE 22
EXPOSE 8990
EXPOSE 8989
CMD ["/usr/bin/supervisord"]
