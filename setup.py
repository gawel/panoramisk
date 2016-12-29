#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import os
from setuptools import setup
from setuptools import find_packages

version = '1.1'

install_requires = []
test_requires = [
    'pytest', 'pytest-asyncio', 'coverage', 'coveralls'
]


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name='panoramisk',
    version=version,
    description="asyncio based library to play with asterisk",
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications :: Telephony',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['asyncio', 'asterisk', 'voip'],
    author='Gael Pasgrimaud',
    author_email='gael@gawel.org',
    url='https://github.com/gawel/panoramisk/',
    license='MIT license',
    packages=find_packages(exclude=['docs', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=test_requires,
    extras_require={
        'test': test_requires,
    },
    entry_points='''
    [console_scripts]
    panoramisk = panoramisk.command:main
    '''
)
