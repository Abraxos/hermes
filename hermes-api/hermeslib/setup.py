from setuptools import setup, find_packages
import sys, os

version = '0.0.1'

setup(name='hermeslib',
      version=version,
      description="Library for servers and clients of the Hermes Secure Messaging Protocol",
      long_description="""\
Hermes is a protocol for secure chat messaging. This library defines the core of protocol as well as giving sample APIs that use it on both the server and the client sides.""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='hermes cryptography chat messenger client server network twisted',
      author='Eugene Kovalev',
      author_email='euge.kovalev@gmail.com',
      url='eugene.kovalev.systems',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
