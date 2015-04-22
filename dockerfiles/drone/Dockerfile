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

