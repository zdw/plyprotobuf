#!/usr/bin/env python

"""plyxproto xproto parser

See:
https://github.com/sb98052/plyprotobuf
https://github.com/opencord/xos
"""

from setuptools import setup

setup(name='plyxproto',
      version='2.2.0',
      description='xproto parser and processor',
      author='Dusan Klinec (original protobuf parser), Sapan Bhatia (xproto extensions)',
      author_email='sapan@opennetworking.org',
      url='https://github.com/sb98052/plyprotobuf',
      license='Apache Software License',

      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Build Tools',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7'
      ],
      keywords='xproto protobuf xos parser',
      packages=['plyxproto'],
      install_requires=['ply']
     )
