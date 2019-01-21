#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/core.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase, InputFileTestCase
import core
import exceptions

import tempfile
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


class TestArguments(InputFileTestCase):
    """Test the behaviour of core.main relative to its arguments."""

    def setUp(self):
        if self.output:  # Verify cleanup from previous test is cleaning up!
            assert not os.path.exists(self.output)
        temp_output = tempfile.NamedTemporaryFile(suffix=".xml")
        self.output = temp_output.name
        self.addCleanup(function=temp_output.close)

    def test_main_runs(self):
        input = self.good_input
        output = self.output

        core.main(input, output)

    def test_main_raises_pkg_exception(self):
        bad_inputs = [self.bad_input, self.decoy_input]
        expected_exception = exceptions.RecomposeError

        for filename in bad_inputs:
            input = filename
            output = self.output
            with self.subTest(input=input):
                with self.assertRaises(expected_exception):
                    core.main(input, output)


if __name__ == '__main__':
    unittest.main()
