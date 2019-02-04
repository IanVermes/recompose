#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/core.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase, InputFileTestCase
import core
import exceptions

import testfixtures

import tempfile
import unittest
import unittest.mock
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

    @unittest.mock.patch("exceptions.RecomposeExit.clean_exit")
    def test_main_raises_pkg_exception(self, mock_clean_exit):
        bad_inputs = [self.bad_input, self.decoy_input, self.track_changes_input]
        pkg_exception = exceptions.RecomposeError
        expected_exception = exceptions.RecomposeExit

        for filename in bad_inputs:
            input = filename
            output = self.output
            with testfixtures.OutputCapture():
                with self.subTest(input=input):
                    with self.assertRaises(Exception) as fail:
                        core.main(input, output)
                    mock_clean_exit.assert_called()  # SystemExit suppressed.
                    self.assertIsInstance(fail.exception, pkg_exception)
                    self.assertIsInstance(fail.exception, expected_exception)



if __name__ == '__main__':
    unittest.main()
