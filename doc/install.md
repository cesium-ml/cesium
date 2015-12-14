# Installation
## Installation (library)

The latest version of `mltsp` can be installed via `pip`:
```
pip install mltsp
```

The MLTSP library has the following dependencies:
- [numpy](http://www.numpy.org/)
- [scipy](http://www.scipy.org/)
- [pandas](http://pandas.pydata.org)
- [scikit-learn](http://scikit-learn.org/)
- [cython](http://cython.org/)
- [dask](http://dask.pydata.org/)
- [xray](http://xray.readthedocs.org/)

The easiest way to install the necessary dependencies is using `conda`:
```
conda install numpy scipy pandas scikit-learn cython dask xray
```

The `mltsp` library is compatible with both Python 2 and 3. 

## Installation (web app)

* Install the library dependencies above:
```
conda install numpy scipy pandas scikit-learn cython dask xray
```

* Install [RabbitMQ](https://www.rabbitmq.com/download.html)
  * Ensure server is running with `rabbitmq-server -detached`

* Install [RethinkDB](https://www.rethinkdb.com/docs/install/)

* Install [Docker](https://docs.docker.com/engine/installation/) (optional)

  * Only required to support the execution of user-specified (custom) feature extraction functions
  * Pull down the required images: `tools/docker_pull.sh`
  * Alternatively (but this takes much longer), build the images on your own machine:
  `tools/build_docker_images.sh`

* Install the `mltsp` package (from source)
  * Clone the (git repo)[https://github.com/mltsp/mltsp]:
    `git clone https://github.com/mltsp/mltsp.git`
  * Within the source directory, install via `pip install -e .`

* Setup sample data and configuration files: `mltsp --install`
  * Optional: locate `~/.config/mltsp/mltsp.yaml` and customize authentication tokens

## Starting the web app
* Create the MLTSP database: `mltsp --db-init`

* Launch the web platform: `mltsp`
  * User authentication is required by default; disable with `--disable-auth`

* Navigate to `http://localhost:5000`.

* Host, port, etc. can be specified in `tools/launch_waitress.sh`.

## Testing
### Back-end
- `pip install nose nose-exclude`
- `make test_backend`

### Front-end
- Install [PhantomJS](http://phantomjs.org/build.html)
- `make test_frontend`
