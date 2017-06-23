#!/usr/bin/env python

from distutils.core import setup

setup(name='plyxproto',
      version='2.0',
      description='Protobuf Parsing Library that uses ply and supports XOS extensions',
      author='Dusan Klinec, Sapan Bhatia',
      url='https://github.com/sb98052/plyprotobuf',
      packages=['plyxproto'],
      install_requires=['ply']
     )
