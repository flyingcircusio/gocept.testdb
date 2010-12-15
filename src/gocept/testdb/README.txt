===========================
Temporary database creation
===========================

gocept.testdb provides small helper classes that create and drop temporary
databases.

>>> import os.path
>>> import sqlalchemy
>>> import gocept.testdb
>>> schema = os.path.join(os.path.dirname(gocept.testdb.__file__), 'sample.sql')

MySQL
-----

First, create a test database object

>>> db = gocept.testdb.MySQL(schema_path=schema)

This will use the appropriate command-line tools to create a database with a
random name (you can specify a prefix if desired).
Login information can be specified via environment variables
(``MYSQL_HOST`` default localhost, ``MYSQL_USER`` default None, ``MYSQL_PASS`` default None)

The dbapi DSN can then be used to connect to the database:

>>> db.dsn
'mysql://localhost/testdb-...'
>>> engine = sqlalchemy.create_engine(db.dsn)

The database is marked as a testing database by creating a table called
'tmp_functest' in it:

>>> conn = engine.connect()
>>> ignore = conn.execute('SELECT * from tmp_functest')

If you passed a schema_path to the constructor, the SQL code in this file
is executed, e. g. to set up tables:

>>> ignore = conn.execute('SELECT * from foo')

When done, simply drop the database:

>>> db.drop()
>>> engine.connect().execute('SELECT * from tmp_functest')
Traceback (most recent call last):
  ...
OperationalError:...

PostgreSQL
----------

General
~~~~~~~

The same procedure also works for PostgreSQL:
(Note however that POSTGRES_PASS is not supported at the moment)

>>> db = gocept.testdb.PostgreSQL(schema_path=schema)
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
~~~~~~~~

For Postgres an optional encoding parameter can be specified in the
constructor. It is used when creating the database.

>>> db = gocept.testdb.PostgreSQL(schema_path=schema, encoding='UTF8')
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


Database prefix
---------------

By default the created database is prefixed with ``testdb`` but this can be
changed by using the ``prefix`` attribute of the constructor: (This works
for MySQL the same way.)

>>> db = gocept.testdb.PostgreSQL(schema_path=schema)
>>> db.dsn
'postgresql://localhost/testdb-...
>>> db.drop()
>>> db = gocept.testdb.PostgreSQL(schema_path=schema, prefix='my-tests')
>>> db.dsn
'postgresql://localhost/my-tests-...
>>> db.drop()

