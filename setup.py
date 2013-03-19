# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
from setuptools import setup, find_packages


def read(*path):
    return open(os.path.join(*path)).read() + '\n\n'

setup(
    name='gocept.testdb',
    version='1.1.1',
    author='gocept <mail at gocept dot com>',
    author_email='mail@gocept.com',
    description='Creates and drops temporary databases for testing purposes.',
    long_description=(
        read('README.txt') +
        '.. contents:: :depth: 1\n\n' +
        read('src', 'gocept', 'testdb', 'README.txt') +
        read('HACKING.txt') +
        read('CHANGES.txt')
        ),
    url='https://bitbucket.org/gocept/gocept.testdb',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    namespace_packages=['gocept'],
    install_requires=[
        'setuptools',
        'SQLAlchemy >= 0.5.6',
        ],
    extras_require=dict(
        test=[
            'zope.testing',
            'MySQL-python',
            'psycopg2',
            'mock',
            ]),
    entry_points="""\
    [console_scripts]
    drop-all = gocept.testdb.cmdline:drop_all_entry_point
    """,
    classifiers = """\
License :: OSI Approved :: Zope Public License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 2 :: Only
"""[:-1].split('\n')
)
