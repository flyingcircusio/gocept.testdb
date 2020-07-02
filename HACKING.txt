Development
===========

To run the `buildout` of this package copy ``local.cfg.example`` to
``local.cfg`` and edit it to match your needs:

* ``MYSQL_COMMAND_POSTFIX`` is needed if your MySQL commands look like `mysql5`
  instead of `mysql`

* MySQL has to open a port for the tests to connect to. Configure this in your
  `my.cnf`.

Running tests
-------------

Install tox_ and run the tests calling ``tox``.

.. _tox : https://pypi.python.org/pypi/tox

Using docker containers for the tests
-------------------------------------

Prerequisites
+++++++++++++

* ``mysqladmin`` and ``mysql`` have to be on $PATH.
* ``createdb`` has to be on $PATH.
* Run the follwing commands (you might change the used passwords)::

    docker run --name mysql56 -e MYSQL_ROOT_PASSWORD=84_L224JF0GlTXcL -d -p 3307:3306 mysql:5.6
    docker run --name postgres96 -e POSTGRES_PASSWORD=j§V7iJY@1xTG67J@ -d -p 5433:5432 postgres:9.6
    echo "localhost:5433:*:postgres:j§V7iJY@1xTG67J@" >> ~/.pgpass
    chmod 600 ~/.pgpass

Run the tests
+++++++++++++

* MYSQL_PORT=3307 MYSQL_USER=root MYSQL_PASS=84_L224JF0GlTXcL POSTGRES_PORT=5433 POSTGRES_USER=postgres tox

Source code
-----------

The source code is available at https://github.com/gocept/gocept.testdb

Bug reports
-----------

Please report any bugs you find to https://github.com/gocept/gocept.testdb/issues
