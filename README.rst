================================
Panoramisk. The Asterisk's druid
================================

.. image:: https://travis-ci.org/gawel/panoramisk.png?branch=master&style=flat-square
        :target: https://travis-ci.org/gawel/panoramisk

.. image:: https://img.shields.io/coveralls/gawel/panoramisk/master.svg
        :target: https://coveralls.io/r/gawel/panoramisk?branch=master

.. image:: https://img.shields.io/pypi/v/panoramisk.svg?style=flat-square
        :target: https://pypi.python.org/pypi/panoramisk

.. image:: https://img.shields.io/pypi/dw/panoramisk.svg?style=flat-square
        :target: https://pypi.python.org/pypi/panoramisk

.. image:: https://img.shields.io/github/issues/gawel/panoramisk.svg?style=flat-square
        :target: https://github.com/gawel/panoramisk/issues

.. image:: https://img.shields.io/github/license/gawel/panoramisk.svg?style=flat-square
        :target: https://github.com/gawel/panoramisk/blob/master/LICENSE


`Panoramisk` is a library based on python's `AsyncIO
<http://docs.python.org/dev/library/asyncio.html>`_ to play with `Asterisk
<http://www.asterisk.org/community/documentation>`_'s `manager
<https://wiki.asterisk.org/wiki/display/AST/The+Asterisk+Manager+TCP+IP+API>`_.

It uses the TCP manager server to listen to events and send actions.

For basic usage, you have some examples in `examples/
<https://github.com/gawel/panoramisk/tree/master/examples>`_ folder.

You can find some help on IRC: irc://irc.freenode.net/panoramisk (`www
<https://kiwiirc.com/client/irc.freenode.net/?nick=panoramisk|?&theme=basic#panoramisk>`_)


Running the Tests
-----------------

Running all the tests::

    $ tox

Running individual test with python 3.5::

    $ tox -e py35 tests/test_manager.py::test_connection


Source code
-----------

Find us on Github at https://github.com/gawel/panoramisk/


Documentation
-------------

Check out the documentation on Read the Docs: https://panoramisk.readthedocs.org/


Installation
------------

Install, upgrade and uninstall panoramisk with these commands::

    $ pip install panoramisk
    $ pip install --upgrade panoramisk
    $ pip uninstall panoramisk


Who use Panoramisk on production ?
----------------------------------

For now, mainly `Eyepea
<http://www.eyepea.eu/>`_ and `ALLOcloud
<http://www.allocloud.com/>`_.

You shouldn't know theses companies, however, Eyepea is a provider of several famous European companies and governments organizations.
You can check their references on their website:

* http://www.eyepea.eu/customers
* http://www.eyepea.eu/company/news

Moreover, ALLOcloud is a cloud solution for SMEs, it handles several millions of calls by month.

If you also use Panoramisk on production, don't hesitate to open a pull request to add your company's name with some details.
