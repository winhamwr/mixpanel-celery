#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import sys
import os

from setuptools import setup, find_packages, Command

import mixpanel

class RunTests(Command):
    description = "Run the test suite from the tests dir."
    user_options = []
    extra_env = {}

    def run(self):
        for env_name, env_value in self.extra_env.items():
            os.environ[env_name] = str(env_value)

        setup_dir = os.path.abspath(os.path.dirname(__file__))
        tests_dir = os.path.join(setup_dir, 'testproj')
        os.chdir(tests_dir)
        sys.path.append(tests_dir)

        try:
            from nose.core import TestProgram
        except ImportError:
            print 'nose is required to run this test suite'
            sys.exit(1)

        print "Mixpanel %s test suite running (Python %s)..." % (
            mixpanel.__version__, sys.version.split()[0])
        args = [
            '-v',
            '--with-id',
            '--with-doctest',
            '--with-coverage', '--cover-erase', '--cover-package', 'mixpanel',
            'mixpanel',
        ]
        TestProgram(argv=args, exit=False)

        os.chdir(setup_dir)
        rabbitmq_msg = "Rabbitmq must be configured with a '/' vhost and "
        rabbitmq_msg += "username/password of 'guest' for all tests to pass"
        print rabbitmq_msg

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

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
    install_requires=['celery>=1.0', 'django>=1.2'],
    tests_require=['nose>=0.11', 'coverage'],
    cmdclass = {'nosetests': RunTests},
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
