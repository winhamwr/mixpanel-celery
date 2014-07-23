from __future__ import absolute_import, unicode_literals

import base64
import datetime
import httplib
import json
import logging
import socket
import urllib

from celery.task import Task
from celery.registry import tasks

from .conf import settings as mp_settings


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

    def run(self, event_name, properties=None, test=None, **kwargs):
        """
        Track an event occurrence to mixpanel through the API.

        ``event_name`` is the string for the event/category you'd like to log
        this event under
        ``properties`` is (optionally) a dictionary of key/value pairs
        describing the event.
        ``token`` is (optionally) your Mixpanel api token. Not required if
        you've already configured your MIXPANEL_API_TOKEN setting.
        ``test`` is an optional override to your
        `:data:mixpanel.conf.settings.MIXPANEL_TEST_PRIORITY` setting for
        putting the events on a high-priority queue at Mixpanel for testing
        purposes.
        """
        l = self.get_logger(**kwargs)
        if mp_settings.MIXPANEL_DISABLE:
            l.info("Mixpanel disabled; not recording event: <%s>" % event_name)
            return False

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

        params = self._build_params(event_name, properties, **kwargs)
        l.debug('params: <%r>' % (params,))

        url_params = self._encode_params(params, test)
        l.debug('encoded: <%s>' % (url_params,))

        conn = self._get_connection()

        try:
            result = self._send_request(conn, url_params)
        except self.FailedEventRequest as e:
            conn.close()
            l.info("Event failed. Retrying: <%s>" % event_name)
            self.retry(
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

    def _get_connection(self):
        server = mp_settings.MIXPANEL_API_SERVER

        # Wish we could use python 2.6's httplib timeout support
        socket.setdefaulttimeout(mp_settings.MIXPANEL_API_TIMEOUT)
        return httplib.HTTPConnection(server)

    def _build_params(self, event, properties, **kwargs):
        """
        Returns the default event format.
        """
        # Avoid overwriting the passed-in properties.
        properties = dict(properties or {})
        properties.setdefault('token', (kwargs.get('token') or
                                        mp_settings.MIXPANEL_API_TOKEN))
        return {'event': event, 'properties': properties}

    def _encode_params(self, params, test):
        """
        Encodes data and returns the urlencoded parameters.
        """
        key = mp_settings.MIXPANEL_DATA_VARIABLE
        value = base64.b64encode(json.dumps(params))
        data = {key: value}
        if test is None:
            test = mp_settings.MIXPANEL_TEST_PRIORITY
        if test:
            data['test'] = '1'
        return urllib.urlencode(data)

    def _send_request(self, connection, params):
        """
        Send a an event with its properties to the api server.

        Returns ``True`` if the event was logged by Mixpanel.
        """

        try:
            connection.request('GET', '%s?%s' % (self.endpoint, params))

            response = connection.getresponse()
        except socket.error, message:
            raise self.FailedEventRequest(
                "The tracking request failed with a socket error. "
                "Message: [%s]" % message
            )

        if response.status != 200 or response.reason != 'OK':
            raise self.FailedEventRequest(
                "The tracking request failed. "
                "Non-200 response code was: "
                "[%s] reason: [%s]" % (response.status, response.reason)
            )

        # Successful requests will generate a log
        response_data = response.read()
        if response_data != '1':
            return False

        return True

event_tracker = EventTracker()


class PeopleTracker(EventTracker):
    name = "mixpanel.tasks.PeopleTracker"
    endpoint = mp_settings.MIXPANEL_PEOPLE_ENDPOINT
    event_map = {
        'add': '$add',
        'append': '$append',
        'delete': '$delete',
        'set': '$set',
        'set_once': '$set_once',
        'track_charge': '$append',
        'union': '$union',
        'unset': '$unset',
    }
    required_params = {
        'token': '$token',
        'distinct_id': '$distinct_id',
    }
    optional_params = {
        'ignore_time': '$ignore_time',
        'time': '$time',
        'ip': '$ip',
    }

    def run(self, event_name, properties=None, **kwargs):
        """
        Track a People event occurrence to mixpanel through the API.

        ``event_name`` is one of the following strings: set, add, track_charge
        ``properties`` a dictionary of key/value pairs to pass to Mixpanel.
        The ``track_charge`` event requires an ``amount`` key.
        May include a ``distinct_id`` key to identify the person
        (deprecated: prefer passing distinct_id as kwarg instead).
        """
        return super(PeopleTracker, self).run(
            event_name,
            properties=properties,
            **kwargs
        )

    def _build_params(self, event, properties, **kwargs):
        """
        Returns the people profile event format.
        """
        if event == 'unset':
            if not isinstance(properties, list):
                raise ValueError("Properties must be a list for unset.")
            unset_props, properties = properties, {}

        # Avoid overwriting the passed-in properties.
        properties = dict(properties or {})

        if event not in self.event_map:
            raise ValueError("Invalid event name: %r (%s)" %
                             (event, ', '.join(self.event_map)))
        op_name = self.event_map[event]

        # Handle distinct_id in props for backward compatibility.
        if 'distinct_id' in properties:
            assert 'distinct_id' not in kwargs or \
                kwargs['distinct_id'] == properties['distinct_id']
            kwargs['distinct_id'] = properties.pop('distinct_id')

        # Default the token before checking required_params.
        kwargs.setdefault('token', mp_settings.MIXPANEL_API_TOKEN)

        if not set(kwargs) >= set(self.required_params):
            raise ValueError("Required kwargs: %s" %
                             ', '.join(self.required_params))

        # Build the params dict.
        params = {}
        for k, v in self.required_params.items():
            params.setdefault(v, kwargs.pop(k))
        for k, v in self.optional_params.items():
            if k in kwargs:
                params.setdefault(v, kwargs.pop(k))

        # Add the operation to params.
        if event == 'track_charge':
            # If time was given as a kwarg, it's already been moved to params
            # as $time. Rescue it from there, and default it otherwise.
            time = params.pop('$time', datetime.datetime.now())
            if hasattr(time, 'isoformat'):
                time = time.isoformat()
            properties['$time'] = time

            # Promote amount to $amount as the JS lib does.
            if 'amount' in properties:
                properties['$amount'] = properties.pop('amount')

            # Demote entire properties dict under $transactions.
            params[op_name] = {'$transactions': properties}

        elif event == 'unset':
            params[op_name] = unset_props

        else:
            params[op_name] = properties

        return params

people_tracker = PeopleTracker()


class FunnelEventTracker(EventTracker):
    """
    Task to track a Mixpanel funnel event.
    """
    name = "mixpanel.tasks.FunnelEventTracker"
    max_retries = mp_settings.MIXPANEL_MAX_RETRIES

    class InvalidFunnelProperties(Exception):
        """Required properties were missing from the funnel-tracking call"""

    def run(self, funnel, step, goal, properties, **kwargs):
        """
        Track an event occurrence to mixpanel through the API.

        ``funnel`` is the string for the funnel you'd like to log
        this event under
        ``step`` the step in the funnel you're registering
        ``goal`` the end goal of this funnel
        ``properties`` is a dictionary of key/value pairs
        describing the funnel event. A ``distinct_id`` is required.
        """
        l = self.get_logger(**kwargs)
        l.info("Recording funnel: <%s>-<%s>" % (funnel, step))

        properties = self._add_funnel_properties(
            properties,
            funnel,
            step,
            goal,
        )

        return super(FunnelEventTracker, self).run(
            mp_settings.MIXPANEL_FUNNEL_EVENT_ID,
            properties,
            **kwargs
        )

    def _add_funnel_properties(self, properties, funnel, step, goal):
        properties = dict(properties or {})
        if 'distinct_id' not in properties:
            raise FunnelEventTracker.InvalidFunnelProperties(
                "A 'distinct_id' must be given to record a funnel event"
            )
        properties['funnel'] = funnel
        properties['step'] = step
        properties['goal'] = goal

        return properties

funnel_tracker = FunnelEventTracker()
