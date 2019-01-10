#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of tests/base_testcases.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase, CommandLineTestCase

import tempfile
import unittest
import os


class Test_BaseTestCase_AssertMethods_Strings(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.string = """Lorem ipsum dolor sit amet, consectetur adipiscing
elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi
ut aliquip ex ea commodo consequat. Duis aute irure dolor in
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa
qui officia deserunt mollit anim id est laborum.
"""
        cls.all_subs = ["Lorem", "ipsum", "consequat", "dolor", "Excepteur",
                        "esse", "in", "est", "voluptate"]
        cls.some_overlap_subs = ["Lorem", "ipsum", "consequat", "foobar",
                                 "pedestrian", "doctor"]
        cls.no_subs = ["foobar", "George", "president", "light", "down",
                       "extinguish"]

    def test_all_substrings_present(self):
        subs = self.all_subs

        self.assertSubstringsInString(substrings=subs, string=self.string)


    def test_some_substrings_present(self):
        subs = self.some_overlap_subs

        with self.assertRaises(AssertionError) as failure:
            self.assertSubstringsInString(substrings=subs, string=self.string)

        err_msg_subs = ["3", "6", "unexpectly missing"] + subs[-3:]
        self.assertSubstringsInString(substrings=err_msg_subs,
                                      string=str(failure.exception).lower(),
                                      msg=f"orginal: {str(failure.exception)}")

    def test_no_substrings_present(self):
        subs = self.no_subs

        with self.assertRaises(AssertionError) as failure:
            self.assertSubstringsInString(substrings=subs, string=self.string)

        err_msg_subs = ["0", "6", "unexpectly missing"] + subs[-3:]
        self.assertSubstringsInString(substrings=err_msg_subs,
                                      string=str(failure.exception).lower(),
                                      msg=f"orginal: {str(failure.exception)}")

    def test_empty_substrings(self):
        subs = []

        with self.assertRaises(ValueError):
            self.assertSubstringsInString(substrings=subs, string=self.string)

    def test_string_not_list_as_substring(self):
        subs_present = "Lorem ipsum dolor"
        subs_absent = "This archaic concept"

        self.assertSubstringsInString(substrings=subs_present,
                                      string=self.string)
        with self.assertRaises(AssertionError):
            self.assertSubstringsInString(substrings=subs_absent,
                                          string=self.string)

    def test_empty_string(self):
        subs = self.some_overlap_subs

        with self.assertRaises(ValueError):
            self.assertSubstringsInString(substrings=subs, string="")


class Test_BaseTestCase_AssertMethods_Files(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.extant_file = "/usr/bin/python"
        assert os.path.isfile(cls.extant_file)
        cls.imaginary_file = "/usr/bin/foofoobarbar"
        assert not os.path.isfile(cls.imaginary_file)

        cls.extant_dir = "/usr/bin"
        assert os.path.isdir(cls.extant_dir)

    def test_file_in_directory(self):
        filename = self.extant_file
        dirname = self.extant_dir

        self.assertFileInDirectory(file=filename, directory=dirname)

        with self.assertRaises(AssertionError):
            self.assertFileNotInDirectory(file=filename, directory=dirname)

    def test_file_not_in_directory(self):
        filename = self.imaginary_file
        dirname = self.extant_dir

        self.assertFileNotInDirectory(file=filename, directory=dirname)

        with self.assertRaises(AssertionError):
            self.assertFileInDirectory(file=filename, directory=dirname)

    def test_temp_file_in_directory(self):
        with tempfile.NamedTemporaryFile() as handle:
            filename = handle.name
            dirname = os.path.dirname(filename)

            self.assertTrue(os.path.exists(filename))
            self.assertFileInDirectory(file=filename, directory=dirname)

        # Context manager closes/deletes the tempfile
        self.assertTrue(os.path.exists(False))
        self.assertFileNotInDirectory(file=filename, directory=dirname)



class Test_CommandLineTestCase_Itself(CommandLineTestCase):

    @classmethod
    def setUpClass(cls):
        cls.cmd_echo = "echo foobar"
        cls.cmd_template_ls = 'ls -l {filename}'

    def test_format_cmd_untouched(self):
        expected = 'echo foobar'
        formatted = self.format_cmd(self.cmd_echo, {})

        self.assertEqual(formatted, expected)

    def test_format_cmd(self):
        naughty_filename = 'somefile; rm -rf ~'
        expected = "ls -l \'somefile; rm -rf ~\'"
        forbidden = self.cmd_template_ls.format(filename=naughty_filename)

        substrings = {"filename": naughty_filename}
        formatted = self.format_cmd(self.cmd_template_ls, substrings)

        self.assertEqual(formatted, expected)
        self.assertNotEqual(formatted, forbidden)

    def test_format_cmd_complex(self):
        filename = os.path.expanduser('~/Desktop')
        template = "test -a {filename}; echo $?"
        expected = "test -a /Users/Ian/Desktop; echo $?"

        substrings = {"filename": filename}
        formatted = self.format_cmd(template, substrings)

        self.assertEqual(formatted, expected)

    def test_format_cmd_bad_template(self):
        substrings = {"fname": "~/Desktop"}
        bad_template = "ls -l {"

        with self.assertRaises(TypeError):
            self.format_cmd(bad_template, substrings)

    def test_format_cmd_bad_dict(self):
        substrings = {"fname": "~/Desktop"}

        with self.assertRaises(TypeError):
            self.format_cmd(self.cmd_template_ls, substrings)

    def test_invoke_cmd_passing(self):
        given_status = 0
        expected_stdout = "foobar"
        cmd = self.cmd_echo

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout)

    def test_invoke_cmd_passing_complex(self):
        given_status = 0
        expected_stdout = "0"
        cmd_template = "test -a {filename}; echo $?"
        filename = os.path.expanduser("/")

        cmd = self.format_cmd(cmd_template, {"filename": filename})

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout, msg=cmd)

    def test_invoke_cmd_failing_complex(self):
        given_status = 0
        # echo execution is successful but "1" reported by test
        expected_stdout = "1"
        cmd_template = "test -a {filename}; echo $?"
        filename = os.path.expanduser("~/FooBar")

        cmd = self.format_cmd(cmd_template, {"filename": filename})

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout, msg=repr(cmd))

    def test_invoke_cmd_failing(self):
        given_status = 1
        expected_stdout = "dirname: illegal option -- h\nusage: dirname path"
        cmd = "dirname -h"

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout)

    def test_invoke_cmd_user_gives_wrong_status(self):
        given_status = 0  # cmd is failing so 1 is status
        cmd = "dirname -h"  # -h is not a legal parameter of dirname

        with self.assertRaises(AssertionError):
            self.invoke_cmd_via_commandline(cmd, given_status)
