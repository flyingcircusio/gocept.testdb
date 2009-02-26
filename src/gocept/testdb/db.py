# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import os
import random
import subprocess
import time

import sqlalchemy


__all__ = ['MySQL', 'PostgreSQL']


class Database(object):
    protocol = None # set by subclass

    def __init__(self, schema_path=None, prefix='testdb'):
        self.schema_path = schema_path
        self.db_name = '%s-%i' % (prefix, random.randint(0, 9999))
        self.db_host = (os.environ.get('%s_HOST' % self.protocol.upper())
                       or 'localhost')
        self.db_user = os.environ.get('%s_USER' % self.protocol.upper())
        self.db_pass = os.environ.get('%s_PASS' % self.protocol.upper())

        login = ''
        if self.db_user:
            login += self.db_user
            if self.db_pass:
                login += ':' + self.db_pass
            login += '@'
        self.dsn = '%s://%s%s/%s' % (self.protocol, login, self.db_host,
                                     self.db_name)

    def create(self):
        self.create_db()
        if self.schema_path:
            self.create_schema()
        self.mark_testing()

    def create_db(self):
        db_result = subprocess.call(self.cmd_create)
        if db_result != 0:
            raise SystemExit("Could not create database %r" % self.db_name)

    def mark_testing(self):
        engine = sqlalchemy.create_engine(self.dsn)
        meta = sqlalchemy.MetaData()
        meta.bind = engine
        table = sqlalchemy.Table('tmp_functest', meta,
                                 sqlalchemy.Column('dummy', sqlalchemy.Integer))
        table.create()
        engine.dispose()

    def drop(self):
        def _drop():
            return subprocess.call(self.cmd_drop)
        db_result = _drop()
        if db_result != 0:
            # give the database some time to shut down
            time.sleep(1)
            db_result = _drop()
            if db_result != 0:
                raise RuntimeError("Could not drop database %r" % self.db_name)

    def create_schema(self):
        pass


class MySQL(Database):
    protocol = 'mysql'

    def __init__(self, *args, **kw):
        super(MySQL, self).__init__(*args, **kw)
        self.cmd_create = self.login_args(
                'mysqladmin', ['create', self.db_name])
        self.cmd_drop = self.login_args(
                'mysqladmin', ['--force', 'drop', self.db_name])
        self.create()

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


class PostgreSQL(Database):
    protocol = 'postgres'

    def __init__(self, *args, **kw):
        super(PostgreSQL, self).__init__(*args, **kw)
        self.cmd_create = self.login_args('createdb', [self.db_name])
        self.cmd_drop = self.login_args('dropdb', [self.db_name])
        self.create()

    def login_args(self, command, extra_args=()):
        args = [
            command,
            '--quiet', '-h', self.db_host]
        if self.db_user:
            args.extend(['-U', self.db_user])
        args.extend(extra_args)
        return args

    def create_schema(self):
        db_result = subprocess.call(self.login_args(
                'psql', ['-f', self.schema_path,
                         '-v', 'ON_ERROR_STOP=true',
                         self.db_name]))
        if db_result != 0:
            raise RuntimeError("Could not initialize schema in database %r." %
                               self.db_name)
