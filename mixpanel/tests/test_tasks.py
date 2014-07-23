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

from mixpanel.tasks import (EventTracker, event_tracker,
                            PeopleTracker, people_tracker,
                            FunnelEventTracker, funnel_tracker)
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

    def get_querystring_dict(self):
        args = self.conn.request.call_args[0]
        self.assertEqual(args[0], 'GET')
        path, qs = args[1].split('?', 1)
        return dict(urlparse.parse_qsl(qs, keep_blank_values=True))

    def assertParams(self, expected):
        parsed = self.get_querystring_dict()
        params = json.loads(base64.b64decode(parsed['data']))
        self.assertEqual(params, expected)


class EventTrackerTest(TasksTestCase):

    def test_disable(self):
        et = EventTracker()
        mp_settings.MIXPANEL_DISABLE = True

        def _fake_get_connection():
            assert False, "Should bail out before trying to get a connection."
        et._get_connection = _fake_get_connection

        et('foo')

    def test_run_priority_default_true(self):
        mp_settings.MIXPANEL_TEST_PRIORITY = True
        result = EventTracker().run('event_foo')
        self.assertTrue(result)
        query = self.get_querystring_dict()
        assert 'test' in query
        self.assertEqual(query['test'], '1')

    def test_run_priority_default_false(self):
        mp_settings.MIXPANEL_TEST_PRIORITY = False
        result = EventTracker().run('event_foo')
        self.assertTrue(result)
        query = self.get_querystring_dict()
        assert 'test' not in query

    def test_run_priority_true(self):
        mp_settings.MIXPANEL_TEST_PRIORITY = False
        result = EventTracker().run('event_foo', test=True)
        self.assertTrue(result)
        query = self.get_querystring_dict()
        assert 'test' in query
        self.assertEqual(query['test'], '1')

    def test_run_priority_false(self):
        mp_settings.MIXPANEL_TEST_PRIORITY = True
        result = EventTracker().run('event_foo', test=False)
        self.assertTrue(result)
        query = self.get_querystring_dict()
        assert 'test' not in query

    def test_build_and_encode_params(self):
        et = EventTracker()

        event = 'foo_event'
        test = True
        properties = {'token': 'testtoken'}
        params = {'event': event, 'properties': properties}

        params = et._build_params(event, properties)
        url_params = et._encode_params(params, test)

        expected_params = urllib.urlencode({
            'data': base64.b64encode(json.dumps(params)),
            'test': '1'
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

    def test_run_token(self):
        result = EventTracker().run('event_foo', token='xxx')
        self.assertTrue(result)
        self.assertParams({
            'event': 'event_foo',
            'properties': {'token': 'xxx'}
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

    def test_instantiated_event_tracker(self):
        result = event_tracker('event_foo')
        self.assertTrue(result)
        self.assertParams({
            'event': 'event_foo',
            'properties': {'token': 'testtesttest'}
        })

    def test_instantiated_event_tracker_delay(self):
        with eager_tasks():
            result = event_tracker.delay('event_foo')
        self.assertTrue(result)
        self.assertParams({
            'event': 'event_foo',
            'properties': {'token': 'testtesttest'}
        })

class PeopleTrackerTest(TasksTestCase):

    @patch('mixpanel.tasks.datetime.datetime', FakeDateTime)
    def test_build_people_track_charge_params(self):
        self.maxDiff = None
        et = PeopleTracker()
        now = datetime.now()
        FakeDateTime.now = classmethod(lambda cls: now)
        event = 'track_charge'
        properties = {'amount': 11.77, 'distinct_id': 'test_id',
                      'extra': 'extra'}
        params = et._build_params(event, properties, token='testtoken')
        expected = {
            '$append': {
                '$transactions': {
                    '$amount': 11.77,
                    '$time': unicode(now.isoformat()),
                    'extra': 'extra'
                }
            },
            '$distinct_id': 'test_id',
            '$token': 'testtoken',
        }
        self.assertEqual(params, expected)

    def test_build_people_track_ignore_time(self):
        et = PeopleTracker()
        event = 'set'
        properties = {'stuff': 'thing', 'blue': 'green',
                      'distinct_id': 'test_id'}
        params = et._build_params(event, properties, token='testtoken',
                                  ignore_time=True)
        expected = {
            '$distinct_id': 'test_id',
            '$ignore_time': True,
            '$set': {
                'stuff': 'thing',
                'blue': 'green',
            },
            '$token': 'testtoken',
        }
        self.assertEqual(params, expected)

    def test_build_people_set_params(self):
        et = PeopleTracker()
        event = 'set'
        properties = {'stuff': 'thing', 'blue': 'green',
                      'distinct_id': 'test_id'}
        params = et._build_params(event, properties, token='testtoken')
        expected = {
            '$distinct_id': 'test_id',
            '$set': {
                'stuff': 'thing',
                'blue': 'green',
            },
            '$token': 'testtoken',
        }
        self.assertEqual(params, expected)

    def test_run_set(self):
        result = PeopleTracker().run('set', {
            'distinct_id': 'x',
            'foo': 'bar',
        })
        self.assertTrue(result)
        self.assertParams({
            '$distinct_id': 'x',
            '$token': 'testtesttest',
            '$set': {'foo': 'bar'},
        })

    def test_run_unset(self):
        result = PeopleTracker().run('unset', ['y', 'z'],
                                     distinct_id='x')
        self.assertTrue(result)
        self.assertParams({
            '$distinct_id': 'x',
            '$token': 'testtesttest',
            '$unset': ['y', 'z'],
        })

    def test_instantiated_people_tracker(self):
        result = people_tracker('set', {
            'distinct_id': 'x',
            'foo': 'bar',
        })
        self.assertTrue(result)
        self.assertParams({
            '$distinct_id': 'x',
            '$token': 'testtesttest',
            '$set': {'foo': 'bar'},
        })

    def test_instantiated_people_tracker_delay(self):
        with eager_tasks():
            result = people_tracker.delay('set', {
                'distinct_id': 'x',
                'foo': 'bar',
            })
        self.assertTrue(result)
        self.assertParams({
            '$distinct_id': 'x',
            '$token': 'testtesttest',
            '$set': {'foo': 'bar'},
        })


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
        self.assertParams({
            'event': 'mp_funnel',
            'properties': {
                'distinct_id': 'test_user',
                'funnel': 'test_funnel',
                'goal': 'test_goal',
                'step': 'test_step',
                'token': 'testtesttest'}
        })

    def test_instantiated_funnel_tracker(self):
        result = funnel_tracker('test_funnel', 'test_step', 'test_goal',
                                {'distinct_id': 'test_user'})
        self.assertTrue(result)
        self.assertParams({
            'event': 'mp_funnel',
            'properties': {
                'distinct_id': 'test_user',
                'funnel': 'test_funnel',
                'goal': 'test_goal',
                'step': 'test_step',
                'token': 'testtesttest'}
        })

    def test_instantiated_funnel_tracker_delay(self):
        with eager_tasks():
            result = funnel_tracker.delay('test_funnel', 'test_step', 'test_goal',
                                          {'distinct_id': 'test_user'})
        self.assertTrue(result)
        self.assertParams({
            'event': 'mp_funnel',
            'properties': {
                'distinct_id': 'test_user',
                'funnel': 'test_funnel',
                'goal': 'test_goal',
                'step': 'test_step',
                'token': 'testtesttest'}
        })
