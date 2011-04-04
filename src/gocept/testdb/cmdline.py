# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.testdb.db
import sys


def drop_all(names):
    if names:
        for name in names:
            gocept.testdb.db.MySQL(prefix=name).drop_all()
            gocept.testdb.db.PostgreSQL(
                prefix=name, db_template=name).drop_all(drop_template=True)
    else:
        gocept.testdb.db.MySQL().drop_all()
        gocept.testdb.db.PostgreSQL().drop_all()


def drop_all_entry_point():
    drop_all(sys.argv[1:])
