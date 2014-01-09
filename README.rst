================================================
panoramisk. The asterisk's druid
================================================

.. image:: https://travis-ci.org/gawel/panoramisk.png?branch=master
  :target: https://travis-ci.org/gawel/panoramisk
.. image:: https://coveralls.io/repos/gawel/panoramisk/badge.png?branch=master
  :target: https://coveralls.io/r/gawel/panoramisk?branch=master
.. image:: https://pypip.in/v/panoramisk/badge.png
   :target: https://crate.io/packages/panoramisk/
.. image:: https://pypip.in/d/panoramisk/badge.png
   :target: https://crate.io/packages/panoramisk/

`panoramisk` is a library based on python's `asyncio
<http://docs.python.org/dev/library/asyncio.html>`_ to play with `asterisk
<http://www.asterisk.org/community/documentation>`_'s `manager
<https://wiki.asterisk.org/wiki/display/AST/The+Asterisk+Manager+TCP+IP+API>`_.

It use the tcp manager server to listen to events and the http server (``/arawman``) to send actions.

See the api for more informations: https://panoramisk.readthedocs.org/

Source: https://github.com/gawel/panoramisk/

Basic usage::

    >>> from panoramisk import Manager
    >>> manager = Manager()

    >>> def handle_meetme(event, manager):
    ...     # do stuff with the event

    >>> # listen to Meetme* events
    >>> manager.register_event('Meetme*', handle_meetme)

    >>> # call gawel and make him call 0299999999 on reply
    >>> manager.send_action({
    ...     'Action': 'Originate',
    ...     'Channel': 'SIP/gawel',
    ...     'WaitTime': 20,
    ...     'CallerID': 'gawel',
    ...     'Exten': '0299999999',
    ...     'Context': 'default',
    ...     'Priority': 1,
    ... })
