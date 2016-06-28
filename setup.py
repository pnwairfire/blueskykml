#!/usr/bin/env python

from setuptools import setup, find_packages

from blueskykml import __version__

test_requirements = []
with open('requirements-test.txt') as f:
    test_requirements = [r for r in f.read().splitlines()]

setup(
    name='blueskykml',
    version=__version__,
    license='GPLv3+',
    author='Anthony Cavallaro, Ken Craig, John Stilley, Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=find_packages(),
    package_data={
        'blueskykml': [
            'assets/*.png',
            'config/*.ini'
        ]
    },
    scripts=[
        'bin/makedispersionkml'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Operating System :: POSIX",
        "Operating System :: MacOS"
    ],
    url='https://github.com/pnwairfire/blueskykml/',
    description='Package for creating kmls from BlueSky smoke dispersion output.',
    install_requires=[
        # Note: numpy and gdal must now be installed manually beforehand
        #"numpy",
        #"GDAL==1.11.2",
        "Pillow==2.8.1",
        "matplotlib==1.4.3"
    ],
    tests_require=test_requirements
)
