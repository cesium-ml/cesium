# Installation
## Installation (library)

The latest version of `cesium` can be installed via `pip`:
```
pip install cesium
```

The cesium library has the following dependencies:
- [numpy](http://www.numpy.org/)
- [scipy](http://www.scipy.org/)
- [pandas](http://pandas.pydata.org)
- [scikit-learn](http://scikit-learn.org/)
- [cython](http://cython.org/)
- [dask](http://dask.pydata.org/)
- [xarray](http://xarray.pydata.org/)

The easiest way to install the necessary dependencies is using `conda`:
```
conda install numpy scipy pandas scikit-learn cython dask xarray
```

The `cesium` library is compatible with both Python 2 and 3. 

## Installation (web app)

* Install the library dependencies above:
```
conda install numpy scipy pandas scikit-learn cython dask xarray
```

* Install [RabbitMQ](https://www.rabbitmq.com/download.html)
  * Ensure server is running with `rabbitmq-server -detached`

* Install [RethinkDB](https://www.rethinkdb.com/docs/install/)

* Install [Docker](https://docs.docker.com/engine/installation/) (optional)

  * Only required to support the execution of user-specified (custom) feature extraction functions
  * Pull down the required images: `tools/docker_pull.sh`
  * Alternatively (but this takes much longer), build the images on your own machine:
  `tools/build_docker_images.sh`

* Install the `cesium` package (from source)
  * Clone the (git repo)[https://github.com/cesium/cesium]:
    `git clone https://github.com/cesium/cesium.git`
  * Within the source directory, install via `pip install -e .`

* Setup sample data and configuration files: `cesium --install`
  * Optional: locate `~/.config/cesium/cesium.yaml` and customize authentication tokens

## Starting the web app
* Create the cesium database: `cesium --db-init`

* Launch the web platform: `cd web_client && make`
* User authentication is required by default; disable by modifying
  'disable_auth' in the configuration file.

* Navigate to `http://localhost:5000`.

* The port can be configured in `web_client/nginx.conf`.

## Testing
### Back-end
- `pip install nose nose-exclude mock`
- `make test_backend`

### Front-end
- Install [PhantomJS](http://phantomjs.org/build.html)
- `make test_frontend`
