import gocept.testdb
import sys


def drop_mysql(name=None):
    try:
        if name is None:
            gocept.testdb.MySQL().drop_all()
        else:
            gocept.testdb.MySQL(prefix=name).drop_all()
    except OSError:  # pragma: no cover
        pass


def drop_postgresql(name=None):
    try:
        if name is None:
            gocept.testdb.PostgreSQL().drop_all()
        else:
            gocept.testdb.PostgreSQL(
                prefix=name, db_template=name).drop_all(drop_template=True)
    except OSError:  # pragma: no cover
        pass


def drop_all(names):
    if names:
        for name in names:
            drop_mysql(name)
            drop_postgresql(name)
    else:
        drop_mysql()
        drop_postgresql()


def drop_all_entry_point():
    drop_all(sys.argv[1:])
