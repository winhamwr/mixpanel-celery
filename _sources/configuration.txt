===========================
Configuring mixpanel-celery
===========================

Mixpanel-celery's configuration looks a lot like `Celery`_'s configuration. All
of the configuration directives will go in the same file you're using to
configure `Celery`_.

If you’re using celery in a Django project these settings should be defined in
your projects ``settings.py`` file.

In a regular Python environment using the default loader you must create the
``celeryconfig.py`` module and make sure it is available on the Python path.

Full instructions on settings up your `Celery`_ configuration are located at the
`Celery Configuration Docs`_ page.


Configuration Options
=====================

* MIXPANEL_API_TOKEN
    As the name suggests, this is the `Mixpanel`_ api token for your Mixpanel
    account. All events that you track/register will take place on this account.

.. _`Mixpanel`: http://mixpanel.com/
.. _`Celery`: http://ask.github.com/celery/
.. _`Celery Configuration Docs`: http://ask.github.com/celery/configuration.html
