# Copyright (c) 2008-2013 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.testdb
import sqlalchemy

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    import MySQLdb
    HAVE_MYSQL = True
except ImportError:
    HAVE_MYSQL = False


@unittest.skipUnless(HAVE_MYSQL, 'no mysql driver available')
class MySQLStatusTests(unittest.TestCase):

    def setUp(self):
        self.db = gocept.testdb.MySQL()

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
