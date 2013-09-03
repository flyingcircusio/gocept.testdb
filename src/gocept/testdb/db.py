# Copyright (c) 2008-2013 gocept gmbh & co. kg
# See also LICENSE.txt

import os
import subprocess
import time

import sqlalchemy


__all__ = ['MySQL', 'PostgreSQL']


class Database(object):

    protocol = NotImplemented

    prefix = 'testdb'

    def __init__(self, schema_path=None, prefix=None, db_name=None):
        self.schema_path = schema_path
        if prefix is not None:
            self.prefix = prefix
        if db_name:
            self.db_name = db_name
        else:
            self.db_name = '%s-%f' % (self.prefix, time.time())
        self.db_host = (os.environ.get('%s_HOST' % self.protocol.upper())
                       or 'localhost')
        self.db_user = os.environ.get('%s_USER' % self.protocol.upper())
        self.db_pass = os.environ.get('%s_PASS' % self.protocol.upper())
        self.dsn = self.get_dsn(self.db_name)

    def get_dsn(self, db_name):
        login = ''
        if self.db_user:
            login += self.db_user
            if self.db_pass:
                login += ':' + self.db_pass
            login += '@'
        return '%s://%s%s/%s' % (self.protocol, login, self.db_host, db_name)

    def create(self):
        """Protocol entry point for setting up the database on the server.

        Implementation may be optimised, for example for PostgreSQL to use
        template databases.

        """
        self.create_db_from_schema(self.db_name)

    def create_db_from_schema(self, db_name):
        """Recipe for how to create a database from a schema.

        Independent of the choice of database engine.

        """
        try:
            self.create_db(db_name)
        except AssertionError:
            raise SystemExit("Could not create database %r" % db_name)
        if self.schema_path:
            try:
                self.create_schema(db_name)
            except AssertionError:
                raise SystemExit(
                    "Could not initialize schema in database %r." % db_name)
        self.mark_testing(db_name)

    def create_db(self, db_name):
        """Implementation of creating an empty database on the server.

        Depends on the choice of database engine. Raises AssertionError if the
        database couldn't be created.

        """
        raise NotImplementedError()

    def create_schema(self, db_name):
        """Implementation of how to load a schema into an existing database.

        Depends on the choice of database engine. Raises AssertionError if the
        schema couldn't be loaded.

        """
        raise NotImplementedError()

    def connect(self):
        return sqlalchemy.create_engine(self.get_dsn(self.db_name))

    def mark_testing(self, db_name):
        engine = sqlalchemy.create_engine(self.get_dsn(db_name))
        meta = sqlalchemy.MetaData()
        meta.bind = engine
        table = sqlalchemy.Table(
            'tmp_functest', meta,
            sqlalchemy.Column('schema_mtime', sqlalchemy.Integer))
        table.create()
        engine.dispose()

    @property
    def is_testing(self):
        engine = self.connect()
        try:
            try:
                engine.connect().execute('SELECT * from tmp_functest')
                return True
            except:
                return False
        finally:
            engine.dispose()

    @property
    def exists(self):
        engine = self.connect()
        try:
            try:
                engine.connect()
                return True
            except:
                return False
        finally:
            engine.dispose()

    def list_db_names(self):
        """Returns a list of names of all databases that exist on the server.

        Implementation depends on choice of database engine.

        """
        raise NotImplementedError

    def drop(self):
        """Protocol entry point for tearing down the database on the server.

        Contains retry logic independent from the choice of database engine.

        """
        for i in range(3):
            if self.db_name not in self.list_db_names():
                break
            try:
                self.drop_db(self.db_name)
            except AssertionError:
                # give the database some time to shut down
                time.sleep(1)
        else:
            raise RuntimeError("Could not drop database %r" % self.db_name)

    def drop_all(self):
        """Protocol entry point for dropping all test dbs on the server.

        May need to be overridden in a given Database implementation, for
        example to deal with PostgreSQL's template databases.

        """
        for name in self.list_db_names():
            if self._matches_db_naming_scheme(name):
                self.drop_db(name)

    def drop_db(self, db_name):
        """Implementation of dropping a database on the server.

        Depends on the choice of database engine. Raises AssertionError if the
        server couldn't drop the database.

        """
        raise NotImplementedError

    def _matches_db_naming_scheme(self, name):
        """Check whether name fits the db naming scheme applied by __init__.

        """
        pieces = name.rsplit('-', 1)
        if len(pieces) != 2:
            return False
        if pieces[0] != self.prefix:
            return False
        try:
            float(pieces[1])
        except ValueError:
            return False
        return True


class MySQL(Database):

    protocol = 'mysql'

    def __init__(self, schema_path=None, prefix=None, db_name=None,
                 cmd_postfix=''):
        self.cmd_postfix = cmd_postfix
        return super(MySQL, self).__init__(schema_path, prefix, db_name)

    def login_args(self, command, extra_args=()):
        args = [
            command + self.cmd_postfix,
            '-h', self.db_host]
        if self.db_user:
            args.extend(['-u', self.db_user])
        if self.db_pass:
            args.extend(['-p' + self.db_pass])
        args.extend(extra_args)
        return args

    def create_db(self, db_name):
        assert 0 == subprocess.call(
            self.login_args('mysqladmin', ['create', db_name]))

    def create_schema(self, db_name):
        assert 0 == subprocess.call(
            self.login_args('mysql', [db_name]), stdin=open(self.schema_path))

    def list_db_names(self):
        raw_list, _ = subprocess.Popen(self.login_args('mysqlshow'),
                                       stdout=subprocess.PIPE).communicate()
        return [line.decode('us-ascii').split()[1]
                for line in raw_list.splitlines()[3:-1]]

    def drop_db(self, db_name):
        assert 0 == subprocess.call(
            self.login_args('mysqladmin', ['--force', 'drop', db_name]))


class PostgreSQL(Database):

    protocol = 'postgresql'

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
                except:
                    pass
                raise e
            try:
                self.create_db(
                    self.db_name,
                    db_template=self.db_template)
            except AssertionError:
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
        assert 0 == subprocess.call(
            self.login_args('createdb', create_args + [db_name]))

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
        result = conn.execute(
            'SELECT schema_mtime FROM tmp_functest;').cursor.next()
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
