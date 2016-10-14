Contribute
==========

Feel free to clone the project on `GitHub <https://github.com/gawel/panoramisk>`_.

Once you made a change, try to add a test for your feature/fix. At least assume
that you have'nt broke anything by running tox::

    $ tox
    ...
    py34: commands succeeded
    py35: commands succeeded
    flake8: commands succeeded
    docs: commands succeeded
    congratulations :)

 You can run tests for a specific version::

    $ tox -e py35

Running individual test::

    $ tox -e py35 tests/test_manager.py::test_connection


You can also build the docs with::

    $ tox -e docs

And check the result::

    $ firefox .tox/docs/tmp/html/index.html
