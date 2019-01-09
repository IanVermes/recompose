#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of tests/base_testcases.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import CommandLineTestCase

import unittest
import os


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
