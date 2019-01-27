#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Integration test of helper/xml classes

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import InputFileTestCase
from helpers import xml

from lxml import etree

import unittest
import os
from difflib import SequenceMatcher


class Test_Paragraph_Selection(InputFileTestCase):

    @staticmethod
    def is_similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = "BR Autumn 2018"
        comparison_text_filename = f"resources/{base} UTF8.txt"
        if not os.path.isfile(comparison_text_filename):
            raise FileNotFoundError(comparison_text_filename)
        assert base in os.path.basename(cls.good_input), "xml and txt mismatch!"

        with open(comparison_text_filename) as handle:
            lines = [line.strip("\n") for line in handle]
            no_empty = [l for l in lines if not (l and l.isspace())]
        cls.txt_lines = lines
        cls.txt_lines_no_empty = no_empty

        cls.input = xml.XMLAsInput()
        cls.input.isSuitable(cls.good_input, fatal=True)

    def test_user_gets_all_paragraphs(self):
        input = self.input

        # User gets all paragraphs
        paras = list(input.iter_paragraphs(force_all=True))

        # User gets the same number of paras as lines in the txt file.
        self.assertEqual(len(paras), len(self.txt_lines))

    def test_user_gets_appropriate_paragraphs(self):
        input = self.input

        # User gets paragraphs, appropriate by default and not all.
        wrong_paras = list(input.iter_paragraphs(force_all=True))
        paras = list(input.iter_paragraphs())
        self.assertNotEqual(wrong_paras, paras)

        # User gets a reasonable number of paras
        lowerbound, upperbound = len(self.txt_lines_no_empty), len(wrong_paras)
        self.assertTrue(lowerbound <= len(paras) < upperbound)

        # Check paras have italic and text get_args
        has_text = etree.XPath("descendant::w/t", namespaces=input.nsmap)
        has_italic = etree.XPath("descendant::w/i", namespaces=input.nsmap)
        get_string = etree.XPath("string()")

        for i, para in enumerate(paras):
            with self.subTest(paras_index=i):
                self.assertTrue(has_text(para))  # text tags
                self.assertTrue(has_italic(para))  # italic tags
            with self.subTest(paras_index=i):
                # paras are 'line for line'
                xml_string = get_string(para)
                txt_file_string = self.txt_lines_no_empty[i]
                ratio = self.is_similar(xml_string, txt_file_string)
                self.assertGreater(ratio, 0.75)



if __name__ == '__main__':
    unittest.main()
