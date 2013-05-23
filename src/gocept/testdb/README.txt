gocept.testdb provides small helper classes that create and drop temporary
databases.

>>> import os.path
>>> import sqlalchemy
>>> import gocept.testdb
>>> schema = os.path.join(sql_dir, 'sample.sql')
>>> write(schema, 'CREATE TABLE foo (dummy int);')

We'll use a custom prefix specific to the current process whenever we create
fixed-name databases during this test, in order to allow concurrent test runs
on the same machine (such as a CI server):

>>> import os
>>> pid_prefix = 'gocept.testdb.tests-PID%s-' % os.getpid()
>>> db_template = pid_prefix + 'templatetest'

MySQL
=====

First, instantiate a test database object and have it create the database on
the server:

>>> db = gocept.testdb.MySQL(schema_path=schema)
>>> db.create()

This will use the appropriate command-line tools to create a database with a
random name (you can specify a prefix if desired).
Login information can be specified via environment variables
(``MYSQL_HOST`` default localhost, ``MYSQL_USER`` default None, ``MYSQL_PASS`` default None)

The dbapi DSN can then be used to connect to the database:

>>> print db.dsn
mysql://...localhost/testdb-...
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

You can specify the name of the database:

>>> db = gocept.testdb.MySQL(schema_path=schema, db_name='mytestdb')
>>> print db.dsn
mysql://...localhost/mytestdb

There's a method to drop all test databases that may have been left on the
server by previous test runs by removing all (but only those) databases whose
name matches the test database naming scheme of ``gocept.testdb`` and using
the same name prefix as the Database instance used for dropping them all:

>>> db = gocept.testdb.MySQL()
>>> gocept.testdb.MySQL().create()
>>> gocept.testdb.MySQL().create()
>>> db.create_db(pid_prefix + 'foo')
>>> db.create_db(pid_prefix + 'bar')
>>> len(list_testdb_names(db))
4
>>> db.drop_all()
>>> len(list_testdb_names(db))
2
>>> db.drop_db(pid_prefix + 'foo')
>>> db.drop_db(pid_prefix + 'bar')
>>> len(list_testdb_names(db))
0

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
>>> engine.connect().execute('SELECT * from tmp_functest')
Traceback (most recent call last):
  ...
OperationalError:...

Encoding
--------

For Postgres an optional encoding parameter can be specified in the
constructor. It is used when creating the database.

>>> db = gocept.testdb.PostgreSQL(schema_path=schema, encoding='UTF8')
>>> db.create()
>>> engine = sqlalchemy.create_engine(db.dsn)
>>> conn = engine.connect()
>>> encoding = conn.execute(
...     '''SELECT pg_catalog.pg_encoding_to_char(encoding) as encoding
...        FROM pg_catalog.pg_database
...        WHERE datname = %s''', db.dsn.split('/')[-1]).fetchall()
>>> encoding in ([(u'UTF8',)], [('UTF8',)],)
True
>>> conn.invalidate()
>>> db.drop()

DB name
--------

You can specify the name of the database:

>>> db = gocept.testdb.PostgreSQL(schema_path=schema, db_name='mytestdb')
>>> db.dsn
'postgresql://localhost/mytestdb'

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
>>> db.create()
>>> table_names(db.get_dsn(db_template))
[u'foo', u'tmp_functest']
>>> table_names(db.dsn)
[u'foo', u'tmp_functest']

Now with the template available, the schema is not used anymore to create the
database (it's re-created from the template). Let's modify the template db
before the next db creation run to demonstrate this:

>>> _ = execute(db.get_dsn(db_template), 'DROP TABLE foo;')
>>> db2 = gocept.testdb.PostgreSQL(
...     schema_path=schema, db_template=db_template)
>>> db2.create()
>>> table_names(db2.get_dsn(db_template))
[u'tmp_functest']
>>> table_names(db2.dsn)
[u'tmp_functest']

When creating the database, we can, however, force the template db to be
created afresh from the schema. Doing so now will leave us with both a test db
and a template db according to the modified schema:

>>> db3 = gocept.testdb.PostgreSQL(
...     schema_path=schema, db_template=db_template, force_template=True)
>>> db3.create()
>>> table_names(db3.get_dsn(db_template))
[u'foo', u'tmp_functest']
>>> table_names(db3.dsn)
[u'foo', u'tmp_functest']

The template db (and with it, the test db) ist also created anew if the schema
file is newer than the existing template db:

>>> import time; time.sleep(1)  # XXX hack; either fake db mtime or see #12431
>>> write(schema, 'CREATE TABLE bar (dummy int);')
>>> db4 = gocept.testdb.PostgreSQL(
...     schema_path=schema, db_template=db_template, force_template=False)
>>> db4.create()
>>> table_names(db4.get_dsn(db_template))
[u'bar', u'tmp_functest']
>>> table_names(db4.dsn)
[u'bar', u'tmp_functest']

If, however, the template db cannot be set up properly, it is removed
altogether to avoid a broken template db interfering with subsequent tests:

>>> write(schema+'-broken', 'foobar')
>>> db_broken = gocept.testdb.PostgreSQL(
...     schema_path=schema+'-broken', db_template=db_template,
...     force_template=True)
>>> db_broken.create()
Traceback (most recent call last):
SystemExit: Could not initialize schema in database
            'gocept.testdb.tests-...-templatetest'.
>>> db_template in db_broken.list_db_names()
False

Clean up:

>>> db.drop()
>>> db2.drop()
>>> db3.drop()
>>> db4.drop()

Database prefix
===============

By default the created database is prefixed with ``testdb`` but this can be
changed by using the ``prefix`` attribute of the constructor: (This works
for MySQL the same way.)

>>> db = gocept.testdb.PostgreSQL(schema_path=schema)
>>> db.dsn
'postgresql://localhost/testdb-...
>>> db = gocept.testdb.PostgreSQL(schema_path=schema, prefix='my-tests')
>>> db.dsn
'postgresql://localhost/my-tests-...

Cleaning up the server
======================

There's a method to drop all test databases that may have been left on the
server by previous test runs by removing all (but only those) databases whose
name matches the test database naming scheme of ``gocept.testdb`` and using
the same name prefix as the Database instance used for dropping them all. For
PostgreSQL, this clean-up method doesn't by default drop the template database
if one was created:

>>> db = gocept.testdb.PostgreSQL(db_template=db_template)
>>> db.create()
>>> gocept.testdb.PostgreSQL().create()
>>> db.create_db(pid_prefix + 'foo')
>>> db.create_db(pid_prefix + 'bar')
>>> len(list_testdb_names(db))
5
>>> db.drop_all()
>>> len(list_testdb_names(db))
3
>>> db.drop_db(pid_prefix + 'foo')
>>> db.drop_db(pid_prefix + 'bar')
>>> len(list_testdb_names(db))
1

However, the clean-up method can be instructed to drop the template database
as well:

>>> db.db_template in db.list_db_names()
True
>>> db.drop_all(drop_template=True)
>>> db.db_template in db.list_db_names()
False
>>> list_testdb_names(db)
[]


The ``drop-all`` command-line script
====================================

The Database classes' ``drop_all`` functionality is available independently
through a command-line script named ``drop-all``. The script drops any test
databases from both the PostgreSQL and MySQL servers that match the
test-database naming convention with any of the prefixes passed as
command-line arguments (clean up first):

>>> gocept.testdb.db.MySQL(prefix=pid_prefix + 'foo').create()
>>> gocept.testdb.db.MySQL(prefix=pid_prefix + 'bar').create()
>>> gocept.testdb.db.MySQL(prefix=pid_prefix + 'bar').create()
>>> len(list_testdb_names(gocept.testdb.db.MySQL()))
3

>>> gocept.testdb.db.PostgreSQL(prefix=pid_prefix + 'foo').create()
>>> gocept.testdb.db.PostgreSQL(prefix=pid_prefix + 'bar').create()
>>> gocept.testdb.db.PostgreSQL(prefix=pid_prefix + 'bar').create()
>>> len(list_testdb_names(gocept.testdb.db.PostgreSQL()))
3

>>> system('drop-all %s %s' % (pid_prefix + 'foo', pid_prefix + 'bar'))
>>> len(list_testdb_names(gocept.testdb.db.MySQL()))
0
>>> len(list_testdb_names(gocept.testdb.db.PostgreSQL()))
0

On the PostgreSQL server, databases named exactly after any of the names
passed will also be dropped. This is how template databases can be dropped
without having to call ``dropdb`` on each of them:

>>> gocept.testdb.db.PostgreSQL(
...     prefix=pid_prefix + 'foo', db_template=pid_prefix + 'bar').create()
>>> len(list_testdb_names(gocept.testdb.db.PostgreSQL()))
2
>>> import gocept.testdb.cmdline
>>> gocept.testdb.cmdline.drop_all([pid_prefix + 'foo', pid_prefix + 'bar'])
>>> len(list_testdb_names(gocept.testdb.db.PostgreSQL()))
0

If the script is called without arguments, test databases matching the default
prefix will be dropped, but no attempt will be made to drop a database named
exactly after the default prefix since in this case, there's no reason to
assume that a template database by that name should have been created:

>>> db = gocept.testdb.db.PostgreSQL(
...     db_template=gocept.testdb.db.PostgreSQL.prefix)
>>> db.create()
>>> len(list_testdb_names(db))
1
>>> gocept.testdb.db.PostgreSQL.prefix in db.list_db_names()
True
>>> gocept.testdb.cmdline.drop_all([])
>>> len(list_testdb_names(db))
0
>>> gocept.testdb.db.PostgreSQL.prefix in db.list_db_names()
True
>>> db.drop_db(gocept.testdb.db.PostgreSQL.prefix)
>>> gocept.testdb.db.PostgreSQL.prefix in db.list_db_names()
False

(We considered an explicit command-line switch for dropping template databases
but felt that it would be too annoying and test databases shouldn't use a
prefix that is itself used by a real or template database.)
