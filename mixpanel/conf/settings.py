"""Default configuration values and documentation"""

from django.conf import settings
import os

if os.getenv('DJANGO_SETTINGS_MODULE', None) is None:
    settings.configure()

"""
.. data:: MIXPANEL_API_TOKEN

    API token for your Mixpanel account. This configures the Mixpanel account
    where all of the action will be.

    You can find this on the ``API Information`` tab on your
    `mixpanel account page`_

    .. _`mixpanel account page`: http://mixpanel.com/user/account/
"""
MIXPANEL_API_TOKEN = getattr(settings, 'MIXPANEL_API_TOKEN', None)

"""
.. data:: MIXPANEL_RETRY_DELAY

    Number of seconds to wait before retrying an event-tracking request that
    failed because of an invalid server response. These failed responses are
    usually 502's or 504's because Mixpanel is under increased load.

    Defaults to 5 minutes.
"""
MIXPANEL_RETRY_DELAY = getattr(settings, 'MIXPANEL_RETRY_DELAY', 60*5)

"""
.. data:: MIXPANEL_DISABLE

    Set to ``True`` to disable mixpanel-celery; no events will be sent to
    Mixpanel.
"""
MIXPANEL_DISABLE = getattr(settings, 'MIXPANEL_DISABLE', False)

"""
.. data:: MIXPANEL_MAX_RETRIES

    Number of retry attempts to make before raising an exception.

    Defaults to 5 attempts.
"""
MIXPANEL_MAX_RETRIES = getattr(settings, 'MIXPANEL_MAX_RETRIES', 5)

"""
.. data:: MIXPANEL_API_TIMEOUT

    Number of seconds to wait before timing out a request the mixpanel api
    server. The default 30-second timeout can cause your job queue to become
    swamped.

    Defaults to 5 seconds.
"""
MIXPANEL_API_TIMEOUT = getattr(settings, 'MIXPANEL_API_TIMEOUT', 5)

"""
.. data:: MIXPANEL_API_SERVER

    URL for the mixpanel api server. This probably shouldn't change.
"""
MIXPANEL_API_SERVER = getattr(settings, 'MIXPANEL_API_SERVER',
                               'api.mixpanel.com')

"""
.. data:: MIXPANEL_TRACKING_ENDPOINT

    URL endpoint for registering events. defaults to ``/track/``

    Mind the slashes.
"""
MIXPANEL_TRACKING_ENDPOINT = getattr(settings, 'MIXPANEL_TRACKING_ENDPOINT',
                               '/track/')

"""
.. data:: MIXPANEL_PEOPLE_ENDPOINT

    URL endpoint for registering events to the People API.
    defaults to ``/engage/``

    Mind the slashes.
"""
MIXPANEL_PEOPLE_ENDPOINT = getattr(settings, 'MIXPANEL_PEOPLE_ENDPOINT',
                               '/engage/')

"""
.. data:: MIXPANEL_DATA_VARIABLE

    Name of the http GET variable used for transferring property information
    when registering events.
"""
MIXPANEL_DATA_VARIABLE = getattr(settings, 'MIXPANEL_DATA_VARIABLE',
                               'data')


"""
.. data:: MIXPANEL_FUNNEL_EVENT_ID

    The event identifier that indicates that a funnel is being tracked and not
    just a normal event.
"""
MIXPANEL_FUNNEL_EVENT_ID = getattr(settings, 'MIXPANEL_FUNNEL_EVENT_ID',
                               'mp_funnel')

"""
.. data:: MIXPANEL_TEST_PRIORITY

    If this value is True, then events will be sent to Mixpanel with the property
    test = 1 which uses a special high-priority queue.

    http://blog.mixpanel.com/2010/04/22/a-way-to-ease-your-integration-with-mixpanel-while-were-working/
"""
MIXPANEL_TEST_PRIORITY = getattr(settings, 'MIXPANEL_TEST_PRIORITY', False)
