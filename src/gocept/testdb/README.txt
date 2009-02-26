gocept.testdb - temporary database creation
-------------------------------------------

gocept.testdb provides small helper classes that create and drop temporary
databases.

>>> import os.path
>>> import sqlalchemy
>>> import gocept.testdb
>>> schema = os.path.join(os.path.dirname(gocept.testdb.__file__), 'sample.sql')

First, create a test database object

>>> db = gocept.testdb.MySQL(schema_path=schema)

This will use the appropriate command-line tools to create a database with a
random name (you can specify a prefix if desired).
Login information can be specified via environment variables
(MYSQL_HOST default localhost, MYSQL_USER default None, MYSQL_PASS default None)

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
