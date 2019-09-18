# coding: utf-8

import io
from os import path

from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))

with io.open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='outplan',

    version='1.2.0',

    description='Support nested experiment/namespace base on Facebook Planout',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/xiachufang/outplan',

    author='x1ah',
    author_email='gaoxiaoqiang@xiachufang.com',
    packages=find_packages(exclude=['docs', 'tests*']),

    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Chinese (Simplified)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'simplejson',
        'planout',
        'typing; python_version < "3.5"'
    ],
    include_package_data=True
)
