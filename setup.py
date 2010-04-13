#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import sys
import os

from setuptools import setup, find_packages, Command

import mixpanel

long_description = codecs.open("README.rst", "r", "utf-8").read()

setup(
    name='mixpanel-celery',
    version=mixpanel.__version__,
    description=mixpanel.__doc__,
    author=mixpanel.__author__,
    author_email=mixpanel.__contact__,
    url=mixpanel.__homepage__,
    platforms=["any"],
    license="BSD",
    packages=find_packages(),
    scripts=[],
    zip_safe=False,
    install_requires=['celery>=1.0.0'],
    cmdclass = {},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description=long_description,
)