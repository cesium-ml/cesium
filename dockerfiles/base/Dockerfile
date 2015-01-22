FROM phusion/baseimage:0.9.15

CMD ["/sbin/my_init"]

RUN /etc/my_init.d/00_regen_ssh_host_keys.sh

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y python-pip python-numpy python-scipy \
                       python-matplotlib python-sklearn python-beautifulsoup \
                       python-parse

RUN pip install future cython
