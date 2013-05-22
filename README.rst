================
 mixpanel-celery
================

Asynchronous event tracking for Mixpanel
========================================

.. image:: https://travis-ci.org/winhamwr/mixpanel-celery.png?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/winhamwr/mixpanel-celery

mixpanel-celery helps you use `Celery`_ to asynchronously track your `Mixpanel`_
events. Waiting on HTTP requests to Mixpanel's api to complete every time you
want to record something slows you down. Using mixpanel-celery gives you all of
the Mixpanel goodness without any of the potential performance impact.

Works wherever Celery works
===========================

mixpanel-celery works great with Django, but because Celery works with just
python, so does mixpanel-celery.

But how do I do the thing?
==========================

I'll tell you how! Have Celery running and want to asynchronously track an
event called ``my_event`` right the heck now?

.. code-block:: python

    from mixpanel.tasks import EventTracker

    EventTracker.delay(
        'my_event',
        {'distinct_id': 1},
        token='YOUR_API_TOKEN',
    )

Boom. Once your Celery worker gets hold of that bad boy, it's tracked.

Full-on Docs
============

For full documenation vist the `online mixpanel-celery documentation`_
(or build the `sphinx`_ documentation yourself).

We like Mixpanel and Celery
===========================

This project isn't affiliated with the `Mixpanel`_ company. Just a customer's
implementation of a client for their service.

.. _`Celery`: http://ask.github.com/celery/
.. _`Mixpanel`: http://mixpanel.com/
.. _`sphinx`: http://sphinx.pocoo.org/
.. _`online mixpanel-celery documentation`: http://mixpanel-celery.readthedocs.org
