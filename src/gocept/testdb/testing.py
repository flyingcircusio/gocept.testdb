import gocept.testdb.base
import os
import os.path
import shutil
import sqlalchemy
import tempfile
import unittest


class TestCase(unittest.TestCase):
    """Base test case for package tests."""

    def setUp(self):
        super().setUp()
        self.sql_dir = tempfile.mkdtemp()
        self.schema = os.path.join(self.sql_dir, 'sample.sql')
        self.write(self.schema, 'CREATE TABLE foo (dummy int);')
        # We'll use a custom prefix specific to the current process whenever
        # we create fixed-name databases during this test, in order to allow
        # concurrent test runs on the same machine (such as a CI server):
        self.pid_prefix = 'gocept.testdb.tests-PID%s-' % os.getpid()
        self.db_template = self.pid_prefix + 'templatetest'
        self._orig_prefix = gocept.testdb.base.Database.prefix
        gocept.testdb.base.Database.prefix += '-PID%s' % os.getpid()

    def tearDown(self):
        super().tearDown()
        gocept.testdb.base.Database.prefix = self._orig_prefix
        shutil.rmtree(self.sql_dir)
        # shutil.rmtree(test.bin_dir)

    def list_testdb_names(self, db):
        pid = '-PID%s-' % os.getpid()
        return [x for x in db.list_db_names() if pid in x]

    def write(self, path, content):
        with open(path, 'w') as f:
            f.write(content)

    def connect(self, db):
        engine = db.create_engine()
        return engine.connect()

    def execute(self, dsn, cmd, fetch=False):
        engine = sqlalchemy.create_engine(dsn)
        with engine.begin() as conn:
            result = conn.execute(sqlalchemy.text(cmd))
            if fetch:
                result = result.fetchall()
        engine.dispose()
        return result

    def table_names(self, dsn):
        engine = sqlalchemy.create_engine(dsn)
        insp = sqlalchemy.inspect(engine)
        result = insp.get_table_names()
        engine.dispose()
        return result
