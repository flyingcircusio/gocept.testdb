gocept.testdb - temporary database creation
----------------------------------------------------

>>> import gocept.testdb
>>> import os.path
>>> db = gocept.testdb.MySQL(schema_path=os.path.join(
...         os.path.dirname(gocept.testdb.__file__),
...         'sample.sql'))
>>> db.dsn
'mysql://localhost/testdb-...'
>>> import sqlalchemy
>>> engine = sqlalchemy.create_engine(db.dsn)
>>> ignore = engine.connect().execute('SELECT * from tmp_functest')
>>> db.drop()
>>> engine.connect().execute('SELECT * from tmp_functest')
Traceback (most recent call last):
  ...
OperationalError:...
