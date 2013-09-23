import base64
import datetime
import httplib
import json
import logging
import socket
import urllib

from celery.task import Task
from celery.registry import tasks

from mixpanel.conf import settings as mp_settings


class EventTracker(Task):
    """
    Task to track a Mixpanel event.
    """
    name = "mixpanel.tasks.EventTracker"
    max_retries = mp_settings.MIXPANEL_MAX_RETRIES
    endpoint = mp_settings.MIXPANEL_TRACKING_ENDPOINT

    class FailedEventRequest(Exception):
        """
        The attempted recording event failed because of a non-200 HTTP return
        code.
        """

    def run(
        self, event_name, properties=None, token=None, test=None, **kwargs
    ):
        """
        Track an event occurrence to mixpanel through the API.

        ``event_name`` is the string for the event/category you'd like to log
        this event under
        ``properties`` is (optionally) a dictionary of key/value pairs
        describing the event.
        ``token`` is (optionally) your Mixpanel api token. Not required if
        you've already configured your MIXPANEL_API_TOKEN setting.
        ``test`` is an optional override to your
        `:data:mixpanel.conf.settings.MIXPANEL_TEST_ONLY` setting for
        determining if the event requests should actually be stored on the
        Mixpanel servers.
        """
        l = self.get_logger(**kwargs)
        l.info("Recording event: <%s>" % event_name)

        # Celery 3.x changed the way the logger could be accessed
        if hasattr(l, 'getEffectiveLevel'):
            # celery 3.x
            effective_level = l.getEffectiveLevel()
        else:
            # Fall back to celery 2.x support
            effective_level = l.logger.getEffectiveLevel()

        if effective_level == logging.DEBUG:
            httplib.HTTPConnection.debuglevel = 1

        is_test = self._is_test(test)
        generated_properties = self._handle_properties(properties, token)

        url_params = self._build_params(
            event_name,
            generated_properties,
            is_test,
        )
        l.debug("url_params: <%s>" % url_params)
        conn = self._get_connection()

        try:
            result = self._send_request(conn, url_params)
        except EventTracker.FailedEventRequest as e:
            conn.close()
            l.info("Event failed. Retrying: <%s>" % event_name)
            EventTracker.retry(
                exc=e,
                countdown=mp_settings.MIXPANEL_RETRY_DELAY,
            )
            return
        conn.close()
        if result:
            l.info("Event recorded/logged: <%s>" % event_name)
        else:
            l.info("Event ignored: <%s>" % event_name)

        return result

    def _is_test(self, test):
        """
        Determine whether this event should be logged as a test request,
        meaning it won't actually be stored on the Mixpanel servers. A return
        result of 1 means this will be a test, 0 means it won't as per the API
        spec.

        Uses ``:mod:mixpanel.conf.settings.MIXPANEL_TEST_ONLY`` as the default
        if no explicit test option is given.
        """
        if test == None:
            test = mp_settings.MIXPANEL_TEST_ONLY

        if test:
            return 1
        return 0

    def _handle_properties(self, properties, token):
        """
        Build a properties dictionary, accounting for the token.
        """
        if properties == None:
            properties = {}

        if not properties.get('token', None):
            if token is None:
                token = mp_settings.MIXPANEL_API_TOKEN
            properties['token'] = token

        l = self.get_logger()
        l.debug('pre-encoded properties: <%s>' % repr(properties))

        return properties

    def _get_connection(self):
        server = mp_settings.MIXPANEL_API_SERVER

        # Wish we could use python 2.6's httplib timeout support
        socket.setdefaulttimeout(mp_settings.MIXPANEL_API_TIMEOUT)
        return httplib.HTTPConnection(server)

    def _build_params(self, event, properties, is_test):
        """
        Build HTTP params to record the given event and properties.
        """
        params = {'event': event, 'properties': properties}
        return self._encode_params(params, is_test)

    def _encode_params(self, params, is_test):
        """
        Encodes data and returns the urlencoded parameters
        """
        data = base64.b64encode(json.dumps(params))

        data_var = mp_settings.MIXPANEL_DATA_VARIABLE
        return urllib.urlencode({data_var: data, 'test': is_test})

    def _send_request(self, connection, params):
        """
        Send a an event with its properties to the api server.

        Returns ``true`` if the event was logged by Mixpanel.
        """

        try:
            connection.request('GET', '%s?%s' % (self.endpoint, params))

            response = connection.getresponse()
        except socket.error, message:
            raise EventTracker.FailedEventRequest(
                "The tracking request failed with a socket error. "
                "Message: [%s]" % message
            )

        if response.status != 200 or response.reason != 'OK':
            raise EventTracker.FailedEventRequest(
                "The tracking request failed. "
                "Non-200 response code was: "
                "[%s] reason: [%s]" % (response.status, response.reason)
            )

        # Successful requests will generate a log
        response_data = response.read()
        if response_data != '1':
            return False

        return True

tasks.register(EventTracker)


class PeopleTracker(EventTracker):
    endpoint = mp_settings.MIXPANEL_PEOPLE_ENDPOINT
    event_map = {
        'set': '$set',
        'add': '$increment',
        'track_charge': '$append',
    }

    def run(
        self, event_name, properties=None, token=None, test=None, **kwargs
    ):
        """
        Track an People event occurrence to mixpanel through the API.

        ``event_name`` is one of the following strings: set, add, track_charge
        ``properties`` a dictionary of key/value pairs to pass to Mixpanel.
        Must include a ``distinct_id`` key to identify the person.
        The ``track_charge`` event requires an ``amount`` key.
        ``token`` is (optionally) your Mixpanel api token. Not required if
        you've already configured your MIXPANEL_API_TOKEN setting.
        ``test`` is an optional override to your
        `:data:mixpanel.conf.settings.MIXPANEL_TEST_ONLY` setting for
        determining if the event requests should actually be stored on the
        Mixpanel servers.
        """
        return super(PeopleTracker, self).run(
            event_name,
            properties=properties,
            token=token,
            test=test,
            **kwargs
        )

    def _build_params(self, event, properties, is_test):
        """
        Build HTTP params to record the given event and properties.
        """
        mp_key = self.event_map[event]
        params = {
            '$token': properties['token'],
            '$distinct_id': properties['distinct_id'],
        }
        if event == 'track_charge':
            time = properties.get('time', datetime.datetime.now().isoformat())
            transactions = dict(
                (k, v) for (k, v) in properties.iteritems()
                if not k in ('token', 'distinct_id', 'amount')
            )

            transactions['$time'] = time
            transactions['$amount'] = properties['amount']
            params[mp_key] = {'$transactions': transactions}

        else:
            # strip token and distinct_id out of the properties and use the
            # rest for passing with $set and $increment
            params[mp_key] = dict(
                (k, v) for (k, v) in properties.iteritems()
                if not k in ('token', 'distinct_id')
            )

        return self._encode_params(params, is_test)

tasks.register(PeopleTracker)


class FunnelEventTracker(EventTracker):
    """
    Task to track a Mixpanel funnel event.
    """
    name = "mixpanel.tasks.FunnelEventTracker"
    max_retries = mp_settings.MIXPANEL_MAX_RETRIES

    class InvalidFunnelProperties(Exception):
        """Required properties were missing from the funnel-tracking call"""
        pass

    def run(
        self, funnel, step, goal, properties, token=None, test=None, **kwargs
    ):
        """
        Track an event occurrence to mixpanel through the API.

        ``funnel`` is the string for the funnel you'd like to log
        this event under
        ``step`` the step in the funnel you're registering
        ``goal`` the end goal of this funnel
        ``properties`` is a dictionary of key/value pairs
        describing the funnel event. A ``distinct_id`` is required.
        ``token`` is (optionally) your Mixpanel api token. Not required if
        you've already configured your MIXPANEL_API_TOKEN setting.
        ``test`` is an optional override to your
        `:data:mixpanel.conf.settings.MIXPANEL_TEST_ONLY` setting for
        determining if the event requests should actually be stored on the
        Mixpanel servers.
        """
        l = self.get_logger(**kwargs)
        l.info("Recording funnel: <%s>-<%s>" % (funnel, step))
        properties = self._handle_properties(properties, token)

        is_test = self._is_test(test)
        properties = self._add_funnel_properties(
            properties,
            funnel,
            step,
            goal,
        )

        url_params = self._build_params(
            mp_settings.MIXPANEL_FUNNEL_EVENT_ID,
            properties,
            is_test,
        )
        l.debug("url_params: <%s>" % url_params)
        conn = self._get_connection()

        try:
            result = self._send_request(conn, url_params)
        except EventTracker.FailedEventRequest as e:
            conn.close()
            l.info("Funnel failed. Retrying: <%s>-<%s>" % (funnel, step))
            FunnelEventTracker.retry(
                exc=e,
                countdown=mp_settings.MIXPANEL_RETRY_DELAY,
            )
            return
        conn.close()
        if result:
            l.info("Funnel recorded/logged: <%s>-<%s>" % (funnel, step))
        else:
            l.info("Funnel ignored: <%s>-<%s>" % (funnel, step))

        return result

    def _add_funnel_properties(self, properties, funnel, step, goal):
        if 'distinct_id' not in properties:
            raise FunnelEventTracker.InvalidFunnelProperties(
                "A 'distinct_id' must be given to record a funnel event"
            )
        properties['funnel'] = funnel
        properties['step'] = step
        properties['goal'] = goal

        return properties

tasks.register(FunnelEventTracker)
