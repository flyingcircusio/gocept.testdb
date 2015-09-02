import gocept.testdb.testing
import gocept.testing.assertion


class MySQLTests(gocept.testdb.testing.TestCase,
                 gocept.testing.assertion.String,
                 gocept.testing.assertion.Exceptions):
    """Testing ..mysql.MySQL"""

    def tearDown(self):
        self.makeOne(create_db=False).drop_all()
        super(MySQLTests, self).tearDown()

    def makeOne(self, db_name=None, create_db=True):
        import gocept.testdb
        db = gocept.testdb.MySQL(schema_path=self.schema, db_name=db_name)
        if create_db:
            db.create()
        return db

    def test_nonexistent_db_returns_exists_False(self):
        self.assertFalse(self.makeOne(create_db=False).exists)

    def test_existing_db_returns_exists_True(self):
        self.assertTrue(self.makeOne(create_db=True).exists)

    def test_nonexistent_db_counts_as_not_testing(self):
        self.assertFalse(self.makeOne(create_db=False).is_testing)

    def test_db_with_special_table_counts_as_testing(self):
        self.assertTrue(self.makeOne(create_db=True).is_testing)

    def test_db_without_special_table_counts_as_not_testing(self):
        db = self.makeOne(create_db=True)
        self.execute(db.dsn, 'DROP TABLE tmp_functest')
        self.assertFalse(db.is_testing)

    def test_takes_configuration_from_environment(self):
        db = self.makeOne(create_db=False)
        self.assertStartsWith('{0}://'.format(db.protocol), db.dsn)
        self.assertIn('/testdb-', db.dsn)

    def test_created_database_contains_marker_table(self):
        db = self.makeOne()
        # The database is marked as a testing database by creating a table
        # called 'tmp_functest' in it:
        with self.assertNothingRaised():
            self.execute(db.dsn, 'SELECT * from tmp_functest')

    def test_schema_gets_loaded(self):
        db = self.makeOne()
        with self.assertNothingRaised():
            self.execute(db.dsn, 'SELECT * from foo')

    def test_name_of_database_can_be_specified(self):
        db = self.makeOne(db_name='mytestdb', create_db=False)
        self.assertEndsWith('/mytestdb', db.dsn)

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
