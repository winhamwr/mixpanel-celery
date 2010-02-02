import unittest
import base64
import simplejson
import urllib

from mixpanel.tasks import EventTracker, FunnelEventTracker
from mixpanel.conf import settings as mp_settings

class EventTrackerTest(unittest.TestCase):

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

    def test_build_params(self):
        et = EventTracker()

        event = 'foo_event'
        properties = {'token': 'testtoken'}
        params = {'event': event, 'properties': properties}

        url_params = et._build_params(event, properties)

        expected_params = urllib.urlencode({'data':base64.b64encode(simplejson.dumps(params))})

        self.assertEqual(expected_params, url_params)

    def test_run(self):
        # "correct" result obtained from: http://mixpanel.com/api/docs/console
        mp_settings.MIXPANEL_API_TOKEN = 'testtesttest'

        et = EventTracker()
        result = et.run('event_foo', {'test': 1})

class FunnelEventTrackerTest(unittest.TestCase):
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
        fp = fet._add_funnel_properties(properties, funnel, step, goal)

        # only ip
        properties = {'ip': 'some_ip'}
        fp = fet._add_funnel_properties(properties, funnel, step, goal)

        # both
        properties = {'distinct_id': 'test_distinct_id',
                      'ip': 'some_ip'}
        fp = fet._add_funnel_properties(properties, funnel, step, goal)

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
        mp_settings.MIXPANEL_API_TOKEN = getattr(mp_settings, 'MIXPANEL_API_TOKEN', 'TEST')

        fet = FunnelEventTracker()
        result = fet.run('funnel_foo', '1', '3', {'ip': '127.0.0.1', 'test': 1})