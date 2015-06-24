from .base import Database
import subprocess


class MySQL(Database):

    protocol = 'mysql+pymysql'
    environ_prefix = 'MYSQL'

    def __init__(self, schema_path=None, prefix=None, db_name=None,
                 cmd_postfix=''):
        return super(MySQL, self).__init__(schema_path, prefix, db_name)
        if cmd_postfix:
            self.cmd_postfix = cmd_postfix

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
