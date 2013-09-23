import base64
import logging
import unittest
import urllib
import urlparse
from datetime import datetime

import mock
from celery.tests.utils import eager_tasks
from django.utils import simplejson

from mixpanel.tasks import EventTracker, PeopleTracker, FunnelEventTracker
from mixpanel.conf import settings as mp_settings


class FakeDateTime(datetime):
    "A fake replacement for datetime that can be mocked for testing."
    def __new__(cls, *args, **kwargs):
        return datetime.__new__(datetime, *args, **kwargs)


class EventTrackerTest(unittest.TestCase):
    def setUp(self):
        mp_settings.MIXPANEL_API_TOKEN = 'testtesttest'
        mp_settings.MIXPANEL_API_SERVER = 'api.mixpanel.com'
        mp_settings.MIXPANEL_TRACKING_ENDPOINT = '/track/'
        mp_settings.MIXPANEL_TEST_ONLY = True

    def test_handle_properties_w_token(self):
        et = EventTracker()

        properties = et._handle_properties({}, 'foo')
        self.assertEqual('foo', properties['token'])

    def test_handle_properties_no_token(self):
        et = EventTracker()
        mp_settings.MIXPANEL_API_TOKEN = 'bar'

        properties = et._handle_properties({}, None)
        self.assertEqual('bar', properties['token'])

    def test_handle_properties_empty(self):
        et = EventTracker()
        mp_settings.MIXPANEL_API_TOKEN = 'bar'

        properties = et._handle_properties(None, None)
        self.assertEqual('bar', properties['token'])

    def test_handle_properties_given(self):
        et = EventTracker()

        properties = et._handle_properties({'token': 'bar'}, None)
        self.assertEqual('bar', properties['token'])

        properties = et._handle_properties({'token': 'bar'}, 'foo')
        self.assertEqual('bar', properties['token'])

    def test_is_test(self):
        et = EventTracker()

        self.assertEqual(et._is_test(None), 1)
        self.assertEqual(et._is_test(False), 0)
        self.assertEqual(et._is_test(True), 1)

        mp_settings.MIXPANEL_TEST_ONLY = False
        self.assertEqual(et._is_test(None), 0)
        self.assertEqual(et._is_test(False), 0)
        self.assertEqual(et._is_test(True), 1)

    def test_build_params(self):
        et = EventTracker()

        event = 'foo_event'
        is_test = 1
        properties = {'token': 'testtoken'}
        params = {'event': event, 'properties': properties}

        url_params = et._build_params(event, properties, is_test)

        expected_params = urllib.urlencode({
            'data': base64.b64encode(simplejson.dumps(params)),
            'test': is_test,
        })

        self.assertEqual(expected_params, url_params)

    @mock.patch('mixpanel.tasks.datetime.datetime', FakeDateTime)
    def test_build_people_track_charge_params(self):
        self.maxDiff = None
        et = PeopleTracker()
        now = datetime.now()
        FakeDateTime.now = classmethod(lambda cls: now)
        event = u'track_charge'
        is_test = 1
        properties = {u'amount': 11.77, u'distinct_id': u'test_id',
                      u'token': u'testtoken', u'extra': u'extra'}
        expected = {
            u'$append': {
                u'$transactions': {
                    u'$amount': 11.77,
                    u'$time': unicode(now.isoformat()),
                    u'extra': 'extra'
                }
            },
            u'$distinct_id': u'test_id',
            u'$token': u'testtoken',
        }
        url_params = et._build_params(event, properties, is_test)
        parsed = dict(urlparse.parse_qsl(url_params, True))
        parsed[u'data'] = simplejson.loads(base64.b64decode(parsed['data']))

        expected_params = {
            u'data': expected,
            u'test': unicode(is_test),
        }

        self.assertEqual(expected_params, parsed)

    def test_build_people_set_params(self):
        et = PeopleTracker()
        event = 'set'
        is_test = 1
        properties = {'stuff': 'thing', 'blue': 'green',
                      'distinct_id': 'test_id', 'token': 'testtoken'}
        expected = {
            '$distinct_id': 'test_id',
            '$set': {
                'stuff': 'thing',
                'blue': 'green',
            },
            '$token': 'testtoken',
        }
        url_params = et._build_params(event, properties, is_test)
        expected_params = urllib.urlencode({
            'data': base64.b64encode(simplejson.dumps(expected)),
            'test': is_test,
        })

        self.assertEqual(expected_params, url_params)

    def test_run(self):
        # "correct" result obtained from: http://mixpanel.com/api/docs/console
        et = EventTracker()
        result = et.run('event_foo', {})

        self.assertTrue(result)

    def test_old_run(self):
        """non-recorded events should return False"""
        et = EventTracker()
        # Times older than 3 hours don't get recorded according to:
        # http://mixpanel.com/api/docs/specification
        # requests will be rejected that are 3 hours older than present time
        result = et.run('event_foo', {'time': 1245613885})

        self.assertFalse(result)

    def test_debug_logger(self):
        et = EventTracker()
        result = et.run('event_foo', {}, loglevel=logging.DEBUG)

        self.assertTrue(result)


class BrokenRequestsTest(unittest.TestCase):

    def setUp(self):
        mp_settings.MIXPANEL_API_TOKEN = 'testtesttest'
        mp_settings.MIXPANEL_TEST_ONLY = True
        mp_settings.MIXPANEL_API_SERVER = 'api.mixpanel.com'
        mp_settings.MIXPANEL_TRACKING_ENDPOINT = '/track/'
        EventTracker.endpoint = mp_settings.MIXPANEL_TRACKING_ENDPOINT

    def tearDown(self):
        EventTracker.endpoint = mp_settings.MIXPANEL_TRACKING_ENDPOINT

    def test_failed_request(self):
        EventTracker.endpoint = 'brokenurl'

        with eager_tasks():
            result = EventTracker.delay('event_foo')

        self.assertNotEqual(result.traceback, None)

    def test_failed_socket_request(self):
        mp_settings.MIXPANEL_API_SERVER = '127.0.0.1:60000'

        with eager_tasks():
            result = EventTracker.delay('event_foo')
        self.assertNotEqual(result.traceback, None)


class FunnelEventTrackerTest(unittest.TestCase):
    def setUp(self):
        mp_settings.MIXPANEL_API_TOKEN = 'testtesttest'
        mp_settings.MIXPANEL_API_SERVER = 'api.mixpanel.com'
        mp_settings.MIXPANEL_TRACKING_ENDPOINT = '/track/'
        mp_settings.MIXPANEL_TEST_ONLY = True

    def test_afp_validation(self):
        fet = FunnelEventTracker()

        funnel = 'test_funnel'
        step = 'test_step'
        goal = 'test_goal'

        # neither
        properties = {}
        self.assertRaises(FunnelEventTracker.InvalidFunnelProperties,
                          fet._add_funnel_properties,
                          properties, funnel, step, goal)

        # only distinct
        properties = {'distinct_id': 'test_distinct_id'}
        fet._add_funnel_properties(properties, funnel, step, goal)

        # only ip
        properties = {'ip': 'some_ip'}
        self.assertRaises(FunnelEventTracker.InvalidFunnelProperties,
                          fet._add_funnel_properties,
                          properties, funnel, step, goal)

        # both
        properties = {'distinct_id': 'test_distinct_id',
                      'ip': 'some_ip'}
        fet._add_funnel_properties(properties, funnel, step, goal)

    def test_afp_properties(self):
        fet = FunnelEventTracker()

        funnel = 'test_funnel'
        step = 'test_step'
        goal = 'test_goal'

        properties = {'distinct_id': 'test_distinct_id'}

        funnel_properties = fet._add_funnel_properties(properties, funnel,
                                                       step, goal)

        self.assertEqual(funnel_properties['funnel'], funnel)
        self.assertEqual(funnel_properties['step'], step)
        self.assertEqual(funnel_properties['goal'], goal)

    def test_run(self):
        funnel = 'test_funnel'
        step = 'test_step'
        goal = 'test_goal'

        fet = FunnelEventTracker()
        result = fet.run(funnel, step, goal, {'distinct_id': 'test_user'})

        self.assertTrue(result)
