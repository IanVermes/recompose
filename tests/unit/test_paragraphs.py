#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of paragraph processing classes: PreProcessed and PostProcessed.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import ParagraphsTestCase, BaseTestCase

import helpers.logging as pkg_logging
from helpers import paragraphs
import helpers.paragraphs  # for tagetted mocking
import exceptions

import testfixtures
from lxml import etree

from unittest.mock import patch
import random
import unittest
import functools
import itertools
import os


class Test_Processor_Classes(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        PreProcessed_config = {"pre_italic": "Berthelot, Katell, Michaël Langlois and Thierry Legrand,",
                               "italic": "La Bibliothèque de Qumran 3b: Torah Deutéronome et Pantateque dans son ensemble.",
                               "post_italic": "Les Éditions du Cerf, Paris, 2017. xxi, 730 pp. €75.00. ISBN 978 2 20411 147 8."
        }
        cls.mock_config = PreProcessed_config
        cls.patcher = patch("helpers.paragraphs.PreProcessed", autospec=True)
        cls.MockPreProcessed = cls.patcher.start()

        cls.processor_classes = {"Pre": paragraphs.ProcessorPreItalic,
                                 "Post": paragraphs.ProcessorPostItalic,
                                 "Italic": paragraphs.ProcessorItalic}

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_mocked_PreProcessed(self):
        pre = self.MockPreProcessed("Some XML paragraph <w:p>")
        pre.configure_mock(**self.mock_config)

        for i, attr in enumerate(("pre_italic", "post_italic", "italic")):
            with self.subTest(attr=attr):
                self.assertHasAttr(pre, attr)
                attr_value = getattr(pre, attr)
                dict_value = self.mock_config[attr]
                self.assertEqual(attr_value, dict_value)


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
        expected_substrings = "paragraph no italic text tags".split()
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
        expected_substrings = "element is not a paragraph w:p".split()
        # Wrong element
        query = "//w:rPr"
        find = self.input.xpaths.get(query)
        para = find(self.input.tree)[0]
        expected_substrings.append(para.xpath("name()"))

        with self.assertRaises(expected_exception) as fail:
            _ = paragraphs.PreProcessed(para)
        self.assertSubstringsInString(expected_substrings,
                                      str(fail.exception))

    def test_instantiation_wrong_arg_PATTERN(self):
        # While memoizing at a class level can be controlled with class methods,
        # the class is generally only going to be instanced by elements of the
        # #same nsmap. In our tests some w:p nodes have different uris: one set
        # by Microsoft in their DOCX derived XML and one by me for the XML
        # stubs. So for instancing when the source element has differing nsmaps,
        # we lobotomize! Its only for testing anyway, right!
        try:
            old_xpaths = paragraphs.PreProcessed._xpaths
            paragraphs.PreProcessed._xpaths = None
            self.assertIsNone(paragraphs.PreProcessed._xpaths, msg="Precondition!")

            expected_exception = exceptions.ParagraphItalicPatternWarning
            # Bad italic pattern
            para = self.italic_interrupted_sequence_raises()


            with self.assertRaises(expected_exception):
                _ = paragraphs.PreProcessed(para)
        finally:
            paragraphs.PreProcessed._xpaths = old_xpaths

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

        self.assertIsInstance(pre.xpaths, xml.XPaths)

    def test_xpath_attr_identity(self):
        paras = itertools.islice(self.input.iter_paragraphs(), 2)
        pre0, pre1, *_ = [paragraphs.PreProcessed(p) for p in paras]

        self.assertIsNot(pre0.xpaths, self.input.xpaths)
        self.assertIs(pre0.xpaths, pre1.xpaths)

    def test_xpaths_attr_shared_by_instances(self):
        iter_para = self.input.iter_paragraphs()
        pre0 = paragraphs.PreProcessed(next(iter_para))
        pre1 = paragraphs.PreProcessed(next(iter_para))
        some_query = "string()"  # May have been used by other test?
        # Precondition
        self.assertNotIn(some_query, pre0.xpaths)
        self.assertNotIn(some_query, pre1.xpaths)

        this_finder = pre0.xpaths.get(some_query)
        self.assertIn(some_query, pre0.xpaths)
        self.assertIn(some_query, pre1.xpaths)

        other_finder = pre1.xpaths.get(some_query)
        self.assertIs(this_finder, other_finder)

    # @unittest.expectedFailure
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
            self.assertEqual(pre.post_italic.lower().count("isbn"), 1,
                             msg=pre.post_italic)
            self.assertGreaterEqual(pre.post_italic.count("."), 4)
            self.assertTrue(pre.post_italic.endswith("."))
            self.assertEqual(len(pre.post_italic), len(pre.post_italic.strip()))

        with self.subTest(attr_name="italic"):
            self.assertIsInstance(pre.italic, str)
            self.assertGreaterEqual(len(pre.italic), 1)
            self.assertGreaterEqual(pre.italic.count("."), 1)
            self.assertTrue(pre.italic.endswith("."))
            self.assertEqual(len(pre.italic), len(pre.italic.strip()))

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
                pre_str = str(pre)
                with self.subTest(property="length"):
                    self.assertEqual(len(pre_str), len(line))
                with self.subTest(property="case_insensitive"):
                    self.assertEqual(pre_str.lower(), line.lower())

    def test_generate_italic_pattern(self):
        data = {(False, True, False): self.italic_correct_sequence,
                (False, True, False, True, False): self.italic_interrupted_sequence_raises
        }
        method = paragraphs.PreProcessed._get_italic_pattern
        for expected, xmlfunc in data.items():
            with self.subTest(pattern=xmlfunc.__name__):
                result = method(xmlfunc(), _memoize=False)
                self.assertEqual(result, expected)

    def test_validate_method_passes_correct_italic_pattern(self):
        funcs = [self.italic_correct_sequence,
                 self.italic_correct_sequence_with_small_caps,
                 self.italic_correct_sequence_longer]
        method = paragraphs.PreProcessed._is_valid_italic_pattern
        funcs = {f: f.__name__ for f in funcs}

        for xml_func, name in funcs.items():
            with self.subTest(xml_type=name):

                flag = method(xml_func(), _memoize=False)

                self.assertTrue(flag)

    def test_validate_method_fails_incorrect_italic_patterns(self):
        funcs = [self.italic_interrupted_sequence_raises,
                 self.italic_interrupted_sequence_longer_raises,
                 self.italic_inverted_sequence_raises,
                 self.italic_NO_PRE_sequence_raises,
                 self.italic_NO_POST_sequence_raises,
                 self.italic_NO_PRE_NO_POST_sequence_raises]
        funcs = {f: f.__name__ for f in funcs}
        method = paragraphs.PreProcessed._is_valid_italic_pattern
        expected_exception = exceptions.ParagraphItalicPatternWarning
        expected_substrings = ["paragraph", "has", "pattern",
                               "Found", "one italic section",
                               "two non-italic sections"]

        for xml_func, name in funcs.items():
            xml = xml_func()
            with self.subTest(xml_type=name, fatal=True):
                with self.assertRaises(expected_exception) as fail:
                    method(xml, fatal=True, _memoize=False)
                errmsg = str(fail.exception)
                self.assertSubstringsInString(expected_substrings, errmsg)

            with self.subTest(xml_type=name, fatal=False):
                flag = method(xml, fatal=False, _memoize=False)
                self.assertFalse(flag)

    def test_validate_method_raises_exception_with_detail(self):
        funcs = [self.italic_inverted_sequence_raises,
                 self.italic_interrupted_sequence_longer_raises]
        funcs = {f: f.__name__ for f in funcs}
        expected_detail = "italic, non-italic, italic"
        method = paragraphs.PreProcessed._is_valid_italic_pattern
        expected_exception = exceptions.ParagraphItalicPatternWarning

        for xml_func, name in funcs.items():
            xml = xml_func()
            with self.subTest(xml_type=name, fatal=True):
                with self.assertRaises(expected_exception) as fail:
                    method(xml, fatal=True, _memoize=False)

                self.assertIn(expected_detail, str(fail.exception))

    def test_validate_method_exception_detail_includes_offending_text(self):
        funcs = [self.italic_correct_sequence_longer,
                 self.italic_interrupted_sequence_longer_raises]
        expected = [((False, 'Pre Text 1Pre Text 2Pre Text 3'),
                    (True, 'Italic Text 1Italic Text 2'),
                    (False, 'Post Text 1Post Text 2Post Text 3')),
                    # func1 result
                   ((False, 'Pre Text 1Pre Text 2Pre Text 3'),
                    (True, 'First Italic Text 1First Italic Text 2'),
                    (False, 'Interupted Not Italic 1Interupted Not Italic 2'),
                    (True, 'Second Italic Text 1Second Italic Text 2Second Italic Text 3'),
                    (False, 'Post Text 1Post Text 2'))
                    # func2 result
                    ]
        details = [tuple((f"italic: {s}" for b, s in t if b)) for t in expected]
        funcs = {f: (f.__name__, exp, d) for f, exp, d in zip(funcs, expected, details)}
        method_grouper = paragraphs.PreProcessed._group_italic_substrings
        method_is_valid = paragraphs.PreProcessed._is_valid_italic_pattern
        expected_exception = exceptions.ParagraphItalicPatternWarning

        for xml_func, (name, expect_res, detail) in funcs.items():
            xml = xml_func()
            with self.subTest(xml_type=name, fatal=True):
                actual_res = method_grouper(xml)

                # Test1 : Verify grouping works.
                self.check_grouped_italic_strings(actual_res, expect_res)

                # Test2 : Verify exceptions raised better detail.
                try:
                    method_is_valid(xml, fatal=True, _memoize=False)
                except expected_exception as err:
                    error = str(err)
                else:
                    error = ""
                if error:
                    msg = f"{name} should not have raised an exception!"
                    self.assertIn("raise", name, msg=msg")
                    self.assertSubstringsInString(detail, error)
                else:
                    msg = f"{name} should not have passed!"
                    self.assertIn("correct", name, msg=msg)


    def check_grouped_italic_strings(self, actual_res, expect_res):
        self.assertEqual(len(actual_res), len(expect_res), msg="Postcondition")
        for pair in zip(actual_res, expect_res):
            actual_tup, expect_tup = pair
            self.assertTupleEqual(actual_tup, expect_tup)

    def test_identify_substrings_method(self):
        xml = self.italic_correct_sequence()
        get_text = etree.XPath("//w:t/text()", namespaces=xml.nsmap)
        exp_pre, exp_ital, exp_post = get_text(xml)
        method = paragraphs.PreProcessed._identify_substrings

        res_pre, res_ital, res_post = method(xml, _memoize=False)

        with self.subTest(section="pre"):
            self.assertEqual(exp_pre, res_pre)
        with self.subTest(section="italic"):
            self.assertEqual(exp_ital, res_ital)
        with self.subTest(section="post"):
            self.assertEqual(exp_post, res_post)

    def test_identify_substrings_method_interprets_smallCaps_tag(self):
        xml = self.italic_correct_sequence_with_small_caps()
        get_text = etree.XPath("//w:t/text()", namespaces=xml.nsmap)
        *_, exp_post = get_text(xml)
        method = paragraphs.PreProcessed._identify_substrings
        self.assertFalse(exp_post.isupper(), msg="Precondition")

        *_, res_post = method(xml, _memoize=False)

        self.assertTrue(res_post.isupper())
        self.assertEqual(exp_post.upper(), res_post)

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

    def italic_correct_sequence_longer(self):
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text 2</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text 3</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Italic Text 2</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text 2</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text 3</w:t>
        </w:r></w:p>
        """
        root = etree.fromstring(xml_str)
        return root

    def italic_correct_sequence_with_small_caps(self):
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
            <w:rPr><w:smallCaps/></w:rPr>
            <w:t>isbn</w:t>
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
            <w:t>Interupted Not Italic</w:t>
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

    def italic_interrupted_sequence_longer_raises(self):
        xml_str = """<w:p xmlns:w="http://google.com">
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text 2</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Pre Text 3</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>First Italic Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>First Italic Text 2</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Interupted Not Italic 1</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Interupted Not Italic 2</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Second Italic Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Second Italic Text 2</w:t>
        </w:r>
        <w:r>
            <w:rPr><w:i/></w:rPr>
            <w:t>Second Italic Text 3</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text 1</w:t>
        </w:r>
        <w:r>
            <w:rPr></w:rPr>
            <w:t>Post Text 2</w:t>
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
        </w:r></w:p>
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


class Test_Paragraph_ShorteningFunc(ParagraphsTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        paras_xml = list(cls.input.iter_paragraphs())[:5]
        paras_preproc = list(map(helpers.paragraphs.PreProcessed, paras_xml))
        cls.args = ["Lorem ipsum dolor sit amet, consectetur adipisicing elit"]
        cls.args.extend(paras_xml)
        cls.args.extend(paras_preproc)

    def test_func_with_different_args(self):
        length = 30
        func = helpers.paragraphs.get_paragraph_head
        for arg in self.args:

            with self.subTest(type=type(arg)):
                result = func(arg, length)
                self.assertIsInstance(result, str)

    def test_func_shortens_string(self):
        desired_length = 30
        func = helpers.paragraphs.get_paragraph_head

        for arg in self.args:

            with self.subTest(type=type(arg)):
                result = func(arg, desired_length)

                self.assertLengthInRange(result,
                                         min=1,
                                         max=desired_length)

    def test_func_kwargs_bullet(self):
        func = helpers.paragraphs.get_paragraph_head
        desired_length = 30
        expected_bullet_star = "* )"
        expected_bullet_number = "{i:02d})"
        for i, arg in enumerate(self.args):

            with self.subTest(type=type(arg), bullet="*"):
                result = func(arg, desired_length, bullet=True)
                self.assertIn(expected_bullet_star, result)

            with self.subTest(type=type(arg), bullet="int"):
                result = func(arg, desired_length, bullet_num=i)

                self.assertIn(str(i), result)
                self.assertIn(expected_bullet_number.format(i=i), result)

    def test_adds_ellipsis(self):
        desired_length = 30
        string = ("Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
                  "sed do eiusmod tempor incididunt")
        ellipsis = "..."
        func = helpers.paragraphs.get_paragraph_head
        self.assertGreater(len(string), desired_length, msg="Precondition")

        result = func(string, desired_length)

        self.assertIn(ellipsis, result)
        self.assertTrue(result.endswith(ellipsis))

    def test_func_wrapped_as_partial(self):
        desired_length = 30
        bullet_number = 7
        expected_bullet = f"{bullet_number:02d})"
        ellipsis = "..."
        string = ("Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
                  "sed do eiusmod tempor incididunt")
        self.assertGreater(len(string), desired_length, msg="Precondition")

        func = helpers.paragraphs.get_paragraph_head
        curried_func = functools.partial(func, string, desired_length,
                                         bullet_num=bullet_number)
        # Curried is callable?
        try:
            result = curried_func()
        except TypeError as err:
            error = err
        else:
            error = None

        # Curried result is as expected
        self.assertIsNone(error)
        self.assertIsInstance(result, str)
        self.assertLengthInRange(result, min=1, max=desired_length)
        self.assertTrue(result.startswith(expected_bullet))
        self.assertTrue(result.endswith(ellipsis))


@patch("helpers.paragraphs.PreProcessed.is_valid_italic_pattern")
class Test_ProcessParagraphs_Function(ParagraphsTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.preprocess_exc = exceptions.ParagraphItalicPatternWarning
        cls.iter_paragraphs = list(cls.input.iter_paragraphs())
        cls.default_log_filename = pkg_logging.default_log_filename()
        cls.error_mock_detail = "*** mocked detail ***".upper()

    def tearDown(self):
        pkg_logging.finish_logging()
        if os.path.exists(self.default_log_filename):
            os.remove(self.default_log_filename)

    def random_fail(self, *args, **kwargs):
        fatal = kwargs["fatal"]
        choice = random.choice([True, False])
        return self._failing_func(choice, fatal)

    def must_fail(self, *args, **kwargs):
        fatal = kwargs["fatal"]
        choice = False
        return self._failing_func(choice, fatal)

    def _failing_func(self, choice, fatal):
        if choice:
            return choice
        else:
            if fatal:
                detail = self.error_mock_detail
                raise self.preprocess_exc(detail=detail)
            else:
                return choice

    def test_mocked_PreProcessed_mock_sideffect1(self, mock_preprocessed_method=None):
        mock_preprocessed_method.side_effect = self.random_fail
        para_elements = self.iter_paragraphs

        count = 0
        exceptions = []
        for para_elem in para_elements:
            try:
                helpers.paragraphs.PreProcessed(para_elem)
            except self.preprocess_exc:
                count += 1
            except Exception as err:
                exceptions.append(err.__class__.__name__)
            else:
                count += 1
        self.assertFalse(len(exceptions), msg=", ".join(set(exceptions)))
        self.assertEqual(len(para_elements), count)

    def test_mocked_PreProcessed_mock_sideffect2(self, mock_preprocessed_method=None):
        mock_preprocessed_method.side_effect = self.must_fail
        para_elements = self.iter_paragraphs

        err_count = 0
        success_count = 0
        exceptions = []
        for para_elem in para_elements:
            try:
                helpers.paragraphs.PreProcessed(para_elem)
            except self.preprocess_exc:
                err_count += 1
            except Exception as err:
                exceptions.append(err.__class__.__name__)
            else:
                success_count += 1
        self.assertFalse(len(exceptions), msg=", ".join(set(exceptions)))
        self.assertEqual(err_count, len(para_elements))
        self.assertEqual(success_count, 0)

    def test_process_paragraphs_handles_warnings(self, mock_preprocessed_method):
            mock_preprocessed_method.side_effect = self.must_fail
            para_elements = self.iter_paragraphs
            handled_exceptions = (exceptions.RecomposeWarning, )
            pkg_logging.setup_logging()

            isHandled = False
            hasUnexpectedError = None

            try:

                helpers.paragraphs.process_paragraphs(para_elements)
            except handled_exceptions:
                isHandled = False
            except Exception as err:
                isHandled = False
                hasUnexpectedError = err
            else:
                isHandled = True

            self.assertIsNone(hasUnexpectedError)
            self.assertTrue(isHandled,
                            msg=(f"Exception of type {handled_exceptions} "
                                 "should have been handled."))

    def test_process_paragraphs_logs(self, mock_preprocessed_method):
        mock_preprocessed_method.side_effect = self.must_fail
        para_elements = self.iter_paragraphs
        pkg_logging.setup_logging()

        with self.subTest(logging="in general"):
            pkg_logger = pkg_logging.getLogger()
            with self.assertLogs(logger=pkg_logger.logger):
                helpers.paragraphs.process_paragraphs(para_elements)

        with self.subTest(logging="quantative"):
            # Capture logging to stream and file
            with testfixtures.OutputCapture() as stream:
                helpers.paragraphs.process_paragraphs(para_elements)
            stream_contents = stream.captured.strip()
            with open(self.default_log_filename) as handle:
                logfile_contents = handle.read().splitlines()

            # Test logging to stdout/stderr: expect nothing
            self.assertEqual(stream_contents, "")
            # Test logging to logfile: expect n warning lines
            filtered_contents = [l for l in logfile_contents if "WARNING" in l]
            self.assertLengthInRange(filtered_contents,
                                     min=len(para_elements),
                                     max=len(para_elements) + 1)
            # Test logging to logfile: expect things - prelog + warning
            self.assertLengthInRange(logfile_contents,
                                     min=len(para_elements) * 2,
                                     max=len(para_elements) * 2 + 1)

    def test_process_paragraphs_log_messages_as_expected(self, mock_preprocessed_method):
        mock_preprocessed_method.side_effect = self.must_fail
        para_elems_zerothonly = list(itertools.islice(self.iter_paragraphs, 1))
        para = para_elems_zerothonly[0]

        helpers.paragraphs.process_paragraphs(para_elems_zerothonly)

        with open(self.default_log_filename) as handle:
            logfile_contents = handle.read().splitlines()

        self.assertLengthInRange(logfile_contents, min=2, max=2)
        line_0, line_1 = logfile_contents
        with self.subTest(line="prelog line"):
            level = "INFO"
            max_length = 30
            raw_detail = para.xpath("string()")[:max_length]
            func = helpers.paragraphs.get_paragraph_head
            expected_detail = func(para, max_length, bullet_num=1)
            expected = [expected_detail, level]

            self.assertSubstringsInString(expected, line_0,
                                          msg=f"line='{line_0}'")
            self.assertStringsSimilar(raw_detail, expected_detail, 0.5)
            line_0_substring = line_0.split(level)[1]
            self.assertStringsSimilar(raw_detail, line_0_substring, 0.3)
        with self.subTest(line="error line"):
            level = "WARNING"
            expected = [self.error_mock_detail, level, "italic"]
            self.assertSubstringsInString(expected, line_1,
                                            msg=f"line='{line_1}'")


if __name__ == '__main__':
    unittest.main()
