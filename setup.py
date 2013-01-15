#!/usr/bin/env python

from distutils.core import setup

setup(
        name="gstat",
        author="nixon",
        url="https://github.com/nixon/gstat/",
        version="0.1.0",
        license="LICENSE",
        description='Send metrics to a graphite host.',
        long_description=open('README.md').read(),
        packages=[
            'gstat',
            'gstat.tests',
            ],
        scripts=[
            'gstat/gstat.py',
            ],
        )
