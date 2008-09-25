gocept.testdb - temporary database creation
----------------------------------------------------

>>> import os.path
>>> import sqlalchemy
>>> import gocept.testdb

>>> schema = os.path.join(os.path.dirname(gocept.testdb.__file__), 'sample.sql')
>>> db = gocept.testdb.MySQL(schema_path=schema)
>>> db.dsn
'mysql://localhost/testdb-...'
>>> engine = sqlalchemy.create_engine(db.dsn)
>>> conn = engine.connect()
>>> ignore = conn.execute('SELECT * from tmp_functest')
>>> ignore = conn.execute('SELECT * from foo')
>>> db.drop()
>>> engine.connect().execute('SELECT * from tmp_functest')
Traceback (most recent call last):
  ...
OperationalError:...

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
