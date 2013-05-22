================
 mixpanel-celery
================

Asynchronous event tracking for Mixpanel
========================================

mixpanel-celery helps you use `Celery`_ to asynchronously track your `Mixpanel`_
events. Waiting on HTTP requests to Mixpanel's api to complete every time you
want to record something slows you down. Using mixpanel-celery gives you all of
the Mixpanel goodness without any of the potential performance impact.

Visit the `mixpanel-celery website`_ or `read the docs`_ for more info.

.. _`Celery`: http://ask.github.com/celery/
.. _`Mixpanel`: http://mixpanel.com/
.. _`mixpanel-celery website`: http://winhamwr.github.io/mixpanel-celery/
.. _`read the docs`: http://mixpanel-celery.readthedocs.org
