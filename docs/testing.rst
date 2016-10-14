=========================
:mod:`panoramisk.testing`
=========================

..
    >>> import os
    >>> stream = os.path.join('tests', 'fixtures', 'ping.yaml')

.. code-block:: python

    >>> from panoramisk import testing
    >>> manager = testing.Manager(stream=stream)  # stream is a filename containing an Asterisk trace
    >>> future = manager.send_action({'Action': 'Ping'})
    >>> resp = future.result()
    >>> assert 'ping' in resp
    >>> assert resp.ping == 'Pong'

.. automodule:: panoramisk.testing

.. autoclass:: Manager
   :members:
