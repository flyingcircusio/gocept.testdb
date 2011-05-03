# Copyright (c) 2008-2011 gocept gmbh & co. kg
# See also LICENSE.txt

import doctest
import gocept.testdb.db
import os
import os.path
import shutil
import sqlalchemy
import stat
import subprocess
import sys
import tempfile
import unittest


def write(path, content):
    f = open(path, 'w')
    f.write(content)
    f.close()


def execute(dsn, cmd):
    engine = sqlalchemy.create_engine(dsn)
    conn = engine.connect()
    result = conn.execute(cmd)
    conn.invalidate()
    conn.close()
    return result


def table_names(dsn):
    engine = sqlalchemy.create_engine(dsn)
    conn = engine.connect()
    result = engine.table_names(connection=conn)
    conn.invalidate()
    conn.close()
    return result


def system(test):
    def system(cmdline):
        args = cmdline.split()
        args[0] = os.path.join(test.bin_dir, args[0])
        subprocess.call(args)
    return system


def setUp(test):
    test.bin_dir = tempfile.mkdtemp()
    drop_all_path = os.path.join(test.bin_dir, 'drop-all')
    write(drop_all_path, """\
#!%s
import sys
sys.path = %r
import gocept.testdb.cmdline
gocept.testdb.cmdline.drop_all_entry_point()
""" % (sys.executable, sys.path))
    os.chmod(drop_all_path, os.stat(drop_all_path).st_mode | stat.S_IXUSR)
    test.sql_dir = tempfile.mkdtemp()
    test.globs.update(
        sql_dir=test.sql_dir,
        write=write,
        execute=execute,
        table_names=table_names,
        system=system(test),
        )


def tearDown(test):
    shutil.rmtree(test.sql_dir)
    shutil.rmtree(test.bin_dir)


class PostgreSQLRegressionTests(unittest.TestCase):

    db_template = 'gocept.testdb.tests-template'

    def drop_all(self):
        db = gocept.testdb.db.PostgreSQL(db_template=self.db_template)
        db.drop_all(drop_template=True)

    setUp = tearDown = drop_all

    def test_template_db_doesnt_need_schema(self):
        db = gocept.testdb.db.PostgreSQL(db_template=self.db_template)
        db.create()

    def test_naming_scheme_matches_with_dash_in_prefix(self):
        db = gocept.testdb.db.PostgreSQL(prefix='foo-bar')
        self.assertTrue(db._matches_db_naming_scheme('foo-bar-123'))


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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PostgreSQLRegressionTests))
    suite.addTest(unittest.makeSuite(StatusTests))
    suite.addTest(doctest.DocFileSuite(
        'README.txt',
        optionflags=doctest.ELLIPSIS
                    | doctest.NORMALIZE_WHITESPACE
                    | doctest.REPORT_NDIFF,
        setUp=setUp,
        tearDown=tearDown,
        ))
    return suite
