# Installation

## System dependencies

If you are using Anaconda, create your environment with packaged
dependencies pre-installed to save time:

``conda create -n mltsp scipy pandas matplotlib scikit-learn pip``

Then activate it:

``source activate mltsp``

* Dependencies are listed in ``requirements.txt``.  Install them using:

  ``pip install --find-links=http://wheels.scikit-image.org -r requirements.txt``

* Install and configure Disco

  Requires: Erlang. If you see errors about `escript` below,
  this is what you're missing.

  ```
  git clone --depth 1 git://github.com/discoproject/disco.git disco
  cd disco
  make
  cd lib && python setup.py install && cd ..
  export DISCO_HOME=/path/to/disco/repository
  ```

  You also have to setup passwordless SSH authentication to the local
  machine (this is required for running the test suite):

  ```
  ssh-keygen -N '' -f ~/.ssh/id_dsa
  cat ~/.ssh/id_dsa.pub >> ~/.ssh/authorized_keys
  ```

  (Test that SSH is working with: ``ssh localhost erl``)

  Navigate to ``localhost:8989``, click "configure" and ensure that
  an entry for "localhost" exists under "Available nodes".  If not,
  add one with the corresponding number of cores as the "workers" value.

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

  Pull down the required images:

  ``tools/docker_pull.sh``

  Alternatively (but this takes much longer), build the images on your own
  machine:

  ``tools/build_docker_images.sh``

* Install nginx

* Install mltsp:

  ``pip install -e .``


## Configuration

* In the file ``cfg.py`, locate the following variables and set
  them to reflect your system architecture:

  ``PROJECT_PATH``

  Optionally, also set

  ``MODELS_FOLDER, UPLOAD_FOLDER, FEATURES_FOLDER, ERR_LOG_PATH``

* Authentication information is currently stored in ``mltsp.yaml``
  (an example is provided as ``mltsp.yaml.example``).  This
  configuration file and ``cfg.py`` will eventually become one.


## Starting the application

Launch RethinkDB:

``make db``

Initialize the database:

``make init``

Launch:

``make webapp``

To specify host, port, etc., edit ``tools/launch_waitress.sh``.
