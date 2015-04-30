FROM mltsp/base

## install requirements
RUN apt-get update
RUN apt-get install -y wget curl erlang git make

## add user for disco
RUN adduser --system disco --shell /bin/bash

RUN echo root:disco | chpasswd

## passwordless login for disco

RUN mkdir -p /home/disco/.ssh
RUN chown disco -R /home/disco/.ssh
RUN ssh-keygen -t dsa -f /home/disco/.ssh/id_dsa
RUN cat /home/disco/.ssh/id_dsa.pub > /home/disco/.ssh/authorized_keys
RUN /usr/sbin/sshd && ssh-keyscan -H localhost > /home/disco/.ssh/known_hosts

## passwordless login for root
RUN mkdir -p /root/.ssh
RUN ssh-keygen -N '' -f /root/.ssh/id_dsa
RUN cat /root/.ssh/id_dsa.pub >> /root/.ssh/authorized_keys
RUN echo -n "localhost " > /root/.ssh/known_hosts
RUN cat /etc/ssh/ssh_host_rsa_key.pub >> /root/.ssh/known_hosts

## install disco

RUN git clone --depth 1 https://github.com/discoproject/disco.git /disco
RUN cd /disco &&  make install
RUN chown -R disco /usr/var/disco
ADD disco_8989.config /usr/var/disco/disco_8989.config

## add disco install location to pythonpath
ENV PYTHONPATH /disco/lib

## add disco to runit
RUN mkdir /etc/service/disco
ADD disco.sh /etc/service/disco/run

# clean system
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
