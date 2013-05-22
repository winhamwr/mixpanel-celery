Changelog
=========

0.6.1
-----

Back to 0.5.0 logging behavior on retry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If only I had listened to
[past Wes](https://groups.google.com/forum/#!msg/celery-users/TbsqdbYE184/ZO8i0vqbW2wJ),
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
