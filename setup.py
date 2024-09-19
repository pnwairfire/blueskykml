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
        'bin/makedispersionkml',
        'bin/reproject'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX",
        "Operating System :: MacOS"
    ],
    url='https://github.com/pnwairfire/blueskykml/',
    description='Package for creating kmls from BlueSky smoke dispersion output.',
    install_requires=[
        "afdatetime>=3.0.0,<4.0.0",
        "numpy==2.1.1",
        "GDAL==3.8.4",
        "pillow==10.4.0",
        "matplotlib==3.9.2"
    ],
    dependency_links=[
        "https://pypi.airfire.org/simple/afdatetime/",
    ],
    tests_require=test_requirements
)
