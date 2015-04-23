FROM jpetazzo/dind

## install requirements
RUN apt-get update
RUN apt-get install -y wget curl git make \
                       python-pip \
                       python-numpy python-scipy python-pandas python-flask \
                       python-numexpr python-parse python-psutil \
                       python-requests python-simplejson python-tables \
                       python-matplotlib python-nose python-yaml \
                       python-sklearn \
                       cython
                       # Add python-docker when switching to utopic / vivid

# Download MLTSP docker images
RUN mkdir -p /tmp
RUN cd /tmp
RUN git clone --depth=1 https://github.com/mltsp/mltsp.git
RUN cd mltsp
RUN /usr/local/bin/wrapdocker & sleep 5
RUN ./tools/docker_pull.sh
RUN start-stop-daemon --stop --pidfile "/var/run/docker.pid"
