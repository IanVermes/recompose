#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Include module, class and function doctests strings to the test suite.

The helper functions discover documentation in the package code with Python
interpretor notation. This unit test is discoverable by the unittest module.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import BaseTestCase

import glob
import unittest
import doctest
import importlib


class DocTest_Module_Documentation(BaseTestCase):

    def test_helper_func_FIND(self):
        files = find_code_with_doctests()
        self.assertGreater(len(files), 0)

    def test_helper_func_GET(self):
        files = find_code_with_doctests()

        try:
            modules = get_modules_by_filename(files)
        except ImportError as err:
            assertmsg = f"Expected no excetions: got {repr(err)}."
            raise AssertionError(assertmsg) from None

        self.assertEqual(len(files), len(modules))


def find_code_with_doctests():
    """Naive search for modules with any doctests strings."""
    candidate = []
    for file in glob.iglob("**/*.py", recursive=True):
        if "main/" not in file:
            continue
        else:
            with open(file) as handle:
                if ">>>" in handle.read():
                    candidate.append(file)
    return candidate


def get_modules_by_filename(files):
    """Get modules from their code file."""
    modules = dict()
    for file in files:
        path = file.strip(".py")
        path = path.replace("/", ".")
        try:
            module = importlib.import_module(path)
        except ImportError as err:
            print(f"Bad import: module path {path} derived from {file}.")
            print(f"Exception: {err}")
            raise
        else:
            modules[file] = module
    return modules


def load_tests(loader, tests, ignore):
    """Add doctests to discovered unittests.

    https://docs.python.org/3/library/doctest.html#unittest-api
    """
    modules = get_modules_by_filename(find_code_with_doctests())
    for file, module in modules.items():
        tests.addTests(doctest.DocTestSuite(module))
    return tests


if __name__ == '__main__':
    unittest.main()
