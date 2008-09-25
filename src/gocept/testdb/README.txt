gocept.testdb - temporary database creation
----------------------------------------------------

>>> import gocept.testdb
>>> db = gocept.testdb.MySQL()
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
