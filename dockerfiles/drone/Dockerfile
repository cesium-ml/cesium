FROM mltsp/base

RUN apt-get install -y wget

# Add RethinkDB repo
RUN \
  echo "deb http://download.rethinkdb.com/apt `lsb_release -cs` main" > /etc/apt/sources.list.d/rethinkdb.list && \
  wget -O- http://download.rethinkdb.com/apt/pubkey.gpg | apt-key add -

RUN apt-get update
RUN apt-get install -y wget curl git make \
                       python-pip \
                       python-numpy python-scipy python-pandas python-flask \
                       python-parse python-psutil \
                       python-requests python-simplejson python-tables \
                       python-matplotlib python-nose python-yaml \
                       python-sklearn \
                       cython \
                       rethinkdb docker.io phantomjs rabbitmq-server
                       # Add python-docker when switching to utopic / vivid
