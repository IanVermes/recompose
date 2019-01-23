#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of main/helpers/xml.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase

from helpers import strformat

STRING_NUMBERED = "The input file is not an XML of the correct type. You need to generate a suitable XML using Microsoft Word. 1) Open the 'Books Received' DOCX file in Microsoft Word, 2) in the menubar go to 'File'> 'Save As...' to open as dialog window, 3) choose the 'FileFormat' called 'Word XML Document (.xml)' from the spinner at the bottom of the dialog-window, 4) choose a suitable location to save the file, 5) click 'Save'.\nNow run this program again with the new XMLfile."
STRING_BULLETED = "The input file is not an XML of the correct type. You need to generate a suitable XML using Microsoft Word. *) Open the 'Books Received' DOCX file in Microsoft Word, *) in the menubar go to 'File'> 'Save As...' to open as dialog window, *) choose the 'FileFormat' called 'Word XML Document (.xml)' from the spinner at the bottom of the dialog-window, *) choose a suitable location to save the file, *) click 'Save'.\nNow run this program again with the new XMLfile."


class Test_Format_String(BaseTestCase):

    def test_replace_bullets(self):
        string = STRING_BULLETED
        res = strformat.format_string(string, numbers=True, has_bullets=True, padding=False)
        self.assertEqual(STRING_NUMBERED, res)

    def test_replace_numbers(self):
        string = STRING_NUMBERED
        res = strformat.format_string(string, numbers=False, has_bullets=True, padding=False)
        self.assertEqual(STRING_BULLETED, res)

    def test_replace_numbers_with_numbers(self):
        string = STRING_NUMBERED
        res = strformat.format_string(string, has_bullets=True, padding=False)
        self.assertEqual(STRING_NUMBERED, res)
