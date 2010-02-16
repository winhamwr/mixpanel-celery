===========================================================
 mixpanel-celery - Asynchronous event tracking for Mixpanel
===========================================================

Documentation
=============

mixpanel-celery helps you use `Celery`_ to asynchronously track your `Mixpanel`_
events. You want to perform your tracking asynchronously, because waiting for HTTP
requests to Mixpanel to complete every time you want to record something important
isn't ideal when you've already worked so hard to tune your performance.

mixpanel-celery works great with Django, but because Celery works with just
python, so does mixpanel-celery.

For full documenation, you can build the `sphinx`_ documentation yourself or
vist the `online mixpanel-celery documentation`_

This project isn't affiliated with the `Mixpanel`_ company. Just a customer's
implementation of a client for their service.

.. _`Celery`: http://ask.github.com/celery/
.. _`Mixpanel`: http://mixpanel.com/
.. _`sphinx`: http://sphinx.pocoo.org/
.. _`online mixpanel-celery documentation`: http://winhamwr.github.com/mixpanel-celery/