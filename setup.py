# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

from setuptools import setup, find_packages

setup(
    name='gocept.testdb',
    version='0.1dev',
    author='gocept',
    author_email='mail@gocept.com',
    description='Creates and drops temporary databases for testing purposes.',
    long_description = (
        open(os.path.join('src', 'gocept', 'testdb', 'README.txt')).read()
    ),
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    namespace_packages=['gocept'],
    install_requires=[
        'setuptools',
        'SQLAlchemy',
        ],
    extras_require=dict(
        test=[
            'zope.testing',
            'MySQL-python',
            'psycopg2',
            ]),
)
