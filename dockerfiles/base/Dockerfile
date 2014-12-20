FROM phusion/baseimage:0.9.15

CMD ["/sbin/my_init"]

RUN /etc/my_init.d/00_regen_ssh_host_keys.sh

RUN apt-get update
RUN apt-get -y upgrade


RUN apt-get install -y python-pip python-numpy python-scipy \
                       python-matplotlib python-sklearn python-beautifulsoup \
                       python-parse

RUN apt-get install -y python3-dev python3-pip python3-numpy python3-scipy \
                       python3-matplotlib 
                       
#
RUN mkdir -p /usr/local/include
RUN ln -s /usr/X11/include/freetype2/freetype /usr/local/include/freetype

RUN pip3 install beautifulsoup4 scikit-learn parse cython
