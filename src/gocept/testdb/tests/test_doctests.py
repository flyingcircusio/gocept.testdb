# Copyright (c) 2008-2013 gocept gmbh & co. kg
# See also LICENSE.txt

import doctest
import gocept.testdb
import gocept.testdb.db
import os
import os.path
import shutil
import sqlalchemy
import stat
import subprocess
import sys
import tempfile


def write(path, content):
    f = open(path, 'w')
    f.write(content)
    f.close()


def execute(dsn, cmd):
    engine = sqlalchemy.create_engine(dsn)
    conn = engine.connect()
    result = conn.execute(cmd)
    conn.invalidate()
    conn.close()
    return result


def table_names(dsn):
    engine = sqlalchemy.create_engine(dsn)
    conn = engine.connect()
    result = engine.table_names(connection=conn)
    conn.invalidate()
    conn.close()
    return result


def system(test):
    def system(cmdline):
        args = cmdline.split()
        args[0] = os.path.join(test.bin_dir, args[0])
        subprocess.call(args)
    return system


def list_testdb_names(db):
    pid = '-PID%s-' % os.getpid()
    return [x for x in db.list_db_names() if pid in x]


def setUp(test):
    test.bin_dir = tempfile.mkdtemp()
    drop_all_path = os.path.join(test.bin_dir, 'drop-all')
    write(drop_all_path, """\
#!%s
import sys
sys.path = %r
import gocept.testdb.cmdline
gocept.testdb.cmdline.drop_all_entry_point()
""" % (sys.executable, sys.path))
    os.chmod(drop_all_path, os.stat(drop_all_path).st_mode | stat.S_IXUSR)
    test.sql_dir = tempfile.mkdtemp()
    test.globs.update(
        sql_dir=test.sql_dir,
        write=write,
        execute=execute,
        table_names=table_names,
        system=system(test),
        list_testdb_names=list_testdb_names,
        )
    gocept.testdb.db.Database.prefix += '-PID%s' % os.getpid()


prefix = gocept.testdb.db.Database.prefix


def tearDown(test):
    gocept.testdb.db.Database.prefix = prefix
    shutil.rmtree(test.sql_dir)
    shutil.rmtree(test.bin_dir)


def test_suite():
    return doctest.DocFileSuite(
        'README.txt',
        optionflags=doctest.ELLIPSIS
                    | doctest.NORMALIZE_WHITESPACE
                    | doctest.REPORT_NDIFF,
        setUp=setUp,
        tearDown=tearDown,
        package=gocept.testdb,
        )
