# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import os
import random
import subprocess

import sqlalchemy


__all__ = ['MySQL']


class MySQL(object):
    def __init__(self, schema_path=None, prefix='testdb'):
        self.schema_path = schema_path
        self.db_name = '%s-%i' % (prefix, random.randint(0, 9999))
        self.db_host = os.environ.get('MYSQL_DATABASE_HOST') or 'localhost'
        self.db_user = os.environ.get('MYSQL_DATABASE_USER')
        self.db_pass = os.environ.get('MYSQL_DATABASE_PASS')

        login = ''
        if self.db_user:
            login += self.db_user
            if self.db_pass:
                login += ':' + self.db_pass
            login += '@'
        self.dsn = 'mysql://%s%s/%s' % (login, self.db_host, self.db_name)

        self.create_db()
        self.create_schema()
        self.mark_testing()

    def db_args(self, command, extra_args=()):
        args = [
            command,
            '-h', self.db_host]
        if self.db_user:
            args.extend(['-u', self.db_user])
        args.extend(extra_args)
        return args

    def create_db(self):
        db_result = subprocess.call(self.db_args(
                'mysqladmin', ['create', self.db_name]))
        if db_result != 0:
            raise SystemExit("Could not create database %r" %
                             self.db_name)

    def create_schema(self):
        if not self.schema_path:
            return
        db_input = subprocess.Popen(get_db_args(
                'mysql', [self.db_name]),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
        stdout, stderr = db_input.communicate(open(self.schema_path).read())
        if db_input.returncode != 0:
            print stderr
            raise SystemExit("Could not initialize schema in database %r." %
                             self.db_name)

    def mark_testing(self):
        engine = sqlalchemy.create_engine(self.dsn)
        meta = sqlalchemy.MetaData()
        meta.bind = engine
        table = sqlalchemy.Table('tmp_functest', meta,
                                 sqlalchemy.Column('dummy', sqlalchemy.Integer))
        table.create()

    def drop(self):
        def _drop():
            return subprocess.call(self.db_args(
                'mysqladmin', ['--force', 'drop', self.db_name]))
        db_result = _drop()
        if db_result != 0:
            # Give the database some time to shut down.
            time.sleep(1)
            db_result = drop()
            if db_result != 0:
                raise SystemExit("Could not drop database %r" %
                                 self.db_name)
