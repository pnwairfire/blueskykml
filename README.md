# blueskykml

This package is based on code extracted from the kml3 module in BlueSky
Framework.

## Installing

First, you need to install dependencies. Beginning with non-python
dependencies, use the following on linux:

    sudo apt-get install gdal

Alternatively, on OSX, use the following:

    brew install gdal

Python package dependencies are listed in requirements.txt. Instell them
with the following:

    pip install -r requirements.txt

These packages will automatically be installed if you use setup.py to
install the blueskykml (rather than running from the source repo). To
install blueskykml, you can use the following:

    python ./setup.py install

## Using

Example uses:

    $ ./bin/makedispersionkml -c ./sample-config/makedispersionkml.ini \
        -o /path/to/bluesky/output/ -v -k ./smoke-dispersion.kmz -f fires.kmz

## Distributing

To build a distribution tarball, use the following.

    python ./setup.py sdist

This will create a tarball in ```REPO_ROOT/dist/```
