import gocept.testdb.base
import os
import os.path
import shutil
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestCase(unittest.TestCase):
    """Base test case for package tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        self.sql_dir = tempfile.mkdtemp()
        self.schema = os.path.join(self.sql_dir, 'sample.sql')
        with open(self.schema, 'w') as schema:
            schema.write('CREATE TABLE foo (dummy int);')
        # We'll use a custom prefix specific to the current process whenever
        # we create fixed-name databases during this test, in order to allow
        # concurrent test runs on the same machine (such as a CI server):
        self.pid_prefix = 'gocept.testdb.tests-PID%s-' % os.getpid()
        self.db_template = self.pid_prefix + 'templatetest'
        self._orig_prefix = gocept.testdb.base.Database.prefix
        gocept.testdb.base.Database.prefix += '-PID%s' % os.getpid()

    def tearDown(self):
        super(TestCase, self).tearDown()
        gocept.testdb.base.Database.prefix = self._orig_prefix
        shutil.rmtree(self.sql_dir)
        #shutil.rmtree(test.bin_dir)

    def list_testdb_names(self, db):
        pid = '-PID%s-' % os.getpid()
        return [x for x in db.list_db_names() if pid in x]
