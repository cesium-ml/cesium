# Installation

## System dependencies

If you are using Anaconda, create your environment with packaged
dependencies pre-installed to save time:

``conda create -n mltsp scipy pandas matplotlib scikit-learn pip``

Then activate it:

``source activate mltsp``

* Dependencies are listed in ``requirements.txt``.  Install them using:

  ``pip install --find-links=http://wheels.scikit-image.org -r requirements.txt``

* Install RabbitMQ

  For Debian / Ubuntu:

  ``sudo apt-get install rabbitmq-server``

  Server will automatically run as a daemon (background process) upon install
  on Ubuntu. On OS X, run ``rabbitmq-server -detached`` after install.

* Install RethinkDB

  For Debian / Ubuntu:

  ```
  source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
  wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
  sudo apt-get update
  sudo apt-get install rethinkdb
  ```

  Run ``rethinkdb`` in the MLTP directory.

* Install Docker

  See https://docs.docker.com/installation/ubuntulinux/ for installation and
  configuration instructions.

  Pull down the required images:

  ``tools/docker_pull.sh``

  Alternatively (but this takes much longer), build the images on your own
  machine:

  ``tools/build_docker_images.sh``

* Install nginx

* Install mltsp:

  ``pip install -e .``


## Configuration

* Execute ``import mltsp; mltsp.install()``

* Locate ``~/.config/mltsp/mltsp.yaml`` and customize authentication tokens.


## Starting the application

Launch RethinkDB:

``make db``

Initialize the database:

``make init``

Launch:

``make webapp``

To specify host, port, etc., edit ``tools/launch_waitress.sh``.
