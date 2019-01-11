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
        # Get input files
        absolute = os.path.abspath
        exists = os.path.isfile
        cls.good_file = absolute("./resources/Pretty BR Autumn 2018.xml")
        cls.bad_file = absolute("./resources/BR Autumn 2018.docx")
        files = (cls.good_file, cls.bad_file)
        assert all([exists(f) for f in files]), {f: exists(f) for f in files}

        # Get default output filename
        argparser = core.RecomposeArgParser()
        cls.default_output_filename = argparser.default_output()
        assert not os.path.exists(cls.default_output_filename)

        # Format commandline cmd
        cmd_basic_template = "python {filename_script}"
        core_py = absolute(core.__file__)
        cls.cmd_basic = cls.format_cmd(cmd_basic_template,
                                       {"filename_script": core_py})
        assert "filename_script" not in cls.cmd_basic

    @property
    def output_file(self):
        return self._output_file

    @output_file.setter
    def output_file(self, value):
        self._output_file = value
        try:
            self._output_file_list.append(value)
        except AttributeError:
            self._output_file_list = [value]

    def clear_output_files(self):
        try:
            output_files = self._output_file_list
        except AttributeError:
            # Forgive unset attribute as no files were ever set to remove
            return
        else:
            for filename in output_files:
                if filename and os.path.exists(filename):
                    os.remove(filename)
            self.output_file = ""

    def setUp(self):
        # This variable is not local to test methods so that the tearDown
        # method can catch the filename when out of test scope. The setUp
        # method resets the value between tests as a precaution.
        self.output_file = ""

    def tearDown(self):
        # The output file is removed after each test
        self.clear_output_files()

    def test_command_line_entry_basic(self):
        # User invokes main.core
        cmd = self.cmd_basic

        # Program exits suddenly
        status = 1
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User given help info
        self.assertTrue(stdout)
        self.assertIn("usage", stdout.lower())

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

        # Program yields defualt output file in the current working directory
        self.output_file = self.default_output_filename
        self.assertFileInDirectory(file=self.output_file, directory=os.getcwd())

    def test_command_line_entry_correct_with_output_argument(self):

        def user_story(self, output_file):
            # User invokes main.core with an XML file and specified output
            cmd_template = self.cmd_basic + " {file_argument}" + " {file_output}"
            self.output_file = output_file
            substring = {"file_argument": self.good_file,
                         "file_output": self.output_file}
            cmd = self.format_cmd(cmd_template, substring)

            # Program exits cleanly
            status = 0
            stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

            # User sees nothing in stdout, all assumed to go well
            self.assertFalse(stdout)

            # Program yields output file at location specified
            self.assertFileInDirectory(file=self.output_file, directory=os.path.dirname(self.output_file))

            # Program does not name the output file with the default value
            self.assertFileNotInDirectory(file=self.default_output_filename, directory=os.getcwd())
            self.assertNotEqual(self.default_output_filename, self.output_file)

        expanduser = os.path.expanduser
        abspath = os.path.abspath
        basename = "custom_output.xml"
        user_specified_filenames = [expanduser(f"~/Desktop/{basename}"),
                                    "foo" + basename,
                                    abspath(basename)]
        for output_filename in user_specified_filenames:
            with self.subTest(filename=output_filename):
                user_story(self, output_file=output_filename)

    def test_command_line_entry_bad_file(self):
        # User invokes main.core without an XML file
        cmd_template = self.cmd_basic + " {file_argument}"
        substring = {"file_argument": self.bad_file}
        cmd = self.format_cmd(cmd_template, substring)

        # Program exits abruptly
        status = 1
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # No output file is made
        self.output_file = self.default_output_filename
        self.assertFileNotInDirectory(file=self.output_file, directory=os.getcwd())

        # User informed of bad file in commandline
        self.assertTrue(stdout)
        subs = ["incompatible", "error", "microsoft word", "save as...", "xml"]
        self.assertSubstringsInString(substrings=subs, string=stdout.lower())

    def test_command_line_entry_no_file(self):
        # User invokes main.core with no arguments
        cmd = self.cmd_basic + " "

        # Program exits abruptly
        status = 1
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User informed of expected argument
        self.assertTrue(stdout)
        self.assertSubstringsInString(substrings=["usage"],
                                      string=stdout.lower())

    def test_command_line_entry_help(self):
        # User invokes main.core with help argument
        cmd = self.cmd_basic + " -h"

        # Program exits cleanly
        status = 0
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User provided helpful information
        self.assertTrue(stdout)
        self.assertSubstringsInString(substrings=["help"],
                                      string=stdout.lower())


if __name__ == '__main__':
    unittest.main()
