#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module simplifies the importing of package modules within testsuites.

Though the top level folder is 'recompose' it is not a package in its own
right: there is not recompose.__init__.py.

recompose.tests and recompose.main cannot 'see' eachother, they are each
packages in their own right and hence to let 'main' become visible to
'tests' and hence 'unittest' itself sys.path has the main package path
insterted.

This module is used during testing only and is imported by base_testcases,
however you can make use of it by importing it before importing
validator modules.

>>> import context
>>> import <some main pkg module>

or

>>> from tests.base_testcases import ExtendedTestCase
>>> import <some main pkg module>

Copyright: Ian Vermes 2019
"""


import sys
import os

PACKAGE_DIR = '../main/'  # Relative to this file.


def add_packagedir_to_syspath(relative_dir):
    """Insert relative dir to sys.path, to facilitate import of pkg modules."""
    pythonpaths = sys.path
    package_dir = os.path.join(os.path.dirname(__file__), relative_dir)
    if not os.path.isdir(package_dir):
        msg = f"Cannot perform tests, test suite cannot find '{package_dir}'"
        raise NotADirectoryError(msg)
    if package_dir in pythonpaths:
        return
    else:
        # Do not reinsert if called more than once.
        sys.path.insert(0, os.path.abspath(package_dir))
        return


def main():
    """While testing, allow imports from another top level directory/package."""
    package_dir = PACKAGE_DIR
    add_packagedir_to_syspath(package_dir)


if __name__ == '__main__':
    main()

    modulename = 'core'
    import core

    if modulename in sys.modules:
        print(f"""You have imported the '{modulename}' module.""")
