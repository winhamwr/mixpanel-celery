from __future__ import absolute_import, unicode_literals

import base64
import json
import logging
import socket
import unittest
import urllib
import urlparse
from datetime import datetime

from mock import call, patch, MagicMock as Mock
try:
    from celery.tests.utils import eager_tasks
except ImportError:
    # Celery 3.1 removed the eager_tasks decorator
    from mixpanel.tests.utils import eager_tasks

from mixpanel.tasks import EventTracker, PeopleTracker, FunnelEventTracker
from mixpanel.conf import settings as mp_settings


class FakeDateTime(datetime):
    "A fake replacement for datetime that can be mocked for testing."
    def __new__(cls, *args, **kwargs):
        return datetime.__new__(datetime, *args, **kwargs)


class TasksTestCase(unittest.TestCase):

    def setUp(self):
        super(TasksTestCase, self).setUp()
        self.patch_network()
        self.set_mp_settings()

    def tearDown(self):
        self.unpatch_network()
        super(TasksTestCase, self).tearDown()

    def set_mp_settings(self):
        mp_settings.MIXPANEL_API_TOKEN = 'testtesttest'
        mp_settings.MIXPANEL_API_SERVER = 'api.mixpanel.com'
        mp_settings.MIXPANEL_TRACKING_ENDPOINT = '/track/'
        mp_settings.MIXPANEL_TEST_PRIORITY = True
        mp_settings.MIXPANEL_DISABLE = False

    def patch_network(self):
        self.old_get_connection = EventTracker._get_connection
        self.conn = Mock()
        EventTracker._get_connection = lambda task: self.conn
        self.response = Mock()
        self.conn.getresponse.return_value = self.response
        self.response.status = 200
        self.response.reason = 'OK'
        self.response.read.return_value = '1'

    def unpatch_network(self):
        EventTracker._get_connection = self.old_get_connection

    def assertParams(self, expected):
        args = self.conn.request.call_args[0]
        self.assertEqual(args[0], 'GET')
        path, qs = args[1].split('?', 1)
        parsed = urlparse.parse_qs(qs, keep_blank_values=True, strict_parsing=True)
        params = json.loads(base64.b64decode(parsed['data'][0]))
        self.assertEqual(params, expected)


class EventTrackerTest(TasksTestCase):

    def test_disable(self):
        et = EventTracker()
        mp_settings.MIXPANEL_DISABLE = True

        def _fake_get_connection():
            assert False, "Should bail out before trying to get a connection."
        et._get_connection = _fake_get_connection

        et('foo')

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

        mp_settings.MIXPANEL_TEST_PRIORITY = False
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
            'data': base64.b64encode(json.dumps(params)),
            'test': is_test,
        })

        self.assertEqual(expected_params, url_params)

    def test_run_properties_None(self):
        result = EventTracker().run('event_foo', None)
        self.assertTrue(result)
        self.assertParams({
            'event': 'event_foo',
            'properties': {'token': 'testtesttest'}
        })

    def test_run_properties_empty(self):
        result = EventTracker().run('event_foo', {})
        self.assertTrue(result)
        self.assertParams({
            'event': 'event_foo',
            'properties': {'token': 'testtesttest'}
        })

    def test_run_properties_foo(self):
        result = EventTracker().run('event_foo', {'foo': 'bar'})
        self.assertTrue(result)
        self.assertParams({
            'event': 'event_foo',
            'properties': {
                'token': 'testtesttest',
                'foo': 'bar',
            }
        })

    def test_non_recorded(self):
        """non-recorded events should return False"""
        self.response.read.return_value = '0'

        et = EventTracker()
        # Times older than 3 hours don't get recorded according to:
        # http://mixpanel.com/api/docs/specification
        # requests will be rejected that are 3 hours older than present time
        # (though actually this is returnin False because of mocking network)
        result = et.run('event_foo', {'time': 1245613885})

        self.assertFalse(result)

    def test_debug_logger(self):
        et = EventTracker()
        result = et.run('event_foo', {}, loglevel=logging.DEBUG)

        self.assertTrue(result)


class PeopleTrackerTest(TasksTestCase):

    @patch('mixpanel.tasks.datetime.datetime', FakeDateTime)
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
        parsed['data'] = json.loads(base64.b64decode(parsed['data']))

        expected_params = {
            u'data': expected,
            u'test': unicode(is_test),
        }

        self.assertEqual(expected_params, parsed)

    def test_build_people_track_ignore_time(self):
        et = PeopleTracker()
        event = 'set'
        is_test = 1
        properties = {'stuff': 'thing', 'blue': 'green',
                      'distinct_id': 'test_id', 'token': 'testtoken',
                      'ignore_time': True}

        expected = {
            '$distinct_id': 'test_id',
            '$ignore_time': True,
            '$set': {
                'stuff': 'thing',
                'blue': 'green',
            },
            '$token': 'testtoken',
        }
        url_params = et._build_params(event, properties, is_test)
        expected_params = urllib.urlencode({
            'data': base64.b64encode(json.dumps(expected)),
            'test': is_test,
        })

        self.assertEqual(expected_params, url_params)

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
            'data': base64.b64encode(json.dumps(expected)),
            'test': is_test,
        })

        self.assertEqual(expected_params, url_params)


class BrokenRequestsTest(TasksTestCase):

    def test_failed_request(self):
        self.response.status = 400
        with eager_tasks():
            result = EventTracker.delay('event_foo')
        self.assertNotEqual(result.traceback, None)

    def test_failed_socket_request(self):
        self.response.read = Mock(side_effect=socket.error('BOOM'))
        with eager_tasks():
            result = EventTracker.delay('event_foo')
        self.assertNotEqual(result.traceback, None)


class FunnelEventTrackerTest(TasksTestCase):

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
