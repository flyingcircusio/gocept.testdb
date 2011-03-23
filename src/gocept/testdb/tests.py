# Copyright (c) 2008-2011 gocept gmbh & co. kg
# See also LICENSE.txt

import doctest
import gocept.testdb.db
import shutil
import sqlalchemy
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


def setUp(test):
    test.sql_dir = tempfile.mkdtemp()
    test.globs.update(
        sql_dir=test.sql_dir,
        write=write,
        execute=execute,
        table_names=table_names,
        )


def tearDown(test):
    shutil.rmtree(test.sql_dir)


class PostgreSQLRegressionTests(unittest.TestCase):

    db_template = 'gocept.testdb.tests-template'

    def setUp(self):
        db = gocept.testdb.db.PostgreSQL()
        try:
            db.drop_db(self.db_template)
        except AssertionError:
            pass

    def tearDown(self):
        db = gocept.testdb.db.PostgreSQL()
        try:
            db.drop_db(self.db_template)
        except AssertionError:
            pass

    def test_template_db_doesnt_need_schema(self):
        db = gocept.testdb.db.PostgreSQL(db_template=self.db_template)
        db.create()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PostgreSQLRegressionTests))
    suite.addTest(doctest.DocFileSuite(
        'README.txt',
        optionflags=doctest.ELLIPSIS
                    | doctest.NORMALIZE_WHITESPACE
                    | doctest.REPORT_NDIFF,
        setUp=setUp,
        tearDown=tearDown,
        ))
    return suite
