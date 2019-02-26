#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Integration test of helper/xml classes

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import InputFileTestCase, BaseTestCase
from helpers import xml
from helpers import paragraphs

from lxml import etree

import unittest
from unittest.mock import patch
import os
import functools
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
            lines = [line.strip() for line in handle]
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

                para_string_lower = para_string.lower()
                text_lower = text.lower()
                percent = int(self.is_similar(para_string, text) * 100)
                percent_lower = int(self.is_similar(para_string_lower, text_lower) * 100)

                with self.subTest(case="mixed_case"):
                    self.assertGreaterEqual(percent, 99)
                with self.subTest(case="lower"):
                    self.assertGreaterEqual(percent_lower, 100,
                    msg=(f"\npreprocess: {repr(para_string_lower)}"
                         f"\ntext_file : {repr(text_lower)}"))

    def test_user_preprocessed_paragraphs_attributes_correspond_to_docx(self):
        input = self.input

        # User gets paragraphs: only consider first
        iter_paras = input.iter_paragraphs()
        first_para = next(iter_paras)

        # User gets preprocessed para
        prepara = paragraphs.PreProcessed(first_para)

        # User interacts with attributes
        docx_preitalic = "Adelman, Rachel E., ".strip()
        self.assertEqual(prepara.pre_italic, docx_preitalic)
        docx_italic = "The Female Ruse: Women's Deception and Divine Sanction in the Hebrew Bible. ".strip()
        self.assertEqual(prepara.italic, docx_italic)
        docx_postitalic = "Sheffield Phoenix Press, Sheffield, 2017. xv, 256 pp. £60.00. ISBN 978 1 91092 825 7.".strip()
        self.assertEqual(prepara.post_italic, docx_postitalic)


class Test_PostProcessor_Produces_Expected_Object(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        PreProcessed_config = {"pre_italic": "Berthelot, Katell, Michaël Langlois and Thierry Legrand,",
                               "italic": "La Bibliothèque de Qumran 3b: Torah Deutéronome et Pantateque dans son ensemble.",
                               "post_italic": "Les Éditions du Cerf, Paris, 2017. xxi, 730 pp. €75.00. ISBN 978 2 20411 147 8."
        }
        cls.mock_config = PreProcessed_config
        cls.patcher = patch("helpers.paragraphs.PreProcessed", autospec=True)
        cls.MockPreProcessed = cls.patcher.start()

        expected_attrs = {"authors": "authors editors",
                          "title": "title series",
                          "meta": ("illustrator translator "
                                   "publisher publplace year "
                                   "pages price isbn issn")}
        for attr_group, attr in expected_attrs.items():
            expected_attrs[attr_group] = attr.split()
        cls.expected_attrs = expected_attrs

        cls.pre = cls.MockPreProcessed("Some XML paragraph <w:p>")
        cls.pre.configure_mock(**cls.mock_config)

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_attr_group_AUTHORS_values(self):
        group = "authors"
        # Sideffect: set deliberatly consumed by test
        expected_attrs = set(self.expected_attrs[group])
        method = self.check_post_value_by_attr

        pre = self.pre
        post = paragraphs.PostProcessed(pre)
        check_value = functools.partial(method, post=post,
                                        precondition=expected_attrs)

        # GENERAL:
        # Check attr name is expected as a precondition, in case spec changes.
        # Value of attr == expected value of attr
        attr, exp_value = "authors", [("Katell", "Berthelot"),
                                      ("Michaël", "Langlois"),
                                      ("Thierry", "Legrand")]
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "editors", list()
        check_value(attr=attr, expected=exp_value)

        # Poscondition:
        self.assertEqual(len(expected_attrs), 0,
                         msg=("Postcondition: did not check all attrs - "
                              f"{expected_attrs}"))

    def test_attr_group_TITLE_values(self):
        group = "title"
        # Sideffect: set deliberatly consumed by test
        expected_attrs = set(self.expected_attrs[group])
        method = self.check_post_value_by_attr

        pre = self.pre
        post = paragraphs.PostProcessed(pre)
        check_value = functools.partial(method, post=post,
                                        precondition=expected_attrs)

        # GENERAL:
        # Check attr name is expected as a precondition, in case spec changes.
        # Value of attr == expected value of attr
        attr, exp_value = "title", ("La Bibliothèque de Qumran 3b: Torah "
                                    "Deutéronome et Pantateque dans son "
                                    "ensemble.")
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "series", ""
        check_value(attr=attr, expected=exp_value)

        # Poscondition:
        self.assertEqual(len(expected_attrs), 0,
                         msg=("Postcondition: did not check all attrs - "
                              f"{expected_attrs}"))

    def test_attr_group_META_values(self):
        group = "meta"
        # Sideffect: set deliberatly consumed by test
        expected_attrs = set(self.expected_attrs[group])
        method = self.check_post_value_by_attr

        pre = self.pre
        post = paragraphs.PostProcessed(pre)
        check_value = functools.partial(method, post=post,
                                        precondition=expected_attrs)

        # GENERAL:
        # Check attr name is expected as a precondition, in case spec changes.
        # Value of attr == expected value of attr
        attr, exp_value = "illustrator", ""
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "translator", ""
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "publisher", "Les Éditions du Cerf"
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "publplace", "Paris"
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "year", "2017"
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "pages", "xxi, 730 pp"
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "price", "€75.00"
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "isbn", "9782204111478"
        check_value(attr=attr, expected=exp_value)

        attr, exp_value = "issn", ""
        check_value(attr=attr, expected=exp_value)

        # Poscondition:
        self.assertEqual(len(expected_attrs), 0,
                         msg=("Postcondition: did not check all attrs - "
                              f"{expected_attrs}"))

    def check_post_value_by_attr(self, post, attr, expected, precondition=None):
        with self.subTest(attr=attr):
            if not precondition:
                msg = ("Preconditon should a be a set of attributes. This "
                       "set is empty. Maybe the attr was removed from the "
                       "set by an earlier call of check_post_value_by_attr "
                       f"or the set never included attr='{attr}'.")
                raise ValueError(msg)
            if attr not in precondition:
                assertmsg = (f"Precondition: {attr} is not in the setUpClass "
                             "expected attr specification for "
                             f"{post.__class__.__name__}.")
                self.fail(assertmsg)
            else:
                precondition.remove(attr)
            value = getattr(post, attr)
            self.assertEqual(value, expected)


if __name__ == '__main__':
    unittest.main()
