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
random name (you can specify a prefix if desired).
Login information can be specified via environment variables
(``MYSQL_HOST`` default localhost, ``MYSQL_USER`` default None,
``MYSQL_PASS`` default None, ``MYSQL_COMMAND_POSTFIX`` default '')

The dbapi DSN can then be used to connect to the database:

>>> engine = sqlalchemy.create_engine(db.dsn)

The database is marked as a testing database by creating a table called
'tmp_functest' in it:

>>> conn = engine.connect()
>>> ignore = conn.execute('SELECT * from tmp_functest')

The database also offers conveniences method for determining the status of the
database:

>>> db.exists
True
>>> db.is_testing
True

If you passed a schema_path to the constructor, the SQL code in this file
is executed, e. g. to set up tables:

>>> ignore = conn.execute('SELECT * from foo')

When done, simply drop the database:

>>> conn.close()
>>> db.drop()
>>> import sqlalchemy.exc
>>> with engine.connect() as conn:
...     try:
...         conn.execute('SELECT * from tmp_functest')
...     except sqlalchemy.exc.SQLAlchemyError:
...         pass
...     else:
...         raise AssertionError()


PostgreSQL
==========

General
-------

The same procedure also works for PostgreSQL:

Note: Instead of using POSTGRES_PASS, use the ~/.pgpass mechanism
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

For Postgres optional encoding, name and prefix parameters can be specified in the
constructor. They are used when creating the database.

>>> gocept.testdb.PostgreSQL(
...     schema_path=schema, encoding='UTF8', db_name='mytestdb').dsn
'postgresql://...localhost/mytestdb'

>>> gocept.testdb.PostgreSQL(schema_path=schema, prefix='my-tests').dsn
'postgresql://...localhost/my-tests-...'


Templates
---------

For Postgres, an optional template parameter can be passed to the constructor.
It specifies the name of a template db which is used for the creation of the
database. If the template db does not exist, it is created with the specified
schema.

The first time you create the database with the db_template argument, the
template db is created (if it does not exist already) along with the requested
db:

>>> db = gocept.testdb.PostgreSQL(
...     schema_path=schema, db_template=db_template)

Now with the template available, the schema is not used anymore to create the
database (it's re-created from the template).

When creating the database, we can, however, force the template db to be
created afresh from the schema. Doing so now will leave us with both a test db
and a template db according to the modified schema:

>>> db = gocept.testdb.PostgreSQL(
...     schema_path=schema, db_template=db_template, force_template=True)

The template db (and with it, the test db) is also created anew if the schema
file is newer than the existing template db.

If, however, the template db cannot be set up properly, it is removed
altogether to avoid a broken template db interfering with subsequent tests.

Clean up:

>>> shutil.rmtree(sql_dir)


The ``drop-all`` command-line script
====================================

The Database classes' ``drop_all`` functionality is available independently
through a command-line script named ``drop-all``. The script drops any test
databases from both the PostgreSQL and MySQL servers that match the
test-database naming convention with any of the prefixes passed as
command-line arguments. Usage::

  $ bin/drop-all "<prefix>"
