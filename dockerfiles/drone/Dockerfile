FROM mltsp/base

RUN sed -i 's/archive.ubuntu.com/us.archive.ubuntu.com/g' /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y wget

# Add RethinkDB repo
RUN \
  echo "deb http://download.rethinkdb.com/apt `lsb_release -cs` main" > /etc/apt/sources.list.d/rethinkdb.list && \
  wget -O- http://download.rethinkdb.com/apt/pubkey.gpg | apt-key add -

RUN apt-get update
RUN apt-get install -y curl git make \
                       python3-dev \
                       rethinkdb docker.io rabbitmq-server nginx \
                       libzmq3 libzmq3-dev supervisor

# Install PhantomJS
RUN apt-get install -y fontconfig-config fonts-dejavu-core libfontconfig1 libfreetype6 \
                       libjpeg-turbo8 libjpeg8 && \
cd /usr/local/share && \
wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.8-linux-x86_64.tar.bz2 && \
tar xjf phantomjs-1.9.8-linux-x86_64.tar.bz2 && \
ln -s /usr/local/share/phantomjs-1.9.8-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs

ENTRYPOINT ["/sbin/my_init", "--"]
