#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/core.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase
import core
import exceptions

import unittest
import os


class TestPrimitive(BaseTestCase):
    """Basic test cases."""

    def test_absolute_truth_and_meaning(self):
        truth = True
        self.assertTrue(truth)

    def test_import_of_module(self):
        primitive = core._TestingPrimitive()

        flag = primitive.verify_import_tester()

        self.assertTrue(flag)

    def test_raising_root_exceptions(self):
        root_exception = exceptions.RecomposeError
        primitive = core._TestingPrimitive()

        with self.assertRaises(root_exception):
            primitive.raise_package_error()


if __name__ == '__main__':
    unittest.main()
