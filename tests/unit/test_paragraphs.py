#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of paragraph processing classes: PreProcessed and PostProcessed.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import ParagraphsTestCase

from helpers import paragraphs
import exceptions

from lxml import etree

import unittest
import itertools


class Test_PreProcessed(ParagraphsTestCase):

    def test_instantiation_good_arg_PARA(self):
        query = ("//w:p[(count(descendant::w:i) > 0) and "
                 "(count(descendant::w:t) > 0)]")
        find = self.input.xpaths.get(query)
        para = find(self.input.tree)[0]
        # Para with text and italic
        _ = paragraphs.PreProcessed(para)

    def test_instantiation_wrong_arg_PARA(self):
        expected_exception = exceptions.RecomposeError
        expected_substrings = "paragraph no italics text tags".split()
        # Xpath queries for various paras
        queries = {}
        queries["neither"] = ("//w:p[(count(descendant::w:i) = 0) and "
                              "(count(descendant::w:t) = 0)]")
        queries["no_italic"] = "//w:p[count(descendant::w:i) = 0]"
        queries["no_text"] = "//w:p[count(descendant::w:t) = 0]"
        # Para without text and italic
        for key, query in queries.items():
            with self.subTest(query=key):

                find = self.input.xpaths.get(query)
                para = find(self.input.tree)[0]

                with self.assertRaises(expected_exception) as fail:
                    _ = paragraphs.PreProcessed(para)
                self.assertSubstringsInString(expected_substrings,
                                              str(fail.exception))

    def test_instantiation_wrong_arg_OTHER(self):
        expected_exception = exceptions.RecomposeError
        expected_substrings = "element is not a paragraph w:p got".split()
        # Wrong element
        query = "//w:rPr"
        find = self.input.xpaths.get(query)
        para = find(self.input.tree)[0]
        expected_substrings.append(para.xpath("name()"))

        with self.assertRaises(expected_exception) as fail:
            _ = paragraphs.PreProcessed(para)
            self.assertSubstringsInString(expected_substrings,
                                          str(fail.exception))

    def test_has_attrs(self):
        iter_para = self.input.iter_paragraphs()
        para = next(iter_para)
        attrs = ["pre_italic", "italic", "post_italic", "xpaths"]

        pre = paragraphs.PreProcessed(para)
        for attr in attrs:
            with self.subTest(attr_name=attr):
                self.assertHasAttr(pre, attr)

    def test_xpath_attr_type(self):
        from helpers import xml
        iter_para = self.input.iter_paragraphs()
        para = next(iter_para)
        pre = paragraphs.PreProcessed(para)

        self.assertIsInstance(pre, xml.XPaths)

    def test_xpath_attr_identity(self):
        paras = itertools.islice(self.input.iter_paragraphs(), 2)
        pre0, pre1 = [paragraphs.PreProcessed(p) for p in paras]

        self.assertIsNot(pre0.xpaths, input.xpaths)
        self.assertIs(pre0.xpaths, pre1.xpaths)

    def test_xpaths_attr_shared_by_instances(self):
        iter_para = self.input.iter_paragraphs()
        pre0 = paragraphs.PreProcessed(next(iter_para))
        pre1 = paragraphs.PreProcessed(next(iter_para))
        some_query = "string()"  # May have been used by other test?
        # Precondition
        self.assertNotIn(some_query, pre0.xpaths)
        self.assertNotIn(some_query, pre1.xpaths)

        this_finder = pre0.get(some_query)
        self.assertIn(some_query, pre0.xpaths)
        self.assertIn(some_query, pre1.xpaths)

        other_finder = pre1.get(some_query)
        self.assertIs(this_finder, other_finder)

    @unittest.expectedFailure
    def test_attrs_substrings(self):
        iter_para = self.input.iter_paragraphs()
        para = next(iter_para)

        pre = paragraphs.PreProcessed(para)

        with self.subTest(attr_name="pre_italic"):
            self.assertIsInstance(pre.pre_italic, str)
            self.assertGreaterEqual(len(pre.pre_italic), 1)
            self.assertGreaterEqual(pre.pre_italic.count(","), 1)
            self.assertTrue(pre.pre_italic.endswith(","))
            self.assertEqual(len(pre.pre_italic), len(pre.pre_italic.strip()))

        with self.subTest(attr_name="post_italic"):
            self.assertIsInstance(pre.post_italic, str)
            self.assertGreaterEqual(len(pre.post_italic), 1)
            self.assertEqual(pre.post_italic.count("isbn"), 1)
            self.assertGreaterEqual(pre.post_italic.count("."), 4)
            self.assertTrue(pre.post_italic.endswith("."))
            self.assertEqual(len(pre.post_italic), len(pre.post_italic.strip()))

        with self.subTest(attr_name="italic"):
            self.assertIsInstance(pre.italic, str)
            self.assertGreaterEqual(len(pre.italic), 1)
            self.assertGreaterEqual(pre.italic.count("."), 1)
            self.assertTrue(pre.italic.endswith("."))
            self.assertEqual(len(pre.italic), len(pre.italic.strip()))

    @unittest.expectedFailure
    def test_str_dunder(self):
        text_file = self.text_filename
        with open(text_file) as handle:
            lines = handle.read().splitlines()
            lines = [l.strip() for l in lines if not l.isspace() if l]
        paras = list(self.input.iter_paragraphs())
        self.assertEqual(len(paras), len(lines))  # Precondition

        for i, (para, line) in enumerate(zip(paras, lines), start=1):
            with self.subTest(para_number=i):
                pre = paragraphs.PreProcessed(para)
                self.assertEqual(str(pre), line)

    @unittest.expectedFailure
    def test_method_passes_correct_italic_pattern(self):
        xml_func = self.italic_correct_sequence
        method = paragraphs.PreProcessed._a_particular_method
        method(xml_func())

    @unittest.expectedFailure
    def text_method_raises_incorrect_italic_patterns(self):
        funcs = [self.italic_interrupted_sequence_raises,
                 self.italic_interrupted_sequence_raises,
                 self.italic_inverted_sequence_raises,
                 self.italic_NO_PRE_sequence_raises,
                 self.italic_NO_POST_sequence_raises,
                 self.italic_NO_PRE_NO_POST_sequence_raises]
        funcs = {f: f.__name__ for f in funcs}
        method = paragraphs.PreProcessed._a_particular_method
        expected_exception = exceptions.ItalicPatternError
        expected_substrings = ["Expected", "paragraph", "starting", "have",
                               "one italic section", "two non-italic sections"]

        for xml_func, name in funcs.items():
            with self.subTest(xml_type=name):
                with self.assertRaises(expected_exception) as fail:
                    method(xml_func())
                errmsg = str(fail.exception)
                self.assertSubstringsInString(expected_substrings, errmsg)

    def italic_correct_sequence(self):
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text</w:t>
        </w:r></w:p>
        """
        root = etree.fromstring(xml_str)
        return root

    def italic_interrupted_sequence_raises(self):
        # XML deliberately has interrupte italic subsequence..
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Interupted Not Italic<w:t/>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>More Italic Text</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text</w:t>
        </w:r></w:p>
        """
        root = etree.fromstring(xml_str)
        return root

    def italic_inverted_sequence_raises(self):
        # XML deliberately has italic then no italic then italic again.
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Pre Text</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Italic Text</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Post Text</w:t>
        </w:r>
        """
        root = etree.fromstring(xml_str)
        return root

    def italic_NO_PRE_sequence_raises(self):
        # XML deliberately too short
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text</w:t>
        </w:r></w:p>
        """
        root = etree.fromstring(xml_str)
        return root

    def italic_NO_POST_sequence_raises(self):
        # XML deliberately too short
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text</w:t>
        </w:r></w:p>
        """
        root = etree.fromstring(xml_str)
        return root

    def italic_NO_PRE_NO_POST_sequence_raises(self):
        # XML deliberately too short
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text</w:t>
        </w:r></w:p>
        """
        root = etree.fromstring(xml_str)
        return root


if __name__ == '__main__':
    unittest.main()
