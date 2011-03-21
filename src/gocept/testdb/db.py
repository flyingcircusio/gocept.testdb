# Copyright (c) 2008-2011 gocept gmbh & co. kg
# See also LICENSE.txt

import os
import random
import subprocess
import time

import sqlalchemy


__all__ = ['MySQL', 'PostgreSQL']


class Database(object):

    protocol = NotImplemented
    cmd_create = NotImplemented

    def __init__(self, schema_path=None, prefix='testdb', db_name=None):
        self.schema_path = schema_path
        if db_name:
            self.db_name = db_name
        else:
            self.db_name = '%s-%i' % (prefix, random.randint(0, 9999))
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
        self.create_db_from_schema()

    def create_db_from_schema(self):
        """Recipe for how to create a database from a schema.

        Independent of the choice of database engine.

        """
        try:
            self.create_db()
        except AssertionError:
            raise SystemExit("Could not create database %r" % self.db_name)
        if self.schema_path:
            self.create_schema()
        self.mark_testing(self.db_name)

    def create_db(self):
        assert 0 == subprocess.call(self.cmd_create)

    def create_schema(self):
        raise NotImplementedError()

    def mark_testing(self, db_name):
        engine = sqlalchemy.create_engine(self.get_dsn(db_name))
        meta = sqlalchemy.MetaData()
        meta.bind = engine
        table = sqlalchemy.Table(
            'tmp_functest', meta,
            sqlalchemy.Column('schema_mtime', sqlalchemy.Integer))
        table.create()
        engine.dispose()

    def drop(self):
        """Protocol entry point for tearing down the database on the server.

        Contains retry logic independent from the choice of database engine.

        """
        try:
            self.drop_db(self.db_name)
        except AssertionError:
            # give the database some time to shut down
            time.sleep(1)
            try:
                self.drop_db(self.db_name)
            except AssertionError:
                raise RuntimeError("Could not drop database %r" % self.db_name)

    def drop_db(self, db_name):
        """Implementation of dropping a database on the server.

        Depends on the choice of database engine. Raises AssertionError if the
        server couldn't drop the database.

        """
        raise NotImplementedError


class MySQL(Database):

    protocol = 'mysql'

    def __init__(self, *args, **kw):
        super(MySQL, self).__init__(*args, **kw)
        self.cmd_create = self.login_args(
                'mysqladmin', ['create', self.db_name])

    def login_args(self, command, extra_args=()):
        args = [
            command,
            '-h', self.db_host]
        if self.db_user:
            args.extend(['-u', self.db_user])
        if self.db_pass:
            args.extend(['-p' + self.db_pass])
        args.extend(extra_args)
        return args

    def create_schema(self):
        db_input = subprocess.Popen(self.login_args(
                'mysql', [self.db_name]),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
        stdout, stderr = db_input.communicate(open(self.schema_path).read())
        if db_input.returncode != 0:
            print stderr
            raise RuntimeError("Could not initialize schema in database %r." %
                               self.db_name)

    def drop_db(self, db_name):
        assert 0 == subprocess.call(
            self.login_args('mysqladmin', ['--force', 'drop', db_name]))


class PostgreSQL(Database):

    protocol = 'postgresql'

    def __init__(self, encoding=None, db_template=None, force_template=False,
                 *args, **kw):
        super(PostgreSQL, self).__init__(*args, **kw)
        self.encoding = encoding
        self.db_template = db_template
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
        create_args = [self.db_name]
        if self.encoding:
            create_args[0:0] = ['-E', self.encoding]
        if self.db_template:
            self.create_template(create_args[:-1])
            create_args[0:0] = ['-T', self.db_template]
            self.cmd_create = self.login_args('createdb', create_args)
            try:
                self.create_db()
            except AssertionError:
                raise SystemExit(
                    "Could not create database %r from template %r" %
                    (self.db_name, self.db_template))
        else:
            self.cmd_create = self.login_args('createdb', create_args)
            self.create_db_from_schema()

    def create_template(self, create_args):
        schema_mtime = int(os.path.getmtime(self.schema_path))

        if self._db_exists(self.db_template):
            template_mtime = self._get_db_mtime(self.db_template)
            if self.force_template or schema_mtime != template_mtime:
                self.drop_db(self.db_template)
            else:
                return

        db_result = subprocess.call(self.login_args(
            'createdb', create_args + [self.db_template]))
        if db_result != 0:
            raise SystemExit(
                'Could not create template database %s.' % self.db_template)
        self.create_schema(db_name=self.db_template)
        self.mark_testing(self.db_template)
        self._set_db_mtime(self.db_template, schema_mtime)

    def create_schema(self, db_name=None):
        db_name = db_name or self.db_name
        db_result = subprocess.call(self.login_args(
                'psql', ['-f', self.schema_path,
                         '-v', 'ON_ERROR_STOP=true', '--quiet',
                         db_name]))
        if db_result != 0:
            raise RuntimeError("Could not initialize schema in database %r." %
                               db_name)

    def _db_exists(self, database):
        dbs, _ = subprocess.Popen(self.login_args('psql', ['-l']),
                               stdout=subprocess.PIPE).communicate()
        for line in dbs.splitlines():
            if line.split('|')[0].strip() == database:
                return True
        else:
            return False

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

    def drop_db(self, db_name):
        assert 0 == subprocess.call(self.login_args('dropdb', [db_name]))
