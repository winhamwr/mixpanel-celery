import httplib
import urllib
import base64
import simplejson
import urlparse

from celery.task import Task
from celery.registry import tasks, AlreadyRegistered

from mixpanel.conf import settings as mp_settings

class EventTracker(Task):
    """
    Task to track a Mixpanel event.
    """

    def run(self, event_name, properties=None, token=None):
        """
        Track an event occurrence to mixpanel through the API.

        ``event_name`` is the string for the event/category you'd like to log
        this event under
        ``properties`` is (optionally) a dictionary of key/value pairs
        describing the event.
        ``token`` is (optionally) your Mixpanel api token. Not required if
        you've already configured your MIXPANEL_API_TOKEN setting.
        """
        properties = self._handle_properties(properties, token)

        url_params = self._build_params(event_name, properties)
        conn = self._get_connection()

        return self._send_request(conn, url_params)

    def _handle_properties(self, properties, token):
        """
        Build a properties dictionary, accounting for the token.
        """
        if properties == None:
            properties = {}
        if token == None:
            token = mp_settings.MIXPANEL_API_TOKEN

        if token not in properties:
            properties['token'] = token

        return properties

    def _get_connection(self):
        server = mp_settings.MIXPANEL_API_SERVER

        return httplib.HTTPConnection(server)

    def _build_params(self, event, properties):
        """
        Build HTTP params to record the given event and properties.
        """
        params = {'event': event, 'properties': properties}
        data = base64.b64encode(simplejson.dumps(params))

        data_var = mp_settings.MIXPANEL_DATA_VARIABLE
        url_params = urllib.urlencode({data_var: data})

        self.url_params = url_params

        return url_params

    def _send_request(self, connection, params):
        """
        Send a an event with its properties to the api server.

        Returns ``true`` if the response had a 200 status.
        """
        endpoint = mp_settings.MIXPANEL_TRACKING_ENDPOINT
        connection.request('GET', endpoint, params)

        response = connection.getresponse()
        if response.status != 200:
            return False

        # Successful requests will generate a log
        response_data = response.read()
        if response_data != '1':
            return False

        return True

tasks.register(EventTracker)

class FunnelEventTracker(EventTracker):
    """
    Task to track a Mixpanel funnel event.
    """

    class InvalidFunnelProperties(Exception):
        """Required properties were missing from the funnel-tracking call"""
        pass

    def run(self, funnel, step, goal, properties, token=None):
        """
        Track an event occurrence to mixpanel through the API.

        ``funnel`` is the string for the funnel you'd like to log
        this event under
        ``step`` the step in the funnel you're registering
        ``goal`` the end goal of this funnel
        ``properties`` is (optionally) a dictionary of key/value pairs
        describing the funnel event.
        ``token`` is (optionally) your Mixpanel api token. Not required if
        you've already configured your MIXPANEL_API_TOKEN setting.
        """
        properties = self._handle_properties(properties, token)

        properties = self._add_funnel_properties(properties, funnel, step, goal)

        url_params = self._build_params(mp_settings.MIXPANEL_FUNNEL_EVENT_ID, properties)
        conn = self._get_connection()

        return self._send_request(conn, url_params)

    def _add_funnel_properties(self, properties, funnel, step, goal):
        if not properties.has_key('distinct_id') and not properties.has_key('ip'):
            error_msg = "Either a ``distinct_id`` or ``ip`` property must be given to record a funnel event"
            raise FunnelEventTracker.InvalidFunnelProperties(error_msg)
        properties['funnel'] = funnel
        properties['step'] = step
        properties['goal'] = goal

        return properties


try:
    tasks.register(FunnelEventTracker)
except AlreadyRegistered:
    pass
