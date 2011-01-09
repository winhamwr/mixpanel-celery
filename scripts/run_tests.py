#! /usr/bin/env python

import os
import subprocess
import sys

scripts_dir = os.path.dirname(__file__)
# Add mixpanel to the python path in case we're trying to test before
# installation and because we need to use ``testproj`` for testing
root_dir = os.path.join(scripts_dir, '..')
sys.path.append(root_dir)
# Set DJANGO_SETTINGS_MODULE
os.environ['DJANGO_SETTINGS_MODULE'] = 'testproj.settings'

try:
    import nose
except ImportError:
    print 'nose is required to run the mixpanel test suite'
    sys.exit(1)

try:
    import mixpanel
except ImportError:
    print "Can't find mixpanel to test: %s" % sys.exc_info()[1]
    sys.exit(1)
else:
    print "Mixpanel %s test suite running (Python %s)..." % (
        mixpanel.__version__, sys.version.split()[0])

covered_modules = ['mixpanel']
coverage_opts = ['--with-coverage', '--cover-erase']
for m in covered_modules:
    coverage_opts.append('--cover-package %s' % m)

excluded_tests = []
exclusion_opts = []
for t in excluded_tests:
    exclusion_opts.append('--exclude %s' % t)

opts = ['-v', '--with-id', '--with-doctest', '--with-xunit']

nose_cmd = ['nosetests']

if '--coverage' in sys.argv:
    sys.argv.remove('--coverage')
else:
    coverage_opts = []

if '--failed' in sys.argv:
    sys.argv.remove('--failed')
    opts.insert(1, '--failed')

# If the user didn't specify any modules on the command line, run the default
# modules.
user_args = sys.argv[1:]
cmd = nose_cmd + opts + coverage_opts + user_args
if len([a for a in user_args if not a.startswith('-')]) == 0:
    cmd += exclusion_opts + ['mixpanel']

cmd_string = ' '.join(cmd)
print "Running: [%s]" % cmd_string
subprocess.call(cmd_string, shell=True)
