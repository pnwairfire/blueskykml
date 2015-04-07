#!/usr/bin/env python

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    REQUIREMENTS = f.read().splitlines()

from blueskykml import __version__

VERSION = open('VERSION').read()

setup(
    name='blueskykml',
    version=VERSION,
    author='Anthony Cavallaro, Ken Craig, John Stilley, Joel Dubowy',
    author_email='jdubowy@gmail.com', # STI's email addresses
    packages=find_packages(),
    package_data={
        'blueskykml': ['assets/*.png']
    },
    scripts=[
        'bin/makedispersionkml'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Operating System :: POSIX",
        "Operating System :: MacOS"
    ],
    url='https://github.com/pnwairfire/blueskykml/',
    description='Package for creating kmls from BlueSky smoke dispersion output.',
    install_requires=REQUIREMENTS,
)
