# blueskykml

This package was build using code extracted from the kml3 module in BlueSky
Framework.

## Non-python Dependencies

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

### Ubuntu

First update

    sudo apt-get update
    sudo apt-get upgrade

If you don't have python and pip installed:

    sudo apt-get install -y python
    sudo apt-get install -y python-dev
    sudo apt-get install -y python-pip
    sudo pip install --upgrade pip

Install libnetcdf

    sudo apt-get install -y libnetcdf-dev

On ubuntu, you need to install numpy and gdal manually.

    sudo pip install numpy==1.8.0
    wget http://download.osgeo.org/gdal/1.11.2/gdal-1.11.2.tar.gz
    tar xvfz gdal-1.11.2.tar.gz
    cd gdal-1.11.2
    ./configure --with-python --prefix=/usr
    make
    sudo make install
    sudo ldconfig
    sudo apt-get install -y python-gdal

## Development

### Clone Repo

Via ssh:

    git clone git@github.com:pnwairfire/blueskykml.git

or http:

    git clone https://github.com/pnwairfire/blueskykml.git

### Install Dependencies

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
    pip install --no-binary :all: gdal==1.11.2

If this doesn't work, uninstall gdal, and then install it manually:

    pip uninstall -y GDAL
    wget https://pypi.python.org/packages/source/G/GDAL/GDAL-1.11.2.tar.gz
    tar xzf GDAL-1.11.2.tar.gz
    cd GDAL-1.11.2
    python setup.py install

### Setup Environment

To import blueskykml in development, you'll have to add the repo root
directory to the search path.

## Running tests

Use pytest:

    py.test
    py.test test/fccsmap/

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about

## Installing

First install the non-python dependencies (mentioned above).

### Installing With pip

Install pip, if it isn't yet installed:

    sudo apt-get install python-pip

Then, to install, for example, v0.2.5, use the following:

    sudo pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple blueskykml==0.2.5

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
cloning the repo.  e.g. To install v0.2.5, use ```git checkout v0.2.5```.

## Using

Example uses:

    $ ./bin/makedispersionkml -c ./sample-config/makedispersionkml.ini \
        -o /path/to/bluesky/output/ -v -k ./smoke-dispersion.kmz -f fires.kmz

## Distributing

To build a distribution tarball, use the following.

    python ./setup.py sdist

This will create a tarball in ```REPO_ROOT/dist/```
