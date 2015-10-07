from setuptools import setup, find_packages
import os.path
import sys


def read(*path):
    return open(os.path.join(*path)).read() + '\n\n'


tests_require = [
    'gocept.testing',
    'mock',
    'psycopg2',
    'PyMySQL',
]

if sys.version_info < (2, 7):
    tests_require.append('unittest2')


setup(
    name='gocept.testdb',
    version='1.3',
    author='gocept <mail at gocept dot com>',
    author_email='mail@gocept.com',
    description='Creates and drops temporary databases for testing purposes.',
    long_description=(
        read('README.txt') +
        read('COPYRIGHT.txt') +
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
        test=tests_require),
    entry_points="""\
    [console_scripts]
    drop-all = gocept.testdb.cmdline:drop_all_entry_point
    """,
    classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: OSI Approved
License :: OSI Approved :: Zope Public License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: Implementation :: CPython
Topic :: Database
Topic :: Software Development :: Testing
Topic :: Utilities
"""[:-1].split('\n')
)
