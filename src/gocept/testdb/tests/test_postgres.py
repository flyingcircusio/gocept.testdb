import gocept.testdb
import gocept.testdb.testing
import gocept.testing.assertion
import os
import sqlalchemy.exc
import time


class PostgreSQLTests(gocept.testdb.testing.TestCase,
                      gocept.testing.assertion.String,
                      gocept.testing.assertion.Exceptions,
                      gocept.testing.assertion.Ellipsis):
    """Testing ..postgres.PostgreSQL."""

    db_template = 'gocept.testdb.tests-template-%s' % os.getpid()

    def tearDown(self):
        try:
            self.drop_all()
        finally:
            super(PostgreSQLTests, self).tearDown()

    def drop_all(self):
        self.makeOne(db_template=self.db_template, create_db=False).drop_all(
            drop_template=True)

    def makeOne(self, create_db=True, db_template=None, **kw):
        import gocept.testdb
        db = gocept.testdb.PostgreSQL(
            db_template=db_template, **kw)
        if create_db:
            db.create()
        return db

    def test_template_db_doesnt_need_schema(self):
        # regression test
        db = self.makeOne(create_db=False)
        with self.assertNothingRaised():
            db.create()

    def test_naming_scheme_matches_with_dash_in_prefix(self):
        # regression test
        db = self.makeOne(prefix='foo-bar', create_db=False)
        self.assertTrue(db._matches_db_naming_scheme('foo-bar-123'))

    def test_can_add_database_with_special_lc_collate(self):
        try:
            db = self.makeOne(lc_collate='de_DE.UTF-8')
        except SystemExit:
            # When using Docker container as suggested in README this call
            # fails with 'invalid locale name: "de_DE.UTF-8"', so let's skip
            # the test in that environment:
            self.skipTest('"de_DE.UTF-8" not supported by database.')
        collate_by_db_name = dict((x[0], x[3]) for x in db.pg_list_db_items())
        self.assertEqual('de_DE.UTF-8', collate_by_db_name[db.db_name])

    def test_takes_configuration_from_environment(self):
        db = self.makeOne(create_db=False)
        self.assertStartsWith('postgresql://', db.dsn)
        hostname = 'localhost'
        if db.db_port:  # pragma: no cover
            hostname = '{}:{}'.format(hostname, db.db_port)
        self.assertIn('{}/testdb-PID'.format(hostname), db.dsn)

    def test_created_database_contains_marker_table(self):
        db = self.makeOne()
        # The database is marked as a testing database by creating a table
        # called 'tmp_functest' in it:
        with self.assertNothingRaised():
            self.execute(db.dsn, 'SELECT * from tmp_functest')

    def test_conveniences_properties_are_set(self):
        db = self.makeOne()
        self.assertTrue(db.exists)
        self.assertTrue(db.is_testing)

    def test_schema_gets_loaded(self):
        db = self.makeOne(schema_path=self.schema)
        with self.assertNothingRaised():
            self.execute(db.dsn, 'SELECT * from foo')

    def test_name_of_database_can_be_specified(self):
        db = self.makeOne(db_name='mytestdb', create_db=False)
        self.assertEndsWith('/mytestdb', db.dsn)

    def test_drop_drops_database(self):
        db = self.makeOne()
        db.drop()
        with self.assertRaises(sqlalchemy.exc.OperationalError) as err:
            self.connect(db)
        self.assertEllipsis(
            '... database ... does not exist...', str(err.exception))

    def test_encoding_is_used(self):
        # An optional encoding parameter can be specified in the constructor.
        # It is used when creating the database.
        db = self.makeOne(schema_path=self.schema, encoding='UTF8')
        encoding = self.execute(
            db.dsn,
            """SELECT pg_catalog.pg_encoding_to_char(encoding) as encoding
               FROM pg_catalog.pg_database
               WHERE datname = '%s'""" % db.dsn.split('/')[-1], fetch=True)
        self.assertEqual([('UTF8',)], encoding)

    def test_db_template_creates_template_database(self):
        # An optional template parameter can be passed to the constructor.
        # It specifies the name of a template db which is used for the creation
        # of the database. If the template db does not exist, it is created
        # with the specified schema.

        # The first time you create the database with the db_template argument,
        # the template db is created (if it does not exist already) along with
        # the requested db:
        db = self.makeOne(
            schema_path=self.schema, db_template=self.db_template)
        self.assertEqual(['foo', 'tmp_functest'],
                         self.table_names(db.get_dsn(self.db_template)))
        self.assertEqual(['foo', 'tmp_functest'],
                         self.table_names(db.dsn))

        # Now with the template available, the schema is not used anymore to
        # create the database (it's re-created from the template). Let's modify
        # the template db before the next db creation run to demonstrate this:
        self.execute(db.get_dsn(self.db_template), 'DROP TABLE foo;')
        db2 = self.makeOne(
            schema_path=self.schema, db_template=self.db_template)
        self.assertEqual(['tmp_functest'],
                         self.table_names(db2.get_dsn(self.db_template)))
        self.assertEqual(['tmp_functest'], self.table_names(db2.dsn))

        # When creating the database, we can, however, force the template db to
        # be created afresh from the schema. Doing so now will leave us with
        # both a test db and a template db according to the modified schema:
        db3 = self.makeOne(
            schema_path=self.schema, db_template=self.db_template,
            force_template=True)
        self.assertEqual(['foo', 'tmp_functest'],
                         self.table_names(db3.get_dsn(self.db_template)))
        self.assertEqual(['foo', 'tmp_functest'],
                         self.table_names(db3.dsn))

        # The template db (and with it, the test db) ist also created anew if
        # the schema file is newer than the existing template db:
        time.sleep(1)  # XXX hack; either fake db mtime or see #12431
        self.write(self.schema, 'CREATE TABLE bar (dummy int);')
        db4 = self.makeOne(
            schema_path=self.schema, db_template=self.db_template,
            force_template=True)
        self.assertEqual(['bar', 'tmp_functest'],
                         self.table_names(db4.get_dsn(self.db_template)))
        self.assertEqual(['bar', 'tmp_functest'],
                         self.table_names(db4.dsn))

        # If, however, the template db cannot be set up properly, it is removed
        # altogether to avoid a broken template db interfering with subsequent
        # tests:
        broken_schema = self.schema + '-broken'
        self.write(broken_schema, 'foobar')
        db_broken = self.makeOne(
            schema_path=broken_schema, db_template=self.db_template,
            force_template=True, create_db=False)
        with self.assertRaises(SystemExit) as err:
            db_broken.create()
        self.assertEllipsis(
            "Could not initialize schema in database "
            "'gocept.testdb.tests-PID...-templatetest'.", str(err.exception))
        self.assertNotIn(self.db_template, db_broken.list_db_names())

    def test_drop_all_drops_all_databases(self):
        # There's a method to drop all test databases that may have been left
        # on the server by previous test runs by removing all (but only those)
        # databases whose name matches the test database naming scheme of
        # ``gocept.testdb`` and using the same name prefix as the Database
        # instance used for dropping them all. This clean-up method doesn't by
        # default drop the template database if one was created:
        db = self.makeOne(db_template=self.db_template)
        self.makeOne()
        db.create_db(self.pid_prefix + 'foo')
        db.create_db(self.pid_prefix + 'bar')
        self.assertEqual(5, len(self.list_testdb_names(db)))
        db.drop_all()
        self.assertEqual(3, len(self.list_testdb_names(db)))
        db.drop_db(self.pid_prefix + 'foo')
        db.drop_db(self.pid_prefix + 'bar')
        self.assertEqual(1, len(self.list_testdb_names(db)))

        # However, the clean-up method can be instructed to drop the template
        # database as well:
        self.assertIn(db.db_template, db.list_db_names())
        db.drop_all(drop_template=True)
        self.assertNotIn(db.db_template, db.list_db_names())
        self.assertEqual([], self.list_testdb_names(db))
