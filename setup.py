#!/usr/bin/env python
import os
import re
from setuptools import setup

PACKAGE_NAME = 'pyramid_addons'

HERE = os.path.abspath(os.path.dirname(__file__))
INIT = open(os.path.join(HERE, PACKAGE_NAME, '__init__.py')).read()
README = open(os.path.join(HERE, 'README.md')).read()
VERSION = re.search("__version__ = '([^']+)'", INIT).group(1)


setup(name=PACKAGE_NAME,
      version=VERSION,
      author='Bryce Boe',
      author_email='bbzbryce@gmail.com',
      url='https://github.com/bboe/pyramid_addons',
      description=('A package containing extra needed pyramid functionality '
                   'including helper functions and form validators.'),
      long_description=README,
      keywords='pyramid validation addons',
      classifiers=['Environment :: Console',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.2',
                   'Topic :: Utilities'],
      install_requires=['pyramid>=1.3', 'pytz'],
      packages=[PACKAGE_NAME],
      test_suite=PACKAGE_NAME)
