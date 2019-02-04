#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Integration test of core.py.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import CommandLineTestCase
from main import core

from lxml import etree

import unittest
import os


class UserStories_CommandLine(CommandLineTestCase):

    @classmethod
    def setUpClass(cls):
        # Get input files
        absolute = os.path.abspath
        exists = os.path.isfile
        cls.good_file = absolute("./resources/BR Autumn 2018.xml")
        cls.bad_file = absolute("./resources/BR Autumn 2018.docx")
        cls.decoy_file = absolute("./resources/invlaid_input.xml")
        cls.almost_good_file = absolute("./resources/BR Spring 2019 Track Changes.xml")
        files = (cls.good_file, cls.bad_file, cls.decoy_file, cls.almost_good_file)
        assert all([exists(f) for f in files]), {f: exists(f) for f in files}

        # Get default output filename
        argparser = core.RecomposeArgParser()
        cls.default_output_filename = argparser.default_output()
        assert not os.path.exists(cls.default_output_filename)

        # Get default log filename
        cls.default_log_filename = argparser.default_log()
        assert not os.path.exists(cls.default_output_filename)

        # Format commandline cmd
        cmd_basic_template = "python {filename_script}"
        core_py = absolute(core.__file__)
        cls.cmd_basic = cls.format_cmd(cmd_basic_template,
                                       {"filename_script": core_py})
        assert "filename_script" not in cls.cmd_basic

        # Schema XSD file
        schema_filename = "/Users/Ian/Google Drive/code/next_gen_xml/recompose/resources/jjs_schema_1.1.xsd"
        assert os.path.isfile(schema_filename)
        cls.schema = etree.XMLSchema(etree.parse(schema_filename))

    @property
    def output_file(self):
        return self._output_file

    @output_file.setter
    def output_file(self, value):
        if not value:
            value = self.default_output_filename
        self._output_file = value
        try:
            self._output_file_list.append(value)
        except AttributeError:
            self._output_file_list = [value]

    @property
    def log_file(self):
        return self._log_file

    @log_file.setter
    def log_file(self, value):
        if not value:
            value = self.default_log_filename
        self._log_file = value
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
            self.log_file = ""

    def setUp(self):
        # This variable is not local to test methods so that the tearDown
        # method can catch the filename when out of test scope. The setUp
        # method resets the value between tests as a precaution.
        self.output_file = ""
        self.log_file = ""

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
        cmd = self.user_story_generates_cmd()
        # Program exits cleanly
        status = self.user_story_program_runs_from_good_cmd(cmd, user_out=False)
        # outputfile validation
        self.fail("Fails at output analysis - remove this self.fail block at "
                  "a later point.")
        self.user_story_after_successful_execution(status)

    def test_command_line_entry_correct_with_output_argument(self):

        # A user chooses a filename for the output file
        for output_filename in self.user_specified_output_files():
            with self.subTest(filename=output_filename):
                # User story continues within definition
                cmd = self.user_story_generates_cmd(output_file=output_filename)
                status = self.user_story_program_runs_from_good_cmd(cmd, user_out=True)
                self.fail("Fails at output analysis - remove this self.fail "
                          "block at a later point.")
                self.user_story_after_successful_execution(status)

    @unittest.expectedFailure
    def test_command_line_entry_correct_with_output_argument_and_default_logging(self):
        self.fail("not written")

    @unittest.expectedFailure
    def test_command_line_entry_correct_with_output_argument_and_output_logging(self):
        self.fail("not written")

    def test_command_line_entry_bad_file(self):

        def user_story(self, input_filename):
            # User invokes main.core without an XML file
            cmd_template = self.cmd_basic + " {file_argument}"
            substring = {"file_argument": input_filename}
            cmd = self.format_cmd(cmd_template, substring)

            # Program exits cleanly but with helpful information printed.
            status = 0
            stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

            # No output file is made
            self.output_file = self.default_output_filename
            self.assertFileNotInDirectory(file=self.output_file, directory=os.getcwd())

            # User informed of bad file in commandline
            self.assertTrue(stdout)
            subs = ["input", "suitable", "error", "microsoft word",
                    "save as...", "xml"]
            self.assertSubstringsInString(substrings=subs,
                                          string=stdout.lower(),
                                          msg=(" the recorded stdout is as "
                                               f"follows\n\"{stdout}\""))

        # A DOCX and unsuitable XML file are selected by the user
        user_defined_input_files = [self.bad_file, self.decoy_file, self.almost_good_file]
        for input_filename in user_defined_input_files:

            with self.subTest(infile=input_filename):
                # User story continues within definition
                user_story(self, input_filename)

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

    # USER STORIES: sub-stories
    # USER STORIES: sub-stories
    # USER STORIES: sub-stories

    def user_story_generates_cmd(self, output_file=None, log_file=None):
        # User invokes main.core with an XML file and specified output
        templates = {
            False: self.cmd_basic + " {file_argument}",
            True: self.cmd_basic + " {file_argument}" + " {file_output}"
        }
        cmd_template = templates[bool(output_file)]
        if log_file:
            cmd_template += " {log_output}"
        ## Set instance attributes for tearDown, default file getting
        ## and for use in follow-on userstories
        self.output_file = output_file
        self.log_file = log_file
        substrings = {"file_argument": self.good_file,
                      "file_output": self.output_file,
                      "file_log": self.log_file}
        cmd = self.format_cmd(cmd_template, substrings, ignore_precond1=True)
        return cmd

    def user_specified_output_files(self, basename=None):
        expanduser = os.path.expanduser
        abspath = os.path.abspath
        if basename is None:
            basename = "custom_output.xml"
        user_specified_filenames = [expanduser(f"~/Desktop/{basename}"),
                                    "foo" + basename,
                                    abspath(basename)]
        for filename in user_specified_filenames:
            yield filename

    def user_story_program_runs_from_good_cmd(self, cmd, user_out=False, user_log=False):
        # Program exits cleanly
        status = 0
        stdout = self.invoke_cmd_via_commandline(cmd, expected_status=status)

        # User sees nothing in stdout, all assumed to go well
        if not user_log:
            self.assertFalse(stdout)

        # User included the output destination in cmd
        if user_out:
            # Program set user defined output rather than adopting the default
            self.assertNotEqual(self.default_output_filename, self.output_file)
            # Program yields output file at location specified
            self.assertFileInDirectory(file=self.output_file,
                                       directory=os.path.dirname(self.output_file))
            # Program does not name the output file with the default value
            self.assertFileNotInDirectory(file=self.default_output_filename,
                                          directory=os.getcwd())
        # User omitted the output destination in cmd
        elif not user_out:
            # Program has set the output name as the default value.
            self.assertEqual(self.default_output_filename, self.output_file)
            # Program yields default output file at cwd.
            self.assertFileInDirectory(file=self.default_output_filename,
                                       directory=os.getcwd())

        if user_log:
            pass  # TODO - logging options
        elif not user_log:
            pass  # TODO - logging options
        return status

    @unittest.expectedFailure
    def user_story_after_successful_execution(self, status):
        # Program exited cleanly
        self.assertEqual(0, status)

        # Output file was written
        self.assertTrue(os.path.isfile(self.output_file))

        # Output file is XML and the XML satisfies an XSD schema
        schema = self.schema
        try:
            parsed_xml = etree.parse(self.output_file)
        except etree.XMLSyntaxError as err:
            detail = str(err).splitlines()[0]
            errmsg = f"Could not parse file: {detail}"
        else:
            errmsg = ""
        if errmsg:
            self.fail(errmsg)
        self.assertTrue(schema.validate(parsed_xml))


if __name__ == '__main__':
    unittest.main()
