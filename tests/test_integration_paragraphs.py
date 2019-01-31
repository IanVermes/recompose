#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Integration test of helper/xml classes

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import InputFileTestCase
from helpers import xml
from helpers import paragraphs

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
            no_empty = [l for l in lines if (l and not l.isspace())]
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
        self.assertTrue(lowerbound <= len(paras) < upperbound,
                        msg=f"{lowerbound} <= {len(paras)} < {upperbound}")

        # Check paras have italic and text get_args
        has_text = etree.XPath("descendant::w:t", namespaces=input.nsmap)
        has_italic = etree.XPath("descendant::w:i", namespaces=input.nsmap)
        get_string = etree.XPath("string()")

        for i, para in enumerate(paras):
            with self.subTest(paras_index=i):
                self.assertTrue(len(has_text(para)))
                self.assertTrue(len(has_italic(para)))
            with self.subTest(paras_index=i):
                # paras are 'line for line'
                xml_string = get_string(para)
                txt_file_string = self.txt_lines_no_empty[i]
                ratio = self.is_similar(xml_string, txt_file_string)
                self.assertGreater(ratio, 0.95)

    def test_user_generates_preprocessed_paragraphs_with_input(self):
        input = self.input

        # User gets paragraphs, appropriate by default and not all.
        iter_paras = input.iter_paragraphs()
        for i, (para, text) in enumerate(zip(iter_paras, self.txt_lines)):

            # User creates PreProcessed objects
            prepara = paragraphs.PreProcessed(para)

            # User is confident Prepara is similar in content to para
            with self.subTest(para_index=i):
                para_string = str(prepara)
                percent = int(self.is_similar(para_string, text) * 100)
                self.assertGreaterEqual(percent, 99)

    def test_user_preprocessed_paragraphs_attributes_correspond_to_docx(self):
        input = self.input

        # User gets paragraphs: only consider first
        iter_paras = input.iter_paragraphs()
        first_para = next(iter_paras)

        # User gets preprocessed para
        prepara = paragraphs.PreProcessed(first_para)

        # User interacts with attributes
        docx_preitalic = "Adelman, Rachel E., "
        self.assertEqual(prepara.pre, docx_preitalic)
        docx_italic = "The Female Ruse: Women's Deception and Divine Sanction in the Hebrew Bible. "
        self.assertEqual(prepara.italic, docx_italic)
        docx_postitalic = "Sheffield Phoenix Press, Sheffield, 2017. xv, 256 pp. £60.00. ISBN 978 1 91092 825 7."
        self.assertEqual(prepara.post, docx_postitalic)


if __name__ == '__main__':
    unittest.main()
