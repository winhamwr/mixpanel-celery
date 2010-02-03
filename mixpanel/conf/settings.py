"""Default configuration values and documentation"""

from django.conf import settings

"""
.. data:: MIXPANEL_API_TOKEN

    API token for your Mixpanel account. This configures the Mixpanel account
    where all of the action will be.

    You can find this on the ``API Information`` tab on your
    `mixpanel account page`_

    .. _`mixpanel account page`: http://mixpanel.com/user/account/
"""
MIXPANEL_API_TOKEN = getattr(settings, 'MIXPANEL_API_TOKEN')

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
.. data:: MIXPANEL_TEST_ONLY

    If this value is True, then events will be sent to Mixpanel with the property
    test = 1 so that no events will actually be logged.
"""
MIXPANEL_TEST_ONLY = getattr(settings, 'MIXPANEL_TEST_ONLY', False)
