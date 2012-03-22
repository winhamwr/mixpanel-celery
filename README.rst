===========================================================
 mixpanel-celery - Asynchronous event tracking for Mixpanel
===========================================================

Documentation
=============

mixpanel-celery helps you use `Celery`_ to asynchronously track your `Mixpanel`_
events. Waiting on HTTP requests to Mixpanel's api to complete every time you
want to record something slows you down. Using mixpanel-celery gives you all of
the Mixpanel goodness without any of the potential performance impact.

mixpanel-celery works great with Django, but because Celery works with just
python, so does mixpanel-celery.

For full documenation vist the `online mixpanel-celery documentation`_ 
(or build the `sphinx`_ documentation yourself).

This project isn't affiliated with the `Mixpanel`_ company. Just a customer's
implementation of a client for their service.

.. _`Celery`: http://ask.github.com/celery/
.. _`Mixpanel`: http://mixpanel.com/
.. _`sphinx`: http://sphinx.pocoo.org/
.. _`online mixpanel-celery documentation`: http://mixpanel-celery.readthedocs.org