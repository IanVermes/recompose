#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of main/helpers/strformat.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import UnicodeItalicTestCase

import helpers.strformat
import unicodedata
import re
from functools import partial

class Test_Italic_Func(UnicodeItalicTestCase):

    def test_changes_font(self):
        func = helpers.strformat.makeItalic
        result = func(self.only_ascii)
        self.assertEqual(len(self.only_ascii), len(result), msg="Postcondition")
        expected = "<font>"

        for char in result:
            details = unicodedata.decomposition(char)
            cat = unicodedata.category(char)
            self.assertIn(expected, details)
            self.assertIn(cat, self.ascii_cat)
            self.assertTrue(char.isprintable(), msg=repr(char))

    def test_italic_characters_correspond_to_primitives(self):
        func = helpers.strformat.makeItalic
        result = func(self.only_ascii)
        decompose = unicodedata.decomposition
        hex2int = partial(int, base=16)

        self.assertEqual(len(self.only_ascii), len(result), msg="Postcondition")
        for char_o, char_res in zip(self.only_ascii, result):
            primitive_value = self.rgx_hex_code.search(decompose(char_res))
            primitive_value = primitive_value.group(1)
            primitive_value = hex2int(primitive_value)
            original_value = ord(char_o)
            with self.subTest(map=f"{char_o} <-> {char_res}"):
                self.assertEqual(primitive_value, original_value)

    def test_accented_characters_replaced_by_fill_when_unavailable(self):
        func = helpers.strformat.makeItalic
        chars = "å Ë ü".split()

        for char in chars:
            with self.subTest(char=char):
                new_char = func(char)
                self.assertEqual(new_char, helpers.strformat.FILL_CHR)
                self.assertTrue(new_char.isprintable())

    def test_punctuation_characters_preserved(self):
            func = helpers.strformat.makeItalic
            chars = "; . : ' & ^ * ( ) ? ! \" / \\".split()

            for char in chars:
                with self.subTest(char=char):
                    new_char = func(char)
                    self.assertNotEqual(new_char, helpers.strformat.FILL_CHR)
                    self.assertEqual(new_char, char)
                    self.assertTrue(new_char.isprintable())

    def test_numbers_preserved(self):
            func = helpers.strformat.makeItalic
            chars = [str(i) for i in range(10)]

            for char in chars:
                with self.subTest(char=char):
                    new_char = func(char)
                    self.assertNotEqual(new_char, helpers.strformat.FILL_CHR)
                    self.assertEqual(new_char, char)
                    self.assertTrue(new_char.isprintable())

    def test_whitespace_characters_substituted_with_viisble_alternatives(self):
        func = helpers.strformat.makeItalic
        chars = " ", "\n", "\t"
        mapping = helpers.strformat.WHITESPACE_CHR_MAP

        for char in chars:
            with self.subTest(char=char):
                new_char = func(char)
                self.assertNotEqual(new_char, helpers.strformat.FILL_CHR)
                self.assertNotEqual(new_char, char)
                self.assertEqual(mapping[char], new_char)
                self.assertTrue(new_char.isprintable())

class Test_Italic_Mapping(UnicodeItalicTestCase):

    def test_global_for_font_A_points(self):
        a_points = helpers.strformat._FONT_A_POINTS
        expected = "CAPITAL A"
        for font, ord_A in a_points:
            with self.subTest(font=font):
                italic_A = chr(ord_A)
                self.assertTrue(italic_A.isprintable())

                name = unicodedata.name(italic_A)
                self.assertIn(font, name)
                self.assertIn(expected, name)

    def test_func_that_creates_mapping(self):
        a_points = helpers.strformat._FONT_A_POINTS
        func = helpers.strformat._get_italic_mapping

        for font, ord_A in a_points:
            with self.subTest(font=font):

                try:
                    mapping = func(ord_A)
                except RuntimeError:
                    continue

                self.assertSetEqual(set(self.only_ascii), set(mapping))
                for chr_ascii, chr_italic in mapping.items():
                    details = unicodedata.decomposition(chr_italic)
                    hex_code = self.rgx_hex_code.search(details).group(1)
                    ord_italic = int(hex_code, base=16)
                    self.assertEqual(ord_italic, ord(chr_ascii))

    def test_func_that_gets_available_mapping(self):
        func = helpers.strformat._get_best_italic_mapping

        mapping = func()

        self.assertEqual(len(mapping), self.expected_length)
        for ascii_chr, italic_chr in mapping.items():
            with self.subTest(mapping=f"{ascii_chr} --> {italic_chr}"):
                self.assertIsInstance(italic_chr, str)
                self.assertEqual(len(italic_chr), 1)


if __name__ == '__main__':
    unittest.main()
