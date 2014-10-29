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

# Expose ports for disco
EXPOSE 22
EXPOSE 8990
EXPOSE 8989

## setup ssh for disco
RUN echo root:disco | chpasswd
RUN mkdir -p /var/run/sshd


#CMD ["service", "sshd", "start"]
#RUN service ssh status
#RUN service ssh start

## passwordless login for root
#RUN mkdir -p /root/.ssh
#RUN ssh-keygen -N '' -f /root/.ssh/id_dsa
#RUN cat /root/.ssh/id_dsa.pub >> /root/.ssh/authorized_keys
#RUN echo -n "localhost " > /root/.ssh/known_hosts
#RUN cat /etc/ssh/ssh_host_rsa_key.pub >> /root/.ssh/known_hosts

## add user for disco
RUN adduser --system disco --shell /bin/sh



## passwordless login for disco 
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


#ADD disco_8989.config /disco/root/disco_8989.config

## add disco install location to pythonpath
ENV PYTHONPATH /disco/lib

## configure the supervisor which will start ssh & docker

ADD supervisor.conf /etc/supervisor/conf.d/disco.conf





CMD ["/usr/bin/supervisord"]


# try starting disco:
#RUN /disco/bin/disco nodaemon


#RUN /disco/bin/disco nodaemon


ADD start_disco /start_disco


#RUN /start_disco

#RUN disco status


ENTRYPOINT ["python","/home/mltp/docker_scripts/run_disco_test.py"]

