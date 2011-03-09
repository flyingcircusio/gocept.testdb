# Copyright (c) 2008-2010 gocept gmbh & co. kg
# See also LICENSE.txt

import doctest
import shutil
import tempfile
import unittest


def write(path, content):
    f = open(path, 'w')
    f.write(content)
    f.close()


def setUp(test):
    test.sql_dir = tempfile.mkdtemp()
    test.globs.update(sql_dir=test.sql_dir, write=write)


def tearDown(test):
    shutil.rmtree(test.sql_dir)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite(
        'README.txt',
        optionflags=doctest.ELLIPSIS
                    | doctest.NORMALIZE_WHITESPACE
                    | doctest.REPORT_NDIFF,
        setUp=setUp,
        tearDown=tearDown,
        ))
    return suite
