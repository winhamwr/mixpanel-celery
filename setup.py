# -*- coding: utf-8 -*-
import codecs
import sys
import os

from setuptools import find_packages, setup, Command

long_description = codecs.open("pypi_description.rst", "r", "utf-8").read()

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Framework :: Django",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Topic :: Internet",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

NAME = 'mixpanel-celery'

# Distribution Meta stuff because importing the module on install is bad
# Mostly cribbed from Celery's setup.py

import re

# Standard ``__foo__ = 'bar'`` pairs.
re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')
# VERSION tuple
re_vers = re.compile(r'VERSION\s*=\s*\((.*?)\)')
# Module docstring
re_doc = re.compile(r'^"""(.+?)"""')
# We don't need the quotes
rq = lambda s: s.strip("\"'")


def add_default(m):
    """
    Get standard ``__foo__ = 'bar'`` pairs as a (foo, bar) tuple.
    """
    attr_name, attr_value = m.groups()
    return ((attr_name, rq(attr_value)), )


def add_version(m):
    v = list(map(rq, m.groups()[0].split(', ')))
    return (('VERSION', '.'.join(v[0:3]) + ''.join(v[3:])), )


def add_doc(m):
    """
    Grab the module docstring
    """
    return (('doc', m.groups()[0]), )

pats = {
    re_meta: add_default,
    re_vers: add_version,
    re_doc: add_doc,
}

here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, 'mixpanel/__init__.py'))

# Parse out the package meta information from the __init__ using *shudder*
# regexes
meta = {}
try:
    for line in meta_fh:
        if line.strip() == '# -eof meta-':
            break
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))
finally:
    meta_fh.close()

# -*- Installation Requires -*-


def strip_comments(l):
    return l.split('#', 1)[0].strip()


def reqs(*f):
    return list(filter(None, [strip_comments(l) for l in open(
        os.path.join(os.getcwd(), 'requirements', *f)).readlines()]))

install_requires = reqs('default.txt')

# -*- Test Runners -*-


class RunDjangoTests(Command):
    description = 'Run the django test suite from the tests dir.'
    user_options = []
    extra_env = {}
    extra_args = []

    def run(self):
        for env_name, env_value in self.extra_env.items():
            os.environ[env_name] = str(env_value)

        this_dir = os.getcwd()
        django_testproj_dir = os.path.join(this_dir, 'testproj')
        os.chdir(django_testproj_dir)
        sys.path.append(django_testproj_dir)

        from django.core.management import execute_manager
        os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get(
            'DJANGO_SETTINGS_MODULE',
            'testproj.settings',
        )
        settings_file = os.environ['DJANGO_SETTINGS_MODULE']
        settings_mod = __import__(settings_file, {}, {}, [''])
        prev_argv = list(sys.argv)
        try:
            sys.argv = [__file__, 'test'] + self.extra_args
            execute_manager(settings_mod, argv=sys.argv)
        finally:
            sys.argv = prev_argv

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

setup(
    name=NAME,
    version=meta['VERSION'],
    description=meta['doc'],
    author=meta['author'],
    author_email=meta['contact'],
    url=meta['homepage'],
    long_description=long_description,
    packages=find_packages(exclude=["*.tests", "*.tests.*"]),
    license='BSD',
    platforms=['any'],
    classifiers=CLASSIFIERS,
    cmdclass={
        'test': RunDjangoTests,
    },
    install_requires=install_requires,
)
