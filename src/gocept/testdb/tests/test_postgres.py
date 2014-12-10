# Copyright (c) 2008-2014 gocept gmbh & co. kg
# See also LICENSE.txt
from gocept.testdb.testing import unittest
import gocept.testdb
import gocept.testing.assertion
import os


class PostgreSQL(unittest.TestCase,
                 gocept.testing.assertion.Exceptions):

    db_template = 'gocept.testdb.tests-template-%s' % os.getpid()

    def drop_all(self):
        self.makeOne().drop_all(drop_template=True)

    setUp = tearDown = drop_all

    def makeOne(self, db_template=None, lc_collate=None, prefix=None):
        import gocept.testdb
        if db_template is None:
            db_template = self.db_template
        return gocept.testdb.PostgreSQL(
            db_template=db_template, lc_collate=lc_collate, prefix=prefix)


class PostgreSQLRegressionTests(PostgreSQL):

    def test_template_db_doesnt_need_schema(self):
        db = self.makeOne()
        with self.assertNothingRaised():
            db.create()

    def test_naming_scheme_matches_with_dash_in_prefix(self):
        db = self.makeOne(prefix='foo-bar')
        self.assertTrue(db._matches_db_naming_scheme('foo-bar-123'))


class PostgreSQLTests(PostgreSQL):

    def test_can_add_database_with_special_lc_collate(self):
        db = self.makeOne(lc_collate='de_DE.UTF-8')
        db.create()
        collate_by_db_name = dict((x[0], x[3]) for x in db.pg_list_db_items())
        self.assertEqual('de_DE.UTF-8', collate_by_db_name[db.db_name])
