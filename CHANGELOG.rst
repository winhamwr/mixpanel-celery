Changelog
=========

0.8.0
-----

PeopleTracker features
~~~~~~~~~~~~~~~~~~~~~~

PeopleTracker now supports all the operations: add, append, delete, set,
set_once, union, unset; plus track_charge which provides the same
functionality as the JS API.

PeopleTracker also accepts kwargs for distinct_id, ignore_time, time and
ip. Thanks to Spencer Ellinor for the original pull request #27 to add
ignore_time.

MIXPANEL_DISABLE
~~~~~~~~~~~~~~~~

There's a new setting ``MIXPANEL_DISABLE`` to disable sending events to
Mixpanel, thanks to Carl Meyer.

MIXPANEL_TEST_PRIORITY
~~~~~~~~~~~~~~~~~~~~~~

Back in 2010 Mixpanel changed the meaning of the ``test`` flag from "don't
record this event" to "record this event on a high priority queue."  Our
EventTracker kwarg ``test`` remains as-is (albeit with a different
meaning), but the corresponding setting changed from ``MIXPANEL_TEST_ONLY``
to ``MIXPANEL_TEST_PRIORITY`` to reflect its purpose.

Mocked network in tests
~~~~~~~~~~~~~~~~~~~~~~~

The unit tests used to send network requests to the Mixpanel server. Now
the network is mocked out, so we're not hitting the network, and even
better, we can investigate after a test (with ``assertParams``) to verify
the content of the event as it would have been sent.

0.7.0
-----

PeopleTracker plus plus
~~~~~~~~~~~~~~~~~~~~~~~

Thanks to `Christopher Lambacher <https://github.com/lambacck>`_,
the PeopleTracker API now has 
`documentation <http://mixpanel-celery.readthedocs.org/en/latest/introduction.html#people-tracker-usage>`_.

Even better,
you can now attach your own custom properties
to ``track_charge`` calls,
just as you can with the javascript API.
Thanks Christopher!

0.6.2
-----

Packaging Fix
~~~~~~~~~~~~~

Packaging is hard.
Let's go shopping.
Thanks to Daniel Koepke for the fix!

0.6.1
-----

Back to 0.5.0 logging behavior on retry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If only I had listened to
`past Wes <https://groups.google.com/forum/#!msg/celery-users/TbsqdbYE184/ZO8i0vqbW2wJ>`_,
I would have realized that my retry change would cause excess logging.
You'll no longer get messages logged when an Event fails and is retried.
You'll only be alerted if it reaches max retries.

0.6.0
-----

Celery 3.0 support!
~~~~~~~~~~~~~~~~~~~

And the people rejoiced for no longer needing to maintain their own fork just
to comment out one line. Thanks to the many folks who submitted pull requests
for this one.

Thanks to Nicholas Serra for the pull request.

Mixpanel People API support
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Track your users like they're actual people.

Thanks to Peter Baumgartner for the pull request.

Actual Tests
~~~~~~~~~~~~

We don't need no stinkin tests (yes we did). And now we have them. We're
testing across python 2.6, python 2.7 and starting at Django version ``1.3``
and Celery version ``2.5``. Even better, they're up on travis-ci, so we'll
actually be running them.

Running tests is now easy ::

    $ pip install tox
    $ tox

Thanks to Nicholas Serra for the initial Tox implementation.

Django Context Processor for your Mixpanel API Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Need to use your API key in your templates and want to stay DRY?

Anton Agestam has you covered. Thanks Anton!

Django No Longer Required
~~~~~~~~~~~~~~~~~~~~~~~~~

In version `0.5.0`, we advertised as not requiring Django, but we were totally
full of it. No Django this time. We're serious (except we don't have any tests
proving it, so pull requests would be very welcome).

Thanks to Solomon Bisker for making an honest project out of us.
