# Django settings for testproj project.

import os

here = os.path.abspath(os.path.dirname(__file__))

ROOT_URLCONF = "testproj.urls"

DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_TZ = True
TIME_ZONE = 'UTC'
SITE_ID = 1
SECRET_KEY = 'testmixpanel'
ADMINS = ()
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(here, 'mpcelery-test-db'),
        'USER': '',
        'PASSWORD': '',
        'PORT': '',
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'djcelery',
    'mixpanel',
    'django_nose',
)

NOSE_ARGS = [
    os.path.join(here, os.pardir, 'mixpanel', 'tests'),
    os.environ.get("NOSE_VERBOSE") and "--verbose" or "",
]
TEST_RUNNER = 'django_nose.run_tests'

MIXPANEL_API_TOKEN = 'testmixpanel'

# Celery Configuration
BROKER_URL = 'memory://'
BROKER_CONNECTION_TIMEOUT = 1
BROKER_CONNECTION_RETRY = False
BROKER_CONNECTION_MAX_RETRIES = 1
# The default BROKER_POOL_LIMIT is 10, broker connections are not
# properly cleaned up on error, so the tests will run out of
# connections and result in one test hanging forever
# To prevent that, just disable it
BROKER_POOL_LIMIT = 0
CELERY_RESULT_BACKEND = 'cache'
CELERY_CACHE_BACKEND = 'locmem://'

CELERY_SEND_TASK_ERROR_EMAILS = False

import djcelery
djcelery.setup_loader()
