import gocept.testdb.testing
import os.path
import shutil
import stat
import subprocess
import sys
import tempfile


class CommandlineTests(gocept.testdb.testing.TestCase):

    """Testing ``drop-all`` command-line script."""

    prefixes = {}

    def setUp(self):
        super(CommandlineTests, self).setUp()
        self.bin_dir = tempfile.mkdtemp()
        drop_all_path = os.path.join(self.bin_dir, 'drop-all')
        with open(drop_all_path, 'w') as f:
            f.write("""\
#!%s
import sys
sys.path = %r
import gocept.testdb.cmdline
gocept.testdb.cmdline.drop_all_entry_point()
""" % (sys.executable, sys.path))
        os.chmod(drop_all_path, os.stat(drop_all_path).st_mode | stat.S_IEXEC)

    def tearDown(self):
        try:
            shutil.rmtree(self.bin_dir)
            self._drop('MySQL')
        finally:
            try:
                self._drop('PostgreSQL')
            finally:
                self.prefixes = {}
                super(CommandlineTests, self).tearDown()

    def _make(self, name, create, prefix=None, suffix=None, **kw):
        import gocept.testdb
        cls = getattr(gocept.testdb, name)
        if prefix is None:
            prefix = self.pid_prefix
            if suffix:
                prefix += suffix
            self.prefixes.setdefault(name, []).append(prefix)
        db = cls(prefix=prefix, **kw)
        if create:
            db.create()
        return db

    def _drop(self, name):
        for prefix in self.prefixes.get(name, []):
            db = self._make(name, prefix=prefix, create=False)
            db.drop_all()
        self._make(name, create=False).drop_all()

    def makeMySQL(self, suffix=None, create=True):
        return self._make('MySQL', suffix=suffix, create=create)

    def makePostgreSQL(self, suffix=None, create=True, **kw):
        return self._make('PostgreSQL', suffix=suffix, create=create, **kw)

    def call_script(self, *args):
        args = list(args)
        args[0] = os.path.join(self.bin_dir, args[0])
        subprocess.call(args)

    def test_drops_mysql_and_postgresql_databases(self):
        # The Database classes' ``drop_all`` functionality is available
        # independently through a command-line script named ``drop-all``. The
        # script drops any test databases from both the PostgreSQL and MySQL
        # servers that match the test-database naming convention with any of
        # the prefixes passed as command-line arguments (clean up first):
        self.makeMySQL('foo')
        self.makeMySQL('bar')
        mysql = self.makeMySQL('bar')
        self.assertEqual(3, len(self.list_testdb_names(mysql)))

        self.makePostgreSQL('foo')
        self.makePostgreSQL('baz')
        self.makePostgreSQL('bar')
        postgres = self.makePostgreSQL('bar')
        self.assertEqual(4, len(self.list_testdb_names(postgres)))

        self.call_script(
            'drop-all', self.pid_prefix + 'foo', self.pid_prefix + 'bar')
        # All MySQL databases have been deleted because they matched the args:
        self.assertEqual(
            0, len(self.list_testdb_names(self.makeMySQL(create=False))))

        # There is one PG database left, the one with baz in the name.
        pg_dbs = self.list_testdb_names(self.makePostgreSQL(create=False))
        self.assertEqual(1, len(pg_dbs))
        self.assertIn('baz', pg_dbs[0])

    def test_drops_template_databases_on_postgresql(self):
        # On the PostgreSQL server, databases named exactly after any of the
        # names passed will also be dropped. This is how template databases can
        # be dropped without having to call ``drop-db`` on each of them:
        self.makePostgreSQL('foo', db_template=self.pid_prefix + 'bar')
        self.assertEqual(
            2, len(self.list_testdb_names(self.makePostgreSQL(create=False))))
        self.call_script(
            'drop-all', self.pid_prefix + 'foo', self.pid_prefix + 'bar')
        self.assertEqual(
            0, len(self.list_testdb_names(self.makePostgreSQL(create=False))))
