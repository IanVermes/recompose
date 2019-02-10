#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/helpers/xml.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase, InputFileTestCase
from helpers import xml
import exceptions

from lxml import etree

import unittest
import os
import types


class Test_XPaths_Class(InputFileTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.klass = xml.XPaths
        cls.package_exception = exceptions.RecomposeError

    def setUp(self):
        self.instance = self.klass(self.good_input)

    def test_attr_nsmap(self):
        attr = "nsmap"

        value = getattr(self.instance, attr)

        self.assertIsInstance(value, dict)

    def test_nsmap_generic_contents(self):
        nsmap = self.instance.nsmap

        self.assertNotIn(None, nsmap)

        for prefix, uri in nsmap.items():
            with self.subTest(prefix=prefix):
                self.assertIsInstance(prefix, str)
                self.assertNotIn(":", prefix)
                self.assertNotIn(" ", prefix)
                self.assertIsInstance(uri, str)

    def test_nsmap_generic_prefixes(self):
        prefixes = set(self.instance.nsmap)
        expected = set(xml.EXPECTED_PREFIXES)

        diff = prefixes.symmetric_difference(expected)

        self.assertEqual(len(prefixes), len(expected))
        self.assertEqual(len(diff), 2)
        self.assertIn(None, diff)
        self.assertIn("ns0", diff)

    def test_nsmap_specific_prefix_uri_pairings(self):
        nsmap = self.instance.nsmap
        expected = xml.SAMPLE_URIS
        for exp_pref, exp_uri in expected.items():
            with self.subTest(prefix=exp_pref):
                if exp_pref is None:
                    exp_pref = "ns0"
                res_uri = nsmap.get(exp_pref, "")

                self.assertEqual(res_uri, exp_uri)

    def test_method_get(self):
        method = self.instance.get
        # veneer method
        self.test_method_get_xpath(method)

    def test_method_get_xpath(self, method=None):
        if method is None:
            method = self.instance.get_xpath

        query = "//*"
        expected_type = etree.XPath
        self.assertNotIn(query, self.instance)

        xpath_obj = method(query)

        self.assertIn(query, self.instance)
        self.assertIsInstance(xpath_obj, expected_type)

    def test_method_add_xpath(self):
        query = "//*"
        expected_type = type(None)
        self.assertNotIn(query, self.instance)

        result = self.instance.add_xpath(query)

        self.assertIn(query, self.instance)
        self.assertIsInstance(result, expected_type)

    def test_method_add_xpath_illegal(self):
        query = "//self()"
        substrings = ["query", "XPath", query, "invalid", "reason"]

        with self.assertRaises(Exception) as failure:
            self.instance.add_xpath(query)

        self.assertIsInstance(failure.exception, exceptions.XPathQueryError)
        self.assertIsInstance(failure.exception, ValueError)
        self.assertSubstringsInString(substrings, str(failure.exception))

    def test_method_make_nsmap(self):
        tree = etree.parse(self.good_input)
        find_prefix_uri = etree.XPath("//namespace::*")
        list_dicts = []

        exp_nsmap1 = {k: v for k, v in find_prefix_uri(tree)}
        res_nsmap1 = self.klass.make_nsmap(self.good_input)
        list_dicts.append((exp_nsmap1, res_nsmap1))

        exp_nsmap2 = {k if k is not None else "ns0": v for k, v in find_prefix_uri(tree)}
        res_nsmap2 = self.klass.make_nsmap(self.good_input, replace=True)
        list_dicts.append((exp_nsmap2, res_nsmap2))

        exp_nsmap3 = {k if k is not None else "foo": v for k, v in find_prefix_uri(tree)}
        res_nsmap3 = self.klass.make_nsmap(self.good_input, replace=True, repl="foo")
        list_dicts.append((exp_nsmap3, res_nsmap3))

        for i, tup in enumerate(list_dicts, start=1):
            with self.subTest(test_number=i):
                self.assertDictEqual(*tup)

    def test_method_make_nsmap_with_clashing_prefix(self):
        tree = etree.parse(self.good_input)
        find_prefix_uri = etree.XPath("//namespace::*")
        prefix = "w"
        substrings = [prefix, "URI", "assign", "already", "repl",
                      "kwarg", "different"]
        expected_exception = exceptions.PrefixSubstitutionError

        exp_nsmap = {k: v for k, v in find_prefix_uri(tree)}
        self.assertIn(prefix, exp_nsmap)
        with self.assertRaises(Exception) as failure:
            self.klass.make_nsmap(self.good_input, replace=True, repl=prefix)

        self.assertIsInstance(failure.exception, expected_exception)
        self.assertIsInstance(failure.exception, ValueError)
        self.assertSubstringsInString(substrings, str(failure.exception))


class Test_XMLAsInput_Workhorse(InputFileTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.klass = xml.XMLAsInput
        cls.package_exception = exceptions.RecomposeError
        cls.attr_not_ready_exception = exceptions.InputOperationError

        cls._memo_inputs = {}

        try:
            input = cls.klass()
            input.isSuitable(cls.good_input, fatal=True)
        except Exception as err:
            msg = "Can not run tests as .isSuitable fails!"
            raise AssertionError(msg) from err
        else:
            cls.input = input

        cls.attr_files = {cls.good_input: True, cls.decoy_input: False, cls.bad_input: False}

    def test_attr_root(self):
        attr = "root"
        return_type = etree._Element

        _result = self.multi_attr_test(attr, return_type)

    def test_attr_tree(self):
        attr = "tree"
        return_type = etree._ElementTree

        _result = self.multi_attr_test(attr, return_type)

    def test_attr_xpaths(self):
        attr = "xpaths"
        return_type = xml.XPaths

        _result = self.multi_attr_test(attr, return_type)

    def test_attr_nsmap(self):
        attr = "nsmap"
        return_type = dict

        _result = self.multi_attr_test(attr, return_type)

    def test_method_paragraphs(self):
        attr = "iter_paragraphs"
        container_type = types.GeneratorType
        content_type = etree._Element

        # Test 1
        container = self.input.iter_paragraphs()
        self.assertIsInstance(container, container_type)
        container = list(container)

        # Test 2 - go over contents genericly
        types_in_container = {type(item) for item in container}
        self.assertIn(content_type, types_in_container)
        self.assertEqual(len(types_in_container), 1)

        # Test 3 - confirm suitability of method by confirming result homogeny
        depths, names = [], []
        expect_name = "w:p"
        for item in container:
            names.append(self.get_prefixed_name(item))
            depths.append(self.get_element_depth(item))
        depths, names = set(depths), set(names)
        self.assertEqual(len(names), 1)
        self.assertEqual(len(depths), 1)
        self.assertIn(expect_name, names, msg=repr(names))

    def multi_attr_test(self, attr, return_type):
        if not isinstance(return_type, type):
            msg = f"Bad arg for this function {repr(return_type)}: not a class."
            raise ValueError(msg)
        # Test attr presence
        self.assertHasAttr(self.input, attr)
        # Test attr for instances evaluated with other files
        # and exceptions raised when failure is encountered
        for tup in self.attr_files.items():
            with self.subTest(should_return=tup[1], file=tup[0]):
                self._attr_test(tup, attr)
        # Test the return type is correct
        value = getattr(self.input, attr)
        self.assertIsInstance(value, return_type)
        return value

    def _attr_test(self, file_and_boolean, attr):
        filename, does_return = file_and_boolean
        input = self._memo_inputs.get(filename)

        # Memoize
        if input is None:
            input = self.klass()
            input.isSuitable(filename, fatal=False)
            self._memo_inputs[filename] = input

        if does_return:
            result = getattr(input, attr)
            self.assertIsNotNone(result)
            try:
                errmsg = (f"result type: {type(result)} -- is length an "
                          "appropriate test?")
                self.assertTrue(len(result), msg=errmsg)
            except TypeError:
                self.assertTrue(result)
        else:
            assertmsg = "\nWrong error type!"
            with self.assertRaises(Exception, msg=assertmsg) as fail:
                result = getattr(input, attr)
            self.assertIsInstance(fail.exception, RuntimeError)
            self.assertIsInstance(fail.exception, self.attr_not_ready_exception)
            errmsg = str(fail.exception)
            method = input.isSuitable.__name__
            substrings = (f"call object method {method} necessary "
                          "attributes").split()
            self.assertSubstringsInString(substrings, errmsg)


class Test_XMLAsInput_Suitablilty(InputFileTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.klass = xml.XMLAsInput
        cls.package_exception = exceptions.RecomposeError
        cls.resource_dir = "resources/test_resources"
        if not os.path.isdir(cls.resource_dir):
            msg = (f"Could not setup test, directory '{cls.resource_dir}' was "
                    "not found.")
            raise ValueError(msg)


    def test_instantiation(self):

        self.klass()

    def test_has_isSuitable_method(self):
        object = self.klass()
        attr = "isSuitable"
        self.assertHasAttr(object, attr)

    def test_isSuitable_passes(self):
        inputcheck = self.klass()
        input = self.good_input

        result = inputcheck.isSuitable(input)

        self.assertIsInstance(result, bool)
        self.assertTrue(result)

    def test_isSuitable_fails(self):
        inputs = [self.bad_input, self.decoy_input, self.track_changes_input]
        inputcheck = self.klass()

        for input in inputs:
            with self.subTest(input=input):
                result = inputcheck.isSuitable(input)

                self.assertIsInstance(result, bool)
                self.assertFalse(result)

    def test_isSuitable_fails_fatally(self):
        inputs = [self.bad_input, self.decoy_input, self.track_changes_input]
        inputcheck = self.klass()
        expected_exception = self.package_exception

        for input in inputs:
            with self.subTest(input=input):
                with self.assertRaises(expected_exception):
                    inputcheck.isSuitable(input, fatal=True)

    def test_isSuitable_raises_appropiate_exception(self):
        inputcheck = self.klass()
        input = self.bad_input
        expected_exception = exceptions.InputFileError
        expected_strings = ["Microsoft", "xml", "click", "choose",
                            os.path.basename(input), "wrong", "file",
                            "type"]

        # Check right exception is raised
        with self.assertRaises(expected_exception) as failure:
            inputcheck.isSuitable(input, fatal=True)

        # Check exception is of appropriate type
        error = failure.exception
        is_subclass = issubclass(type(error), self.package_exception)
        self.assertTrue(is_subclass, msg=("Exception is "
                        f"of an unexpected subtype: {type(error)}"))

        # Check exception has the correct message for the user.
        self.assertSubstringsInString(substrings=expected_strings,
                                      string=str(error))

    def test_isSuitable_raises_appropiate_exception_if_xml_has_trackchanges(self):
        inputcheck = self.klass()
        input = self.track_changes_input
        expected_exception = exceptions.InputFileTrackChangesError
        expected_strings = ["Microsoft", "xml", "cannot be used", "click",
                            "choose", os.path.basename(input), "file", "Track",
                            "Changes", "accept", "Review",
                            "Accept All Changes"]

        # Check right exception is raised
        with self.assertRaises(expected_exception) as failure:
            inputcheck.isSuitable(input, fatal=True)

        # Check exception is of appropriate type
        error = failure.exception
        is_subclass = issubclass(type(error), self.package_exception)
        self.assertTrue(is_subclass, msg=("Exception is "
                        f"of an unexpected subtype: {type(error)}"))

        # Check exception has the correct message for the user.
        self.assertSubstringsInString(substrings=expected_strings,
                                      string=str(error))

    def check_boolean_fileobject_method(self, func, bool2file_map):
        for expected, file_list in bool2file_map.items():
            for filename in file_list:
                if not os.path.isfile(filename):
                    raise ValueError(f"Could not find {filename} for testing.")
                with self.subTest(expected_bool=expected,
                                  file=os.path.basename(filename)):
                    with open(filename, "r") as handle:

                        result = func(handle)
                    if os.path.basename(filename) == "valid_namespace_2.xml":
                        specific_msg = """*** its a valid file that previously
had trackchanges but they were accepted/rejected. The resultant file has a
slightly different default namespace... infact it has 2 default namespaces but
the first one is overwritten by the second one as they share the same prefix
'None'
"""
                        self.assertEqual(expected, result, msg=specific_msg)
                    else:
                        self.assertEqual(expected, result)


    def get_test_files(self, keyword):
        allowed_keys = {True, False}
        result = {}
        with os.scandir(self.resource_dir) as dir:
            for file in dir:
                if file.is_file() and keyword in file.name:
                    fullname = os.path.join(self.resource_dir, file.name)
                    if file.name.startswith("valid"):
                        result.setdefault(True, []).append(fullname)
                    elif file.name.startswith("invalid"):
                        result.setdefault(False, []).append(fullname)
        correct_keys = allowed_keys != set(result)
        has_values = all([bool(result.get(k)) for k in allowed_keys])
        if correct_keys and has_values:
            extra_keys = set(result) - allowed_keys
            msg = ("Did not find sufficient files. "
                   f"True: {repr(result.get(True))}, "
                   f"False: {repr(result.get(True))}, "
                   f"extrakeys? {repr(extra_keys)}.")
            raise ValueError(msg)
        else:
            return result

    def test_private_method_sniff(self):
        has = "sniff"
        test_files = self.get_test_files(keyword=has)
        instance = self.klass()
        method = instance._sniff

        self.check_boolean_fileobject_method(func=method,
                                             bool2file_map=test_files)

    def test_private_method_parse(self):
        has = "parse"
        test_files = self.get_test_files(keyword=has)
        instance = self.klass()
        method = instance._parse

        self.check_boolean_fileobject_method(func=method,
                                             bool2file_map=test_files)

    def test_method_trackchanges(self):
        has = "trackchanges"
        test_files = self.get_test_files(keyword=has)
        instance = self.klass()
        method = instance._trackchanges

        self.check_boolean_fileobject_method(func=method,
                                             bool2file_map=test_files)

    def test_private_method_namespaces(self):
        has = "namespace"
        test_files = self.get_test_files(keyword=has)
        instance = self.klass()
        method = instance._namespace

        self.check_boolean_fileobject_method(func=method,
                                         bool2file_map=test_files)

    def test_battery_of_tests_method(self):
        instance = self.klass()
        method = instance._battery_test
        good_file = self.good_input
        bad_files = [f for f in os.listdir(self.resource_dir)
                             if f.startswith("invalid")]
        bad_files = [os.path.join(self.resource_dir, f) for f in bad_files]

        files = {True: [good_file],
                 False: bad_files}
        self.check_boolean_fileobject_method(func=method,
                                             bool2file_map=files)


if __name__ == '__main__':
    unittest.main()
