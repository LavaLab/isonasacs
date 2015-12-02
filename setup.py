#!/usr/bin/env python
import os
import re
import codecs
from setuptools import setup, find_packages


def read(fname):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), fname), 'r', 'utf-8').read()


def get_version():
    init = read(os.path.join('isonasacs', '__init__.py'))
    return re.search("__version__ = '([0-9.]*)'", init).group(1)

setup(name='isonasacs',
    version=get_version(),
    author='Lava Lab Software',
    author_email='mail@lavalab.com.au',
    url='https://github.com/LavaLab/isonasacs',
    description='A module to manage ISONAS Access Control System',
    long_description=read('README.rst'),
    packages=find_packages(),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Office/Business',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        ],
    license='BSD',
    test_suite='isonasacs.test',
    tests_require=['mock'],
    use_2to3=True,
    )
