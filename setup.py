#!/usr/bin/env python

from distutils.core import setup

setup(name='plyprotobuf',
      version='1.1',
      description='Protobuf Parsing Library that uses ply',
      author='Dusan Klinec',
      url='https://github.com/sb98052/plyprotobuf',
      packages=['plyproto'],
      install_requires=['ply']
     )
