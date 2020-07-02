import os
import sqlalchemy
import time


class Database(object):

    protocol = NotImplemented
    environ_prefix = NotImplemented

    prefix = 'testdb'

    def __init__(self, schema_path=None, prefix=None, db_name=None):
        self.schema_path = schema_path
        if prefix is not None:
            self.prefix = prefix
        if db_name:
            self.db_name = db_name
        else:
            self.db_name = '%s-%f' % (self.prefix, time.time())
        self.db_host = (
            os.environ.get('%s_HOST' % self.environ_prefix) or 'localhost')
        self.db_port = os.environ.get('%s_PORT' % self.environ_prefix)
        self.db_user = os.environ.get('%s_USER' % self.environ_prefix)
        self.db_pass = os.environ.get('%s_PASS' % self.environ_prefix)
        self.cmd_postfix = os.environ.get(
            '%s_COMMAND_POSTFIX' % self.environ_prefix) or ''
        self.dsn = self.get_dsn(self.db_name)

    def get_dsn(self, db_name):
        login = ''
        if self.db_user:
            login += self.db_user
            if self.db_pass:
                login += ':' + self.db_pass
            login += '@'
        host = self.db_host
        if self.db_port:
            host = '{}:{}'.format(host, self.db_port)
        return '{proto}://{login}{host}/{name}'.format(
            proto=self.protocol, login=login, host=host, name=db_name)

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
        except AssertionError as e:
            raise SystemExit("Could not create database %r\n%s" % (db_name, e))
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
        raise NotImplementedError

    def create_schema(self, db_name):
        """Implementation of how to load a schema into an existing database.

        Depends on the choice of database engine. Raises AssertionError if the
        schema couldn't be loaded.

        """
        raise NotImplementedError

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
        """Return a list of names of all databases that exist on the server.

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
            except AssertionError:  # pragma: no cover
                # give the database some time to shut down
                time.sleep(1)
        else:  # pragma: no cover
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
