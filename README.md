# mixpanel-celery

Asynchronous event tracking for Mixpanel

[![Build Status](https://travis-ci.org/winhamwr/mixpanel-celery.png?branch=master)](https://travis-ci.org/winhamwr/mixpanel-celery)

mixpanel-celery helps you use [Celery](http://celeryproject.org)
to asynchronously track your
[Mixpanel](http://mixpanel.com) events.
Waiting on HTTP requests to Mixpanel's api to complete
every time you want to record something slows you down.
Using mixpanel-celery gives you all of the Mixpanel goodness
without any of the potential performance impact.

## Works wherever Celery works

mixpanel-celery works great with Django,
but because Celery works with just python,
so does mixpanel-celery.

## But how do I do the thing?

I'll tell you how!
Have Celery running and want to asynchronously track an event?
Is your event called `my_event`?
You're in luck!

    from mixpanel.tasks import EventTracker

    EventTracker.delay(
        'my_event',
        {'distinct_id': 1},
        token='YOUR_API_TOKEN',
    )

Boom.
Once your Celery worker gets hold of that bad boy, it's tracked.

## Full-on Docs

Would you like to know more?
Well then you should [read the docs](http://mixpanel-celery.readthedocs.org),
[citizen](http://tvtropes.org/pmwiki/pmwiki.php/Film/StarshipTroopers).

## We like Mixpanel and Celery

This project isn't affiliated with the Mixpanel company.
Just a customer's implementation of a client for their service.
