# blueskykml

This package was build using code extracted from the kml3 module in BlueSky
Framework.

## Dependencies

Whether cloning the repo or installing with pip, you'll first need to manually
install netcdf and gdal libraries, which blueskykml depends on. These
instructions assume you already have python and pip installed, as well as
C and C++ compilers, etc.

### Mac

On a mac, using [Homebrew](http://brew.sh/):

    brew install homebrew/science/netcdf
    brew install gdal --with-netcdf --enable-unsupported

Note that the '--with-netcdf' option is required to build gdal with the
netCDF driver. See http://trac.osgeo.org/gdal/wiki/NetCDF for more information.

Additionally, you'll need the gdal python bindings.  These used to be
baked into setup.py, but the version available for install depends
on your platform.

    gdal-config --version
    pip install gdal==`gdal-config --version`

### Ubuntu, 12.04 LTS (precise)

First update

    sudo apt-get update

If you don't have python and pip installed:

    sudo apt-get install -y python python-dev python-pip
    sudo pip install --upgrade pip

Install libnetcdf

    sudo apt-get install -y libnetcdf-dev

Install numpy and gdal.

    sudo pip install numpy==1.8.0
    sudo apt-get install -y libgdal1-1.7.0
    sudo pip install gdal==1.7.0

Install xml libs:

    sudo apt-get install -y libxml2-dev libxslt1-dev

## Development

### Clone Repo

Via ssh:

    git clone git@github.com:pnwairfire/blueskykml.git

or http:

    git clone https://github.com/pnwairfire/blueskykml.git

### Install Python Dependencies

#### Main dependencies

After installing the non-python dependencies (mentioned above), run the
following to install required python packages:

    pip install --no-binary gdal -r requirements.txt

#### Dev and test dependencies

Run the following to install packages required for testing:

    pip install -r requirements-test.txt

#### Notes

##### pip issues

If you get an error like    ```AttributeError: 'NoneType' object has no
attribute 'skip_requirements_regex```, it means you need in upgrade
pip. One way to do so is with the following:

    pip install --upgrade pip

##### gdal issues

If, when you run makedispersionkml, you get the following error:

    *** Error: No module named _gdal_array

it's because your osgeo package (/path/to/site-packages/osgeo/) is
missing _gdal_array.so.  This happens when gdal is built on a
machine that lacks numpy.  The ```--no-binary :all:``` in the pip
install command, above, is meant to fix this issue.  If it doesn't work,
try uninstalling the gdal package and then re-installing it individually
with the ```--no-binary``` option to pip:

    pip uninstall -y GDAL
    pip install --no-binary :all: gdal==<VERSION>

If this doesn't work, uninstall gdal, and then install it manually:

    pip uninstall -y GDAL
    wget https://pypi.python.org/packages/source/G/GDAL/GDAL-<VERSION>.tar.gz
    tar xzf GDAL-<VERSION>.tar.gz
    cd GDAL-<VERSION>
    python setup.py install

### Setup Environment

To import blueskykml in development, you'll have to add the repo root
directory to the search path.

## Running tests

Use pytest:

    py.test
    py.test test/blueskykml/

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about

## Installing

First install the non-python dependencies (mentioned above).

### Installing With pip

Install pip, if it isn't yet installed:

    sudo apt-get install python-pip

Then, to install, for example, v0.2.10, use the following:

    sudo pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple blueskykml==0.2.10

See the Development > Install Dependencies > Notes section, above, for
notes on resolving pip and gdal issues.

### Installing With setup.py

To install blueskykml from the source repo, you can use the following:

    git clone https://github.com/pnwairfire/blueskykml.git
    cd blueskykml
    rm .python-version
    python ./setup.py install

#### Dependency conflicts

If blueskykml's python dependencies conflict with versions already
installed on your machine, then remove the 'install_requires'
kwarg from the setup call in setup.py, and then rerun ```python ./setup.py
install```.  Of course, there's no guarantee that blueskykml will work
with the older versions, but it very well might.  Also, you need to
make sure that each dependency, whatever the version, is installed.

#### Installing specific version

To install a specific version, git checkout the appropriate tag after
cloning the repo.  e.g. To install v0.2.10, use ```git checkout v0.2.10```.

## Using

Example uses:

    $ ./bin/makedispersionkml -c ./sample-config/makedispersionkml.ini \
        -o /path/to/bluesky/output/ -v -k ./smoke-dispersion.kmz -f fires.kmz

### Config Options

#### Section 'DEFAULT'
 - MODES -- e.g. 'fires dispersion'

#### Section 'PolygonsKML'
 - MAKE_POLYGONS_KMZ --
 - POLYGONS_OUTPUT_DIR --
 - MAKEPOLYGONS_BINARY --
 - KMZ_FILE --
 - OVERLAY_TITLE --
 - POLYGON_COLORS --

#### Section 'DispersionGridInput'
 - FILENAME --
 - PARAMETER --
 - LAYER --

#### DispersionGridOutput
 - OUTPUT_DIR --
 - GRID_INFO_JSON --
 - HOURLY_COLORS --
 - THREE_HOUR_COLORS --
 - DAILY_COLORS --

#### RedColorBar
 - DEFINE_RGB --
 - DATA_LEVELS --
 - GREEN --
 - BLUE --
 - RED --
 - IMAGE_OPACITY_FACTOR --
 - DEFINE_HEX --
 - HEX_COLORS --

#### DispersionImages
 - DEFINE_RGB --
 - BACKGROUND_COLOR_RED --
 - BACKGROUND_COLOR_GREEN --
 - BACKGROUND_COLOR_BLUE --
 - DEFINE_HEX --
 - BACKGROUND_COLOR_HEX --
 - IMAGE_OPACITY_FACTOR --
 - REPROJECT_IMAGES --

#### SmokeDispersionKMLInput
 - MET_TYPE --
 - FIRE_LOCATION_CSV --
 - FIRE_EVENT_CSV --
 - DISCLAIMER_IMAGE --
 - FIRE_EVENT_ICON --
 - FIRE_LOCATION_ICON --

#### SmokeDispersionKMLOutput
 - KMZ_FILE --

## Distributing

To build a distribution tarball, use the following.

    python ./setup.py sdist

This will create a tarball in ```REPO_ROOT/dist/```

## Docker

Two Dockerfiles are included in this repo - one for running blueskykml
out of the box, and the other for use as a base environment for
development.

### Install Docker

See https://docs.docker.com/engine/installation/ for platform specific
installation instructions.

### Start Docker

#### Mac OSX

On a Mac, the docker daemon runs inside a Linux VM. The first time
you use docker, you'll need to create a vm:

    docker-machine create --driver virtualbox docker-default

Check that it was created:

    docker-machine ls

Subsequently, you'll need to start the vm with:

    docker-machine start docker-default

Once it's running, set env vars so that your docker knows how to find
the docker host:

    eval "$(docker-machine env docker-default)"

#### Ubuntu

...TODO: fill in insructions...


### Build Bluesky Docker Image from Dockerfile

    cd /path/to/blueskykml/repo/
    docker build -t blueskykml-base docker/base/
    docker build -t blueskykml docker/complete/

### Obtain pre-built docker images

As an alternative to building the image yourself, you can use the pre-built
complete image.

    docker pull pnwairfire/blueskykml

See the [blueskykml docker hub page](https://hub.docker.com/r/pnwairfire/blueskykml/)
for more information.

### Run Complete Container

If you run the image without a command, i.e.:

    docker run blueskykml

it will output the makedispersionkml help image.  To run makedispersionkml
with input, you'll need to use the '-v' option to mount host machine
directories in your container.  For example, suppose you've got bluesky
output data in /bluesky-output/20151212f/data/ and you want to create
the dispersion kml in /docker-output/, you could run something like the
following:

    docker run \
        -v /home/foo/bluesky-output/2015121200/data/:/input/ \
        -v /home/foo/docker-output/:/output/ blueskykml \
        makedispersionkml \
        -i /input/smoke_dispersion.nc \
        -l /input/fire_locations.csv \
        -e /input/fire_events.csv \
        -o /output/

### Using base image for development

The blueskykml-base image has everything except the blueskykml
package and it's python dependencies.  You can use it to run blueskykml
from your local repo. First install the python dependencies for your
current version of the repo

    docker run --name blueskykml-base \
        -v /home/foo/path/to/blueskykml/repo/:/blueskykml/ -w /blueskykml/ \
        blueskykml-base pip install --no-binary gdal \
        --trusted-host pypi.smoke.airfire.org -r requirements.txt

then commit container changes back to image

    docker commit blueskykml-base blueskykml-base

Then run makedispersionkml:

    docker run -v /home/foo/path/to/blueskykml/repo:/blueskykml/ -w /blueskykml/ blueskykml-base ./bin/makedispersionkml -h

### Notes about using Docker

#### Mounted volumes

Mounting directories outside of your home
directory seems to result in the directories appearing empty in the
docker container. Whether this is by design or not, you apparently need to
mount directories under your home directory.  Sym links don't mount either, so
you have to cp or mv directories under your home dir in order to mount them.

#### Cleanup

Docker leaves behind partial images during the build process, and it leaves behind
containers after they've been used.  To clean up, you can use the following:

    # remove all stopped containers
    docker ps -a | awk 'NR > 1 {print $1}' | xargs docker rm

    # remove all untagged images:
    docker images | grep "<none>" | awk '{print $3}' | xargs docker rmi
