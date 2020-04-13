#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup, find_packages
import setuptools

import prismic

with open("README.md", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name='prismic-httpx',
    version=prismic.__version__,
    description='Asyncio fork of the Python client for prismic.io',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Rémi DEBETTE',
    author_email='remi.debette@gmail.com',
    url='https://github.com/remidebette/prismic-httpx',
    license='Apache 2',
    packages=find_packages(),
    test_suite='tests',
    classifiers=[
        "Development Status :: 4 - Beta",
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=[
        'httpx',
        'aiocache'
    ],
    python_requires='>=3.6'
)
