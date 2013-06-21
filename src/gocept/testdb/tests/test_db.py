# Copyright (c) 2008-2013 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.testdb.db
import os
import sqlalchemy
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class PostgreSQL(unittest.TestCase):

    db_template = 'gocept.testdb.tests-template-%s' % os.getpid()

    def drop_all(self):
        db = gocept.testdb.db.PostgreSQL(db_template=self.db_template)
        db.drop_all(drop_template=True)

    setUp = tearDown = drop_all


class PostgreSQLRegressionTests(PostgreSQL):

    def test_template_db_doesnt_need_schema(self):
        db = gocept.testdb.db.PostgreSQL(db_template=self.db_template)
        db.create()

    def test_naming_scheme_matches_with_dash_in_prefix(self):
        db = gocept.testdb.db.PostgreSQL(prefix='foo-bar')
        self.assertTrue(db._matches_db_naming_scheme('foo-bar-123'))


class PostgreSQLTests(PostgreSQL):

    def test_can_add_database_with_special_lc_collate(self):
        db = gocept.testdb.db.PostgreSQL(lc_collate='de_DE.UTF-8')
        db.create()
        collate_by_db_name = dict((x[0], x[3]) for x in db.pg_list_db_items())
        self.assertEqual('de_DE.UTF-8', collate_by_db_name[db.db_name])


try:
    import MySQLdb
    HAVE_MYSQL = True
except ImportError:
    HAVE_MYSQL = False


@unittest.skipUnless(HAVE_MYSQL, 'no mysql driver available')
class StatusTests(unittest.TestCase):

    def setUp(self):
        self.db = gocept.testdb.db.MySQL()

    def tearDown(self):
        self.db.drop_all

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
