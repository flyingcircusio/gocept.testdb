# Copyright (c) 2008-2013 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.testdb
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class PostgreSQL(unittest.TestCase):

    db_template = 'gocept.testdb.tests-template-%s' % os.getpid()

    def drop_all(self):
        db = gocept.testdb.PostgreSQL(db_template=self.db_template)
        db.drop_all(drop_template=True)

    setUp = tearDown = drop_all


class PostgreSQLRegressionTests(PostgreSQL):

    def test_template_db_doesnt_need_schema(self):
        db = gocept.testdb.PostgreSQL(db_template=self.db_template)
        db.create()

    def test_naming_scheme_matches_with_dash_in_prefix(self):
        db = gocept.testdb.PostgreSQL(prefix='foo-bar')
        self.assertTrue(db._matches_db_naming_scheme('foo-bar-123'))


class PostgreSQLTests(PostgreSQL):

    def test_can_add_database_with_special_lc_collate(self):
        db = gocept.testdb.PostgreSQL(lc_collate='de_DE.UTF-8')
        db.create()
        collate_by_db_name = dict((x[0], x[3]) for x in db.pg_list_db_items())
        self.assertEqual('de_DE.UTF-8', collate_by_db_name[db.db_name])
