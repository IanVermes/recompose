#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of paragraph processing classes: PreProcessed and PostProcessed
as well as Processor subclasses.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import ParagraphsTestCase, BaseTestCase, ProcessorTestCase_Genuine
from tests.special_testcases import ProcessorTestCase_Abstract

import helpers.logging as pkg_logging
from helpers import paragraphs
import helpers.paragraphs  # for tagetted mocking
import exceptions

import testfixtures
from lxml import etree

from unittest.mock import patch, MagicMock
from collections import defaultdict
import random
import unittest
import functools
import itertools
import os

PREPROCESSED_CONFIG = {
    "pre_italic": "Berthelot, Katell, Michaël Langlois and Thierry Legrand,",
    "italic": ("La Bibliothèque de Qumran 3b: Torah Deutéronome et "
               "Pantateque dans son ensemble."),
    "post_italic": ("Les Éditions du Cerf, Paris, 2017. xxi, 730 pp. €75.00. "
                    "ISBN 978 2 20411 147 8.")
}


class Test_Processor_Classes(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_config = PREPROCESSED_CONFIG
        cls.patcher = patch("helpers.paragraphs.PreProcessed", autospec=True)
        cls.MockPreProcessed = cls.patcher.start()

        cls.processor_classes = {"authors": paragraphs.ProcessorAuthors,
                                 "title": paragraphs.ProcessorTitle,
                                 "meta": paragraphs.ProcessorMeta}

        expected_attrs = {"authors": "authors editors",
                          "title": "title series",
                          "meta": ("illustrator translator "
                                   "publisher pubplace year "
                                   "pages price isbn")}
        for attr_group, attr in expected_attrs.items():
            expected_attrs[attr_group] = attr.split()
        cls.expected_attrs = expected_attrs

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def setUp(self):
        self.pre = self.MockPreProcessed("Some XML paragraph <w:p>")
        self.pre.configure_mock(**self.mock_config)

    def test_mocked_PreProcessed(self):
        pre = self.MockPreProcessed("Some XML paragraph <w:p>")
        pre.configure_mock(**self.mock_config)

        for i, attr in enumerate(("pre_italic", "post_italic", "italic")):
            with self.subTest(attr=attr):
                self.assertHasAttr(pre, attr)
                attr_value = getattr(pre, attr)
                dict_value = self.mock_config[attr]
                self.assertEqual(attr_value, dict_value)

    def test_PostProcessed_attr_by_group(self):
        pre = self.pre
        post = paragraphs.PostProcessed(pre)

        for group in self.expected_attrs:
            with self.subTest(criteria=f"{group} - hasAttr"):
                for attr in self.expected_attrs[group]:
                    with self.subTest(attr=attr):

                        self.assertHasAttr(post, attr)

    def test_Processor_attrs_by_group(self):
        for group in self.processor_classes.keys():
            with self.subTest(group=group):
                self.check_Processor_attrs_by_group(group)

    def check_Processor_attrs_by_group(self, group):
        pre = self.pre
        Processor = self.processor_classes[group]
        self.assertIn(group.lower(), Processor.__name__.lower(),
                      msg="Precondition - class name is sensible!")
        expected_attrs = self.expected_attrs[group]

        processor_obj = Processor(pre)

        for attr in expected_attrs:
            with self.subTest(attr=attr):
                self.assertHasAttr(processor_obj, attr)


class Test_ProcessorAuthor_Class(ProcessorTestCase_Abstract, ProcessorTestCase_Genuine):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = "pre_italic"
        cls.strings = cls._strings[cls.group]
        cls.Processor = paragraphs.ProcessorAuthors

        cls.mock_config = PREPROCESSED_CONFIG
        cls.MockPreProcessed = MagicMock(autospec=helpers.paragraphs.PreProcessed)

        cls.strucural_arg["good"] = ("Hockey, Katherine M., and David G. "
                                     "Horrell (eds),")
        cls.strucural_arg["bad"] = ("Berthelot, Katell, Michaël Langlois and "
                                    "Thierry Legrand,")

        cls.first_author = "del Olmo Lete, Gregorio,"

        cls.editorial_arg = {}
        cls.editorial_arg["(eds),"] = cls.strucural_arg["good"]
        cls.editorial_arg["(ed.),"] = "Alexandru, Florian (ed.),"
        cls.editorial_arg[""] = cls.first_author

    def test_assignement_to_editor_or_author_attr(self):
        for editor_substring, raw_string in self.editorial_arg.items():

            with self.subTest(criteria="specific", substring=editor_substring):
                processor_obj = self.Processor(raw_string)
                self.assertEqual(processor_obj.isEditor(),
                                 bool(editor_substring),
                                 msg="Precondtion")

                # Test1: either attribute list is populated
                is_populated = any([len(processor_obj.authors),
                                    len(processor_obj.editors)])
                self.assertTrue(is_populated, msg=f"raw_string = {raw_string}")
                # Test2: the correct list is populated:
                self.check_author_editor_attr_assignment(processor_obj)

        with self.subTest(criteria="generic"):
            for raw_string in self.strings:
                processor_obj = self.Processor(raw_string)

                if processor_obj.isValid():
                    self.check_author_editor_attr_assignment(processor_obj)
                else:
                    continue  # Ignore badly structured raw strings.

    def check_author_editor_attr_assignment(self, processor_obj):
        if processor_obj.isEditor():
            self.assertGreaterEqual(len(processor_obj.editors), 1)
            self.assertEqual(len(processor_obj.authors), 0)
        else:
            self.assertGreaterEqual(len(processor_obj.authors), 1)
            self.assertEqual(len(processor_obj.editors), 0)

    def test_method_isEditor(self):
        for editor_suffix in ["(ed.),", "(eds),"]:
            msg = f"isEditor - positive specific {editor_suffix}"
            with self.subTest(criteria=msg):
                string = self.editorial_arg[editor_suffix]

                processor_obj = self.Processor(string)
                flag = processor_obj.isEditor()

                self.assertTrue(flag)
                self.assertIs(flag, True)

        no_editor_suffix = ""
        with self.subTest(criteria=f"strip - negative specific"):
            string = self.editorial_arg[no_editor_suffix]

            processor_obj = self.Processor(string)
            flag = processor_obj.isEditor()

            self.assertFalse(flag)
            self.assertIs(flag, False)

    def test_cls_method_strip_editor(self):
        cls_method = self.Processor.strip_editor

        naughty = "(eds),"
        with self.subTest(criteria=f"strip - positive specific {naughty}"):
            string = self.editorial_arg[naughty]
            self.assertIn(naughty, string, msg="Precondtion")
            # Expect string should have a trailing space.
            expect = "Hockey, Katherine M., and David G. Horrell "

            result = cls_method(string)

            self.assertNotEqual(string, result)
            self.assertEqual(result, expect)

        naughty = "(ed.),"
        with self.subTest(criteria=f"strip - positive specific {naughty}"):
            string = self.editorial_arg[naughty]
            self.assertIn(naughty, string, msg="Precondtion")
            # Expect string should have a trailing space.
            expect = "Alexandru, Florian "

            result = cls_method(string)

            self.assertNotEqual(string, result)
            self.assertEqual(result, expect)

        with self.subTest(criteria="strip - negative specific"):
            string = self.editorial_arg[""]
            expect = string

            result = cls_method(string)

            self.assertEqual(result, expect)

        with self.subTest(criteria="strip - generic"):
            missing1, missing2 = "(eds),", "(ed.),"
            counter = 0
            for string in self.strings:
                if missing1 in string:
                    counter += 1
                    result = cls_method(string)
                    self.assertNotIn(missing1, result)
                elif missing2 in string:
                    counter += 1
                    result = cls_method(string)
                    self.assertNotIn(missing2, result)
                else:
                    result = cls_method(string)
                    self.assertEqual(string, result)

            assertmsg = "Postcondition: nothing was actually tested!"
            self.assertGreater(counter, 0, msg=assertmsg)

    def test_cls_method_split(self):
        cls_method = self.Processor.split
        with self.subTest(criteria="split - multi auth"):
            string = self.strucural_arg["good"]
            expected = ["Katherine M. Hockey", "David G. Horrell"]

            result = cls_method(string)

            self.assertListEqual(expected, result)

        with self.subTest(criteria="split - multi auth, bad struct"):
            string = self.strucural_arg["bad"]
            expected = ["Katell Berthelot",
                        "Michaël Langlois and Thierry Legrand"]

            result = cls_method(string)

            self.assertListEqual(expected, result)

        with self.subTest(criteria="split - single author"):
            string = self.first_author
            expected = ["Gregorio del Olmo Lete"]

            result = cls_method(string)

            self.assertListEqual(expected, result)


class Test_ProcessorTitle_Class(ProcessorTestCase_Abstract, ProcessorTestCase_Genuine):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = "italic"
        cls.strings = cls._strings[cls.group]
        cls.Processor = paragraphs.ProcessorTitle

        cls.mock_config = PREPROCESSED_CONFIG
        cls.MockPreProcessed = MagicMock(autospec=helpers.paragraphs.PreProcessed)

        cls.strucural_arg["good"] = ("New Approaches to an Integrated History "
                                     "of the Holocaust: Social History, "
                                     "Representation, Theory. Lessons and "
                                     "Legacies: Volume XIII.")
        cls.strucural_arg["bad"] = ("Lessons and Legacies, Volume XIII: New "
                                    "Approaches to an Integrated History of "
                                    "the Holocaust: Social History, "
                                    "Representation, Theory.")

        cls.series_arg = {}
        cls.series_arg[True] = (cls.strucural_arg["good"])
        cls.series_arg[False] = ("An Early History of Compassion: Emotion "
                                 "and Imagination in Hellenistic Judaism.")

    def test_assignment_to_title_and_series(self):
        for series_flag, raw_string in self.series_arg.items():

            with self.subTest(criteria="specific", has_series=series_flag):
                processor_obj = self.Processor(raw_string)
                self.assertEqual(processor_obj.isSeries(),
                                 series_flag,
                                 msg="Precondtion")

                # Test1: both attributes is a string even if empty
                is_string = all([isinstance(processor_obj.title, str),
                                 isinstance(processor_obj.series, str)])
                self.assertTrue(is_string)

                # Test2: either attribute is populated
                is_populated = any([len(processor_obj.title),
                                    len(processor_obj.series)])
                self.assertTrue(is_populated, msg=f"raw_string = {raw_string}")

                # Test3: the correct list is populated:
                self.check_title_series_attr_assignment(processor_obj)

        with self.subTest(criteria="generic"):
            for raw_string in self.strings:
                processor_obj = self.Processor(raw_string)

                if processor_obj.isValid():
                    self.check_title_series_attr_assignment(processor_obj)
                else:
                    continue  # Ignore badly structured raw strings.

    def check_title_series_attr_assignment(self, processor_obj):
        if processor_obj.isSeries():
            self.assertGreaterEqual(len(processor_obj.title), 1)
            self.assertGreaterEqual(len(processor_obj.series), 1)
        else:
            self.assertGreaterEqual(len(processor_obj.title), 1)
            self.assertEqual(len(processor_obj.series), 0)

    def test_method_isSeries_specific(self):
        for expected_bool, raw_string in self.series_arg.items():

            processor_obj = self.Processor(raw_string)

            self.assertEqual(processor_obj.isSeries(), expected_bool)

    def test_method_isSeries_general(self):
        tally = defaultdict(int)
        expect_series_count = 2  # Expect 2 raw strings with legit seriesinfo

        for raw_string in self.strings:
            processor_obj = self.Processor(raw_string)
            tally[processor_obj.isSeries()] += 1

        self.assertEqual(tally[True], expect_series_count)
        self.assertEqual(tally[False], len(self.strings) - expect_series_count)

    def test_cls_method_split(self):
        cls_method = self.Processor.split
        with self.subTest(criteria="split - title + series"):
            string = self.strucural_arg["good"]
            expected = [("New Approaches to an Integrated History of the "
                         "Holocaust: Social History, Representation, Theory"),
                         "Lessons and Legacies: Volume XIII"]

            result = cls_method(string)

            self.assertListEqual(expected, result)

        with self.subTest(criteria="split - title + series, bad structure"):
            string = self.strucural_arg["bad"]
            expected = [string.strip().strip(".").strip(), ""]

            result = cls_method(string)

            self.assertListEqual(expected, result)

        with self.subTest(criteria="split - title only"):
            string = self.series_arg[False]
            expected = [string.strip().strip(".").strip(), ""]

            result = cls_method(string)

            self.assertListEqual(expected, result)


class Test_ProcessorMeta_Class(ProcessorTestCase_Abstract, ProcessorTestCase_Genuine):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = "post_italic"
        cls.strings = cls._strings[cls.group]
        cls.Processor = paragraphs.ProcessorMeta

        cls.mock_config = PREPROCESSED_CONFIG
        cls.MockPreProcessed = MagicMock(autospec=helpers.paragraphs.PreProcessed)

        cls.strucural_arg["good"] = ("Translated by Michaela Lang. Indiana "
                                     "University Press, Bloomington IN, 2018. "
                                     "ix, 161 pp. $65.00. ISBN 978 0 25303 "
                                     "835 7.")
        cls.strucural_arg["bad"] = ("The Jewish Museum of Greece, Athens, "
                                    "2018. 312 pp. ISBN 978 9 60888 539 4.")

        cls.extra_arg = {}
        cls.extra_arg[True] = cls.strucural_arg["good"]
        cls.extra_arg[False] = ("Brill, Leiden, 2018. xiii, 240 pp. €94.00. "
                                "ISBN 978 9 00434 447 1.")

        cls.illustrator_translator_arg = {}
        cls.illustrator_translator_arg["illustrator"] = ("Illustrated by Kristine A. Thorsen. Northwestern University Press, Evanston IL, 2018. xii, 642 pp. $45.00. ISBN 978 0 81012 607 7.")
        cls.illustrator_translator_arg["translator"] = cls.strucural_arg["good"]

        cls.issn_isbn_arg = {}
        cls.issn_isbn_arg["issn"] = ("The Hebrew University of Jerusalem, "
                                     "Jerusalem, 2018. x, 660 pp. $120.00. "
                                     "ISSN 0793 4289.")
        cls.issn_isbn_arg["isbn"] = cls.strucural_arg["good"]

    @staticmethod
    def get_strings_by_attr(obj, attrs):
        "Helper func to retrieve object strings from a list of attribute names."
        for attr in attrs:
            yield getattr(obj, attr)

    def test_assignement_of_extra_attributes_specifc(self):
        extra_attrs = set("extra translator illustrator".split())
        non_extra_attrs = self.Processor._data_attrs - extra_attrs

        for extra_flag, raw_string in self.extra_arg.items():
            processor_obj = self.Processor(raw_string)
            self.assertEqual(processor_obj.isExtra(),
                             extra_flag,
                             msg="Precondtion")

            # Test1: extra attributes are a string even if empty
            query = self.get_strings_by_attr(processor_obj, extra_attrs)
            is_string = all([isinstance(q, str) for q in query])
            self.assertTrue(is_string)

            # Test2a: non-extra attr have populated strings
            query = self.get_strings_by_attr(processor_obj, non_extra_attrs)
            is_notempty = all([len(q) > 0 for q in query])
            self.assertTrue(is_notempty)

            # Test2b: extra attrs are partially populated with strings
            self.assertTrue(processor_obj.isValid(), msg="Precondition")
            self.check_extra_attr_assignment(processor_obj)

    def test_assignement_of_extra_attributes_generic(self):
        for raw_string in self.strings:
            processor_obj = self.Processor(raw_string)

            if processor_obj.isValid():
                self.check_extra_attr_assignment(processor_obj)
            else:
                continue  # Ignore badly structured raw strings.

    def check_extra_attr_assignment(self, processor_obj):
        attrs = processor_obj._extra_attrs
        query = self.get_strings_by_attr(processor_obj, attrs)
        if processor_obj.isExtra():
            self.assertGreaterEqual(len(processor_obj.extra), 1)
            any_notempty = any([len(q) > 0 for q in query])
            self.assertTrue(any_notempty)
        else:
            self.assertEqual(len(processor_obj.extra), 0)
            all_empty = any([len(q) == 0 for q in query])
            self.assertTrue(all_empty)

    def test_assignment_of_translator_illustrator_attributes(self):
        for key_string, raw_string in self.illustrator_translator_arg.items():
            obj = self.Processor(raw_string)

            self.asserTrue(obj.isExtra(), msg="Precondtion")
            self.asserTrue(obj.isValid(), msg="Precondtion")
            self.assertIn(key_string, obj._extra_attrs, msg="Precondtion")

            # Test1: Assignment is to the correct attribute
            value = getattr(obj, key_string)  # key_string == an attr of obj
            self.assertGreater(len(value), 0)

            # Test2: Other extra attrs are left empty
            other_attrs = obj._extra_attrs - set([key_string])
            query = self.get_strings_by_attr(obj, other_attrs)
            all_empty = any([len(q) == 0 for q in query])
            self.assertTrue(all_empty)

    def test_method_isExtra(self):
        for key in ["illustrator", "translator"]:
            msg = f"Positive method result for '{key}'"
            with self.subTest(criteria=msg):
                string = self.illustrator_translator_arg[key]

                processor_obj = self.Processor(string)
                flag = processor_obj.isExtra()

                self.assertTrue(flag)
                self.assertIs(flag, True)

        with self.subTest(criteria="Negative method result"):
            string = self.extra_arg[False]

            processor_obj = self.Processor(string)
            flag = processor_obj.isExtra()

            self.assertFalse(flag)
            self.assertIs(flag, False)

    def test_cls_method_split(self):
        cls_method = self.Processor.split
        with self.subTest(criteria="split - good, no extra"):
            expected = {"publisher": "Brill",
                        "pubplace": "Leiden",
                        "year": "2018",
                        "pages": "xiii, 240 pp",
                        "price": "€94.00",
                        "isbn": "ISBN 978 9 00434 447 1",
                        "issn": "",
                        "extra": "",
                        "translator": "",
                        "illustrator": "",
            }
            result = cls_method(self.extra_arg[False])

            self.assertDictEqual(expected, result)

        with self.subTest(criteria="split - good, with extra"):
            expected = {"publisher": "Indiana University Press",
                        "pubplace": "Bloomington IN",
                        "year": "2018",
                        "pages": "ix, 161 pp",
                        "price": "$65.00",
                        "isbn": "ISBN 978 0 25303 835 7",
                        "issn": "",
                        "extra": "Translated by Michaela Lang",
                        "translator": "Michaela Lang",
                        "illustrator": "",
            }

            result = cls_method(self.illustrator_translator_arg["translator"])

            self.assertDictEqual(expected, result)

        with self.subTest(criteria="split - bad"):
            expected = {"publisher": "The Jewish Museum of Greece",
                        "pubplace": "Athens",
                        "year": "2018",
                        "pages": "312 pp",
                        "price": "",
                        "isbn": "ISBN 978 9 60888 539 4",
                        "issn": "",
                        "extra": "",
                        "translator": "",
                        "illustrator": "",
            }
            result = cls_method(self.strucural_arg["bad"])

            self.assertDictEqual(expected, result)

    def test_cls_method_count_fullstop(self):
        self.assertEqual(self.Processor.count_fullstop(""), 0)
        self.assertEqual(self.Processor.count_fullstop("."), 1)
        self.assertEqual(self.Processor.count_fullstop("." * 5), 5)

        string = self.strucural_arg["good"]
        self.assertEqual(self.Processor.count_fullstop(string), 6)

    def test_cls_search_isbn(self):
        method = self.Processor._search_isbn
        setup = [("good", "ISBN 978 0 25303 835 7"),
                 ("bad", "ISBN 978 9 60888 539 4")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_issn(self):
        method = self.Processor._search_issn
        setup = [("issn", "ISSN 0793 4289"),
                 ("isbn", "")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.issn_isbn_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_price(self):
        method = self.Processor._search_price
        setup = [("good", "$65.00"),
                 ("bad", "")  # Deliberately empty.
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_pages(self):
        method = self.Processor._search_pages
        setup = [("good", "ix, 161 pp"),
                 ("bad", "312 pp")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_year(self):
        method = self.Processor._search_year
        setup = [("good", "2018"),
                 ("bad", "2018")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_publisher(self):
        method = self.Processor._search_publisher
        setup = [("good", "Indiana University Press"),
                 ("bad", "The Jewish Museum of Greece")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_pubplace(self):
        method = self.Processor._search_pubplace
        setup = [("good", "Bloomington IN"),
                 ("bad", "Athens")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_extra(self):
        method = self.Processor._search_extra
        setup = [("good", "Translated by Michaela Lang"),
                 ("bad", "")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.strucural_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_illustrator(self):
        method = self.Processor._search_illustrator
        setup = [("illustrator", "Kristine A. Thorsen"),
                 ("translator", "")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.illustrator_translator_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

    def test_cls_search_translator(self):
        method = self.Processor._search_translator
        setup = [("illustrator", ""),
                 ("translator", "Michaela Lang")
        ]

        for key, expected in setup:
            with self.subTest(criteria=f"structure is {key}"):
                string = self.illustrator_translator_arg[key]
                result = method(string)
                self.assertEqual(expected, result)

class Test_PreProcessed(ParagraphsTestCase):

    def setUp(self):
        paragraphs.PreProcessed._reset_xpaths()

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
        expected_substrings = ["paragraph", "has", "Pattern",
                               "found", "one italic section",
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
                 self.italic_interrupted_sequence_longer_raises,
                 self.italic_interrupted_sequence_with_whitespace_raises]
        expected = [((False, 'Pre Text 1Pre Text 2Pre Text 3'),
                    (True, 'Italic Text 1Italic Text 2'),
                    (False, 'Post Text 1Post Text 2Post Text 3')),
                    # func1 result
                    ((False, 'Pre Text 1Pre Text 2Pre Text 3'),
                     (True, 'First Italic Text 1First Italic Text 2'),
                     (False, 'Interupted Not Italic 1Interupted Not Italic 2'),
                     (True, 'Second Italic Text 1Second Italic Text 2Second Italic Text 3'),
                     (False, 'Post Text 1Post Text 2')),
                    # func2 result
                    ((False, 'Pre Text 1Pre Text 2Pre Text 3'),
                     (True, 'First Italic Text 1First Italic Text 2'),
                     (False, 'Interupted Not Italic 1Interupted Not Italic 2'),
                     (True, ' '),
                     (False, 'Post Text 1Post Text 2'))
                     # func3 result
                    ]
        details = [tuple((f"italic: {s}" for b, s in t if b)) for t in expected]
        funcs = {f: (f.__name__, exp, d) for f, exp, d in zip(funcs, expected, details)}
        method_grouper = paragraphs.PreProcessed._group_contiguous_text_by_font
        method_is_valid = paragraphs.PreProcessed._is_valid_italic_pattern
        expected_exception = exceptions.ParagraphItalicPatternWarning
        whitespace_generic = "# SPACE! "
        whitespace_repl = chr(9251)  # OPEN BOX symbol
        whitespace_specific = f"...Not Italic 2{whitespace_repl}Post Text..."
        substrings = [whitespace_generic,
                      whitespace_repl,
                      whitespace_specific]

        for xml_func, (name, expect_res, detail) in funcs.items():
            xml = xml_func()
            with self.subTest(xml_type=name, fatal=True):
                actual_res = method_grouper(xml, _memoize=False)

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
                    self.assertIn("raise", name, msg=msg)
                    self.assertSubstringsInString(detail, error)
                else:
                    msg = f"{name} should not have passed!"
                    self.assertIn("correct", name, msg=msg)
                    continue
                # Test3 : Verify whitespace annotated.
                if error and "whitespace" in name:
                    self.assertSubstringsInString(substrings, error)
                else:
                    msg = f"{name} skipped a test!"
                    self.assertNotIn("whitespace", name, msg=msg)

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

    def italic_interrupted_sequence_with_whitespace_raises(self):
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
            <w:t> </w:t>
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
