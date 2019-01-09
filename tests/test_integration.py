#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of core.py.

Copyright Ian Vermes 2018
"""

from tests.base_testcases import BaseTestCase
from main import core

import unittest

class UserStories_CommandLine(BaseTestCase):

    def test_command_line_entry_correct(self):
        # User invokes main.core with an XML file
        self.fail()
        # Program exits cleanly

        # Program yields output xml file in same directory as input

    def test_command_line_entry_bad_file(self):
        # User invokes main.core without an XML file
        self.fail()

        # Program exits abruptly

        # User informed of bad file in commandline

    def test_command_line_entry_no_file(self):
        # User invokes main.core with no arguments
        self.fail()

        # Program exits abruptly

        # User informed of expected argument

    def test_command_line_entry_help(self):
        # User invokes main.core with help argument
        self.fail()
        # Program exits cleanly

        # User provided helpful information


if __name__ == '__main__':
    unittest.main()
