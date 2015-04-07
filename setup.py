#!/usr/bin/env python

from distutils.core import setup
from pip.req import parse_requirements

REQUIREMENTS = [str(ir.req) for ir in parse_requirements('requirements.txt')]
# Note: the version is stored in a separate file so that it can be read by the Makefile
VERSION = open('VERSION').read()

setup(
    name='blueskykml',
    version=VERSION,
    author='Anthony Cavallaro, Ken Craig, John Stilley, Joel Dubowy', # TODO: anyone else?
    author_email='jdubowy@gmail.com', # STI's email addresses
    packages=[
        'blueskykml',
        'blueskykml.pykml'
    ],
    scripts=[
        'bin/makedispersionkml'
    ],
    data_files=[
        ('assets', ['assets/disclaimer.png', 'assets/fire_event.png', 'assets/fire_location.png'])
    ],
    # TODO: add git repo url if this gets moved into it's own repo
    description='Package for creating kmls from BlueSky smoke dispersion output.',
    install_requires=REQUIREMENTS,
)
