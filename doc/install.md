# Installation

## System dependencies

Install compiler dependecies with

``sudo apt-get install build-essential python-dev libgfortran3``

If you are using Anaconda (install dependencies with
`sudo apt-get install libsm6 libxrender1 libfontconfig1`),
create your environment with packaged dependencies pre-installed to save time:

``conda create -n mltsp scipy pandas matplotlib scikit-learn pip``

Then activate the environment:

  ``source activate mltsp``

* Install MLTSP

  ``pip install mltsp``

* Install RabbitMQ

  For Debian / Ubuntu:

  ``sudo apt-get install rabbitmq-server``

  The server will automatically run as a daemon (background process)
  upon install on Ubuntu.

  Downloads for Mac OS X are
  [here](https://www.rabbitmq.com/install-standalone-mac.html).
  Launch via ``rabbitmq-server -detached``  after install.

* Install PhantomJS

  For Debian / Ubuntu:

  ``sudo apt-get install phantomjs``

  Downloads for Mac OS X are [here](http://phantomjs.org/download.html).

* Install RethinkDB

  For Debian / Ubuntu:

  ```
  source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
  wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
  sudo apt-get update
  sudo apt-get install rethinkdb
  ```

  Instructions for Mac OS X are [here](https://rethinkdb.com/docs/install/osx/).

* Install Docker (optional)

  *This step is only required if you want to support the execution of
  user-specified feature extractors.*

  See https://docs.docker.com/installation/ubuntulinux/ for installation and
  configuration instructions.

  Pull down the required images:

  ``tools/docker_pull.sh``

  Alternatively (but this takes much longer), build the images on your own
  machine:

  ``tools/build_docker_images.sh``

## Configuration

* Run ``mltsp --install``.

* Optionally: locate ``~/.config/mltsp/mltsp.yaml`` and customize
  authentication tokens.

## Running MLTSP

Create the MLTSP database:

  ``mltsp --db-init``

Then, launch the web platform:

  ``mltsp --disable-auth``  # Without user authentication
  ``mltsp``                 # With user authentication

Connect with a web browser to ``http://localhost:5000``.

## Developer installation

Dependencies are listed in ``requirements.txt``.  Install them using:

  ``pip install --find-links=http://wheels.scikit-image.org -r requirements.txt``

Then do a local installation from the MLTSP directory:

  ``pip install -e .``

## Developer Makefile targets

* Launch RethinkDB:

``make db``

* Initialize the database:

``make init``

* Launch:

``make webapp``

* To specify host, port, etc., edit ``tools/launch_waitress.sh``.
