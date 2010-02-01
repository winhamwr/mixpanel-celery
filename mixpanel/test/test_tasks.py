import unittest
import base64
import simplejson

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

    def test_build_url(self):
        et = EventTracker()

        event = 'foo_event'
        properties = {'token': 'testtoken'}
        params = {'event': event, 'properties': properties}

        url = et._build_url(event, properties)

        expected_data = base64.b64encode(simplejson.dumps(params))

        self.assertEqual('track/?data=%s' % expected_data, url)

    def test_run(self):
        mp_settings.MIXPANEL_API_SERVER = '127.0.0.1'
        mp_settings.MIXPANEL_API_TOKEN = 'bar'

        et = EventTracker()
        result = et.run('event_foo')

        self.assertFalse(result)

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
        mp_settings.MIXPANEL_API_SERVER = '127.0.0.1'
        mp_settings.MIXPANEL_API_TOKEN = 'bar'

        fet = FunnelEventTracker()
        result = fet.run('funnel_foo', '1', '3', {'ip': 'foo'})

        self.assertFalse(result)