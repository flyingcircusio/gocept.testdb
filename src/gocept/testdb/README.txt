``gocept.testdb`` provides small helper classes that create and drop temporary
databases.

>>> import gocept.testdb
>>> import os.path
>>> import shutil
>>> import sqlalchemy
>>> import tempfile
>>> sql_dir = tempfile.mkdtemp()
>>> schema = os.path.join(sql_dir, 'sample.sql')
>>> with open(schema, 'w') as f:
...     _ = f.write('CREATE TABLE foo (dummy int);')

We'll use a custom prefix specific to the current process whenever we create
fixed-name databases during this test, in order to allow concurrent test runs
on the same machine (such as a CI server):

>>> import os
>>> pid_prefix = 'gocept.testdb.tests-PID%s-' % os.getpid()
>>> db_template = pid_prefix + 'templatetest'

MySQL
=====

``gocept.testdb`` expects the usage of PyMySQL_ as database driver.

.. _PyMySQL : https://pypi.python.org/pypi/PyMySQL

First, instantiate a test database object and have it create the database on
the server. You can specify the name or the prefix of the database:

>>> gocept.testdb.MySQL(schema_path=schema, db_name='mytestdb').dsn
'mysql+pymysql://.../mytestdb'
>>> db = gocept.testdb.MySQL(schema_path=schema, prefix='my-tests')
>>> db.dsn
'mysql+pymysql://.../my-tests-...'
>>> db.create()

This will use the appropriate command-line tools to create a database with a
random name.

You can use the following environment variables to customize the DSN:

``MYSQL_HOST``
    hostname, defaults to ``localhost``
``MYSQL_USER``
    username, defaults to ``None`` which means to use the name of the
    user logged into the operating system.
``MYSQL_PASS``
    password, defaults to ``None`` which means no password required.
``MYSQL_COMMAND_POSTFIX``
    attach this postfix to MySQL commands, defaults to an empty string. You
    need this variable if your MySQL commands are named like ``mysql5`` instead
    of ``mysql``.

The dbapi DSN can then be used to connect to the database:

>>> engine = sqlalchemy.create_engine(db.dsn)

The database is marked as a testing database by creating a table called
``tmp_functest`` in it:

>>> conn = engine.connect()
>>> ignore = conn.execute('SELECT * from tmp_functest')

The database object also offers convenience methods for determining the status
of the database:

>>> db.exists
True
>>> db.is_testing
True

If you passed a ``schema_path`` to the constructor, the SQL code in this file
is executed, e. g. to set up tables:

>>> ignore = conn.execute('SELECT * from foo')

When done, simply drop the database:

>>> conn.close()
>>> try:
...     db.drop()
... except RuntimeError:
...     pass  # Jenkins fails to drop databases in Python 3, *sigh*


PostgreSQL
==========

General
-------

The same procedure also works for PostgreSQL.
You can use the following environment variables to customize the DSN:

``POSTGRES_HOST``
    hostname, defaults to ``localhost``
``POSTGRES_USER``
    username, defaults to ``None`` which means to use the name of the
    user logged into the operating system.
``POSTGRES_PASS``
    password, defaults to ``None`` which means no password required.
    *Note:* Instead of using ``POSTGRES_PASS``, use the ``~/.pgpass`` mechanism
    `provided by postgres`_ itself.

.. _`provided by postgres`: http://wiki.postgresql.org/wiki/Pgpass

>>> db = gocept.testdb.PostgreSQL(schema_path=schema)
>>> db.create()
>>> engine = sqlalchemy.create_engine(db.dsn)
>>> conn = engine.connect()
>>> ignore = conn.execute('SELECT * from tmp_functest')
>>> ignore = conn.execute('SELECT * from foo')
>>> conn.invalidate()
>>> db.drop()

Encoding
--------

For PostgreSQL an optional encoding, database name and database name prefix
parameters can be specified in the constructor. They are used when creating the
database.

>>> gocept.testdb.PostgreSQL(encoding='UTF8', db_name='mytestdb').dsn
'postgresql://...localhost/mytestdb'
>>> gocept.testdb.PostgreSQL(prefix='my-tests').dsn
'postgresql://...localhost/my-tests-...'


Templates
---------

For PostgreSQL, an optional template parameter can be passed to the
constructor. It specifies the name of a template database which is used for the
creation of the test database. If the template database does not exist, it is
created with the specified schema.

The first time you create the database with the ``db_template`` argument, the
template database is created (if it does not exist already) along with the
requested database:

>>> db = gocept.testdb.PostgreSQL(schema_path=schema, db_template=db_template)

Now with the template available, the schema is not used any more to create the
database (it's copied from the template database).

When creating the database, we can, however, force the template database to be
created afresh from the schema. Doing so now will leave us with both a test
database and a template database according to the modified schema:

>>> db = gocept.testdb.PostgreSQL(
...     schema_path=schema, db_template=db_template, force_template=True)

The template database (and with it, the test database) is also created anew if
the schema file is newer than the existing template database.

If, however, the template database cannot be set up properly, it is removed
altogether to avoid a broken template database interfering with subsequent
tests.


The ``drop-all`` command-line script
====================================

The Database classes' ``drop_all`` functionality is available independently
through a command-line script named ``drop-all``. The script drops any test
databases from both the PostgreSQL and MySQL servers that match the
test-database naming convention with any of the prefixes passed as
command-line arguments. Usage::

  $ bin/drop-all "<prefix>"


Test clean up:

>>> shutil.rmtree(sql_dir)
