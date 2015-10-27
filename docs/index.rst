.. panoramisk documentation master file, created by
   sphinx-quickstart on Thu Jan  9 12:06:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: ../README.rst

=========================
How to configure Asterisk
=========================

In ``/etc/asterisk/manager.conf``, add:

::

    [username]
    secret=password
    deny=0.0.0.0/0.0.0.0
    permit=127.0.0.1/255.255.255.255
    read = all
    write = all

Launch: ``rasterisk -x 'manager reload'``

=====================
:mod:`panoramisk` api
=====================

.. automodule:: panoramisk

.. autoclass:: Manager
   :members:

.. toctree::
   :maxdepth: 2

.. automodule:: panoramisk.fast_agi

.. autoclass:: Application
   :members:

.. toctree::
   :maxdepth: 2

=======
CHANGES
=======

.. include:: ../CHANGES.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

