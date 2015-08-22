#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# license: AGPL, see LICENSE for details. In addition we strongly encourage
#          you to buy us beer if we meet and you like the software.

from setuptools import setup, find_packages

setup(
    name="mapomat",
    version="0.1",
    author="Hermann Blum and Alexander Dietmüller",
    author_email="adietmueller@student.ethz.ch",
    description=("A tool to visualize yelp data."),
    license='MIT',
    platforms=["any"],
    test_suite="amivapi.tests",
    install_requires = [],
    packages=find_packages(),
)
