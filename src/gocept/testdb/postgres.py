from .base import Database
import os
import sqlalchemy
import subprocess


class PostgreSQL(Database):

    protocol = 'postgresql'
    environ_prefix = 'POSTGRES'

    def __init__(self, encoding=None, db_template=None,
                 force_template=False, lc_collate=None,
                 *args, **kw):
        super(PostgreSQL, self).__init__(*args, **kw)
        self.encoding = encoding
        self.db_template = db_template
        self.lc_collate = lc_collate
        self.force_template = force_template

    def login_args(self, command, extra_args=()):
        args = [
            command,
            '-h', self.db_host]
        if self.db_port:
            args.extend(['-p', self.db_port])
        if self.db_user:
            args.extend(['-U', self.db_user])
        args.extend(extra_args)
        return args

    def create(self):
        if self.db_template:
            try:
                self.create_template()
            except SystemExit as e:
                try:
                    self.drop_db(self.db_template)
                except:  # pragma: no cover
                    pass
                raise e
            try:
                self.create_db(
                    self.db_name,
                    db_template=self.db_template)
            except AssertionError:  # pragma: no cover
                raise SystemExit(
                    "Could not create database %r from template %r" %
                    (self.db_name, self.db_template))
        else:
            self.create_db_from_schema(self.db_name)

    def create_template(self):
        if self.schema_path is None:
            schema_mtime = 0
        else:
            schema_mtime = int(os.path.getmtime(self.schema_path))

        if self.db_template in self.list_db_names():
            template_mtime = self._get_db_mtime(self.db_template)
            if self.force_template or schema_mtime != template_mtime:
                self.drop_db(self.db_template)
            else:
                return

        self.create_db_from_schema(self.db_template)
        self._set_db_mtime(self.db_template, schema_mtime)

    def create_db(self, db_name, db_template=None, lc_collate=None):
        create_args = []
        if db_template is not None:
            create_args.extend(['-T', self.db_template])
        if self.lc_collate is not None:
            create_args.extend(['--lc-collate', self.lc_collate])
            create_args.extend(['-T', 'template0'])
        if self.encoding:
            create_args.extend(['-E', self.encoding])
        args = self.login_args('createdb', create_args + [db_name])
        assert 0 == subprocess.call(args), " ".join(args)

    def create_schema(self, db_name):
        assert 0 == subprocess.call(
            self.login_args(
                'psql', ['-f', self.schema_path,
                         '-v', 'ON_ERROR_STOP=true', '--quiet',
                         db_name]))

    def pg_list_db_items(self):
        # Use unaligned output to simplify splitting.
        raw_list, _ = subprocess.Popen(self.login_args('psql', ['-l', '-A']),
                                       stdout=subprocess.PIPE).communicate()
        result = []
        for line in raw_list.splitlines()[2:-1]:
            line = line.decode('us-ascii')
            if '|' in line:
                result.append(line.split('|'))
        return result

    def list_db_names(self):
        return [items[0] for items in self.pg_list_db_items()]

    def _get_db_mtime(self, database):
        dsn = self.get_dsn(database)
        conn = sqlalchemy.create_engine(dsn).connect()
        result = next(conn.execute(
            'SELECT schema_mtime FROM tmp_functest;').cursor)
        conn.invalidate()
        conn.close()
        if result:
            result = result[0]
        else:
            result = 0
        return result

    def _set_db_mtime(self, database, mtime):
        dsn = self.get_dsn(database)
        conn = sqlalchemy.create_engine(dsn).connect()
        conn.execute('INSERT INTO tmp_functest (schema_mtime) VALUES (%s);' %
                     mtime)
        conn.invalidate()
        conn.close()

    def drop_all(self, drop_template=False):
        for name in self.list_db_names():
            if (name == self.db_template and drop_template or
                    self._matches_db_naming_scheme(name)):
                self.drop_db(name)

    def drop_db(self, db_name):
        assert 0 == subprocess.call(self.login_args('dropdb', [db_name]))
