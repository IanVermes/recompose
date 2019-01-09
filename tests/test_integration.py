#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Integration test of core.py.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import CommandLineTestCase
from main import core

import unittest
import os


class UserStories_CommandLine(CommandLineTestCase):

    @classmethod
    def setUpClass(cls):
        absolute = os.path.abspath
        exists = os.path.isfile
        cls.good_file = absolute("./resources/Pretty BR Autumn 2018.xml")
        cls.bad_file = absolute("./resources/BR Autumn 2018.docx")
        files = (cls.good_file, cls.bad_file)
        assert all([exists(f) for f in files]), {f: exists(f) for f in files}

        cmd_basic_template = "python {filename_script}"
        core_py = absolute(core.__file__)
        cls.cmd_basic = cls.format_cmd(cmd_basic_template,
                                       {"filename_script": core_py})
        assert "filename_script" not in cls.cmd_basic

    def test_command_line_entry_basic(self):
        # User invokes main.core
        cmd = self.cmd_basic

        # Program exits suddenly
        status = 1
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User given help info
        self.assertTrue(stdout)
        self.assertIn("help", stdout.lower())

class UserStories_CommandLine(CommandLineTestCase):

    @classmethod
    def setUpClass(cls):
        absolute = os.path.abspath
        exists = os.path.isfile
        cls.good_file = absolute("./resources/Pretty BR Autumn 2018.xml")
        cls.bad_file = absolute("./resources/BR Autumn 2018.docx")
        files = (cls.good_file, cls.bad_file)
        assert all([exists(f) for f in files]), {f: exists(f) for f in files}

        cmd_basic_template = "python {filename_script}"
        core_py = absolute(core.__file__)
        cls.cmd_basic = cls.format_cmd(cmd_basic_template,
                                       {"filename_script": core_py})
        assert "filename_script" not in cls.cmd_basic

    @unittest.expectedFailure
    def test_command_line_entry_basic(self):
        # User invokes main.core
        cmd = self.cmd_basic

        # Program exits suddenly
        status = 1
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User given help info
        self.assertTrue(stdout)
        self.assertIn("help", stdout.lower())

    @unittest.expectedFailure
    def test_command_line_entry_correct(self):
        # User invokes main.core with an XML file
        cmd_template = self.cmd_basic + " {file_argument}"
        substring = {"file_argument": self.good_file}
        cmd = self.format_cmd(cmd_template, substring)

        # Program exits cleanly
        status = 0
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User sees nothing in stdout, all assumed to go well
        self.assertFalse(stdout)

        # Program yields output.xml file in same directory as input
        output_filename = "output.xml"
        target_dir = os.path.dirname(self.good_file)
        files = set(os.path.basename(f) for f in os.listdir(target_dir))
        self.assertIn(output_filename, files)

        # Program yields output.xml file in same directory as input
        output_filename = "output.xml"
        target_dir = os.path.dirname(self.good_file)
        files = set(os.path.basename(f) for f in os.listdir(target_dir))
        self.assertIn(output_filename, files)

    @unittest.expectedFailure
    def test_command_line_entry_bad_file(self):
        # User invokes main.core without an XML file
        cmd_template = self.cmd_basic + " {file_argument}"
        substring = {"file_argument": self.bad_file}
        cmd = self.format_cmd(cmd_template, substring)

        # Program exits abruptly
        status = 0
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User informed of bad file in commandline
        self.assertTrue(stdout)
        self.assertIn("incompatible", stdout.lower())
        self.assertIn("error", stdout.lower())
        self.assertIn("save as...", stdout.lower())
        self.assertIn("xml", stdout.lower())

    @unittest.expectedFailure
    def test_command_line_entry_no_file(self):
        # User invokes main.core with no arguments
        cmd = self.cmd_basic + " "

        # Program exits abruptly
        status = 1
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User informed of expected argument
        self.assertTrue(stdout)
        self.assertIn("default", stdout.lower())

    @unittest.expectedFailure
    def test_command_line_entry_help(self):
        # User invokes main.core with help argument
        cmd = self.cmd_basic + " -h"

        # Program exits cleanly
        status = 0
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User provided helpful information
        self.assertTrue(stdout)
        self.assertIn("help", stdout.lower())


if __name__ == '__main__':
    unittest.main()
