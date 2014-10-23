# Machine Learning Time-series Platform


## System dependencies:

   If you are using Anaconda, create your environment with packaged
   dependencies pre-installed to save time:

   ``conda create -n mltp scipy pandas matplotlib scikit-learn pytables pip``

   Then activate it:

   ``source activate mltp``

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
     bin/disco nodaemon
     ```

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

     Build the required images from Docker files by running

     ``tools/build_docker_images.sh``

   * Install nginx


## Configuration

   * In the file cfg.py, locate the following variables and set them
     to reflect your system architecture:

     ``PROJECT_PATH``

     Optionally, also set

     ``MODELS_FOLDER, UPLOAD_FOLDER, FEATURES_FOLDER, ERR_LOG_PATH``


## Starting the application

   First, initialize the database:

   ``PYTHONPATH="." python flask/flask_app.py --dbinit``

   Invoke the app either in **standard** mode or in **debug mode**:

   ``PYTHONPATH="." python flask/flask_app.py``

   or

   ``PYTHONPATH="." python flask/flask_app.py --debug``

   To specify host, port, etc., execute with ``--help`` for more information.
