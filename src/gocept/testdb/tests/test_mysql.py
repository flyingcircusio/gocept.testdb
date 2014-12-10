# Copyright (c) 2008-2013 gocept gmbh & co. kg
# See also LICENSE.txt
from gocept.testdb.testing import unittest
import gocept.testdb.testing
import gocept.testing.assertion
import sqlalchemy

try:
    import MySQLdb
    HAVE_MYSQL = True
except ImportError:
    HAVE_MYSQL = False
else:
    del MySQLdb


@unittest.skipUnless(HAVE_MYSQL, 'no mysql driver available')
class MySQLStatusTests(unittest.TestCase):

    def setUp(self):
        import gocept.testdb
        self.db = gocept.testdb.MySQL()

    def tearDown(self):
        self.db.drop_all()

    def test_nonexistent_db_returns_exists_False(self):
        self.assertFalse(self.db.exists)

    def test_existing_db_returns_exists_True(self):
        self.db.create()
        self.assertTrue(self.db.exists)

    def test_nonexistent_db_counts_as_not_testing(self):
        self.assertFalse(self.db.is_testing)

    def test_db_with_special_table_counts_as_testing(self):
        self.db.create()
        self.assertTrue(self.db.is_testing)

    def test_db_without_special_table_counts_as_not_testing(self):
        self.db.create()
        engine = sqlalchemy.create_engine(self.db.dsn)
        engine.connect().execute('DROP TABLE tmp_functest')
        self.assertFalse(self.db.is_testing)


@unittest.skipUnless(HAVE_MYSQL, 'no mysql driver available')
class MySQLTests(gocept.testdb.testing.TestCase,
                 gocept.testing.assertion.String,
                 gocept.testing.assertion.Exceptions):
    """Testing ..mysql.MySQL"""

    def tearDown(self):
        import gocept.testdb
        gocept.testdb.MySQL().drop_all()
        super(MySQLTests, self).tearDown()

    def makeOne(self, db_name=None, create_db=True):
        import gocept.testdb
        db = gocept.testdb.MySQL(schema_path=self.schema, db_name=db_name)
        if create_db:
            db.create()
        return db

    def connect(self, db):
        engine = sqlalchemy.create_engine(db.dsn)
        return engine.connect()

    def test_takes_configuration_from_environment(self):
        db = self.makeOne()
        self.assertStartsWith('mysql://', db.dsn)
        self.assertIn('localhost/testdb-', db.dsn)

    def test_created_database_contains_marker_table(self):
        conn = self.connect(self.makeOne())
        # The database is marked as a testing database by creating a table
        # called 'tmp_functest' in it:
        with self.assertNothingRaised():
            conn.execute('SELECT * from tmp_functest')

    def test_conveniences_properties_are_set(self):
        db = self.makeOne()
        self.assertTrue(db.exists)
        self.assertTrue(db.is_testing)

    def test_schema_gets_loaded(self):
        conn = self.connect(self.makeOne())
        with self.assertNothingRaised():
            conn.execute('SELECT * from foo')

    def test_name_of_database_can_be_specified(self):
        db = self.makeOne(db_name='mytestdb', create_db=False)
        self.assertEndsWith('localhost/mytestdb', db.dsn)

    def test_drop_all_drops_all_databases(self):
        # There's a method to drop all test databases that may have been left
        # on the server by previous test runs by removing all (but only those)
        # databases whose name matches the test database naming scheme of
        # ``gocept.testdb`` and using the same name prefix as the Database
        # instance used for dropping them all:
        db = self.makeOne(create_db=False)
        db.create_db(self.pid_prefix + 'foo')
        db.create_db(self.pid_prefix + 'bar')
        self.makeOne()
        self.makeOne()
        self.assertEqual(4, len(self.list_testdb_names(db)))
        db.drop_all()
        self.assertEqual(2, len(self.list_testdb_names(db)))
        db.drop_db(self.pid_prefix + 'foo')
        db.drop_db(self.pid_prefix + 'bar')
        self.assertEqual(0, len(self.list_testdb_names(db)))
