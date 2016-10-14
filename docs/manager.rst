:mod:`panoramisk` - AMI
========================

An API to communicate with Asterisk's AMI

Configure Asterisk
--------------------------

In ``/etc/asterisk/manager.conf``, add:

.. code-block:: ini

    [username]
    secret=password
    deny=0.0.0.0/0.0.0.0
    permit=127.0.0.1/255.255.255.255
    read = all
    write = all

Launch:

.. code-block:: sh

    $ rasterisk -x 'manager reload'


API
---

.. automodule:: panoramisk

.. autoclass:: Manager
   :members:
