import subprocess
import base64
import simplejson
import urlparse

from celery.task import Task
from celery.registry import tasks

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

        request = self._build_request(event, properties)

        return self._send_request(request)

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

    def _build_request(self, event, properties):
        """
        Build an http request to record the given event and properties.
        """
        params = {'event': event, 'properties': properties}
        data = base64.b64encode(simplejson.dumps(params))

        server = mp_settings.MIXPANEL_API_SERVER
        endpoint = mp_settings.MIXPANEL_TRACKING_ENDPOINT
        data_var = mp_settings.MIXPANEL_DATA_VARIABLE

        url = urlparse.urljoin(server, endpoint)
        request = url + '?%s=%s' (data_var, data)

        return request

    def _send_request(self, request):
        """
        Send a an event with its properties to the api server.
        """
        sub = subprocess.Popen(['curl', request], stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE)

tasks.register(EventTracker)

class FunnelEventTracker(EventTracker):
    """
    Task to track a Mixpanel funnel event.
    """

    class InvalidFunnelProperties(Exception):
        """Required properties were missing from the funnel-tracking call"""
        pass

    def run(self, funnel, step, goal, properties=None, token=None):
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

        if not properties.has_key('distinct_id') and not properties.has_key('ip'):
            error_msg = "Either a ``distinct_id`` or ``ip`` property must be given to record a funnel event"
            raise FunnelEventTracker.InvalidFunnelProperties(error_msg)
        properties['funnel'] = funnel
        properties['step'] = step
        properties['goal'] = goal

        request = self._build_request(mp_settings.MIXPANEL_FUNNEL_EVENT_ID,
                                      properties)

        return self._send_request(request)