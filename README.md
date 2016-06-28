# blueskykml

This package was build using code extracted from the kml3 module in BlueSky
Framework.

***This software is provided for research purposes only. It's output may
not accurately reflect observed data due to numerous reasons. Data are
provisional; use at own risk.***

## Python 2 and 3 Support

This package was originally developed to support python 2.7, but has since
been refactored to support 3.5. Attempts to support both 2.7 and 3.5 have
been made but are not guaranteed.

## External Dependencies

Whether cloning the repo or installing with pip, you'll first need to manually
install numpy, netcdf, and gdal, which blueskykml depends on. These
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

    pip install numpy
    gdal-config --version
    pip install gdal==`gdal-config --version`

### Ubuntu 12.04, 14.04, 16.04

    sudo apt-get update
    sudo apt-get install -y python3 python3-dev python3-pip
    sudo pip3 install distribute
    sudo apt-get install -y libnetcdf-dev
    sudo apt-get install -y libgdal-dev
    sudo apt-get install -y python3-numpy python3-gdal
    sudo apt-get install -y libxml2-dev libxslt1-dev
    sudo apt-get install -y mapserver-bin python3-mapscript

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

    pip install -r requirements.txt

#### Dev and test dependencies

Run the following to install packages required for testing:

    pip install -r requirements-dev.txt
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

Then, to install, for example, v1.0.0, use the following:

    sudo pip install --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple blueskykml==1.0.0

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
cloning the repo.  e.g. To install v1.0.0, use ```git checkout v1.0.0```.

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

There is no longer a Dockerfile maintained for this project. If you'd
like to run ```makedispersionkml``` in docker, you can use the
[bluesky docker image](https://hub.docker.com/r/pnwairfire/bluesky/),
which contains all of blueskykml's dependencies (as well as blueskykml
itself).
