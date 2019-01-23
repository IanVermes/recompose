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


class Test_XMLBase_Class(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.klass = xml._XMLAsInputBase

    def test_instantiation(self):
        self.klass()


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

    @unittest.expectedFailure
    def test_attr_xpaths(self):
        attr = "tree"
        return_type = xml.Xpaths

        _result = self.multi_attr_test(attr, return_type)

    @unittest.expectedFailure
    def test_attr_nsmap(self):
        attr = "nsmap"
        return_type = dict

        _result = self.multi_attr_test(attr, return_type)

    @unittest.expectedFailure
    def test_attr_paragraphs(self):
        attr = "paragraphs"
        return_type = types.GeneratorType

        _result = self.multi_attr_test(attr, return_type)

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
                self.assertTrue(len(result))
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
        inputs = [self.bad_input, self.decoy_input]
        inputcheck = self.klass()

        for input in inputs:
            with self.subTest(input=input):
                result = inputcheck.isSuitable(input)

                self.assertIsInstance(result, bool)
                self.assertFalse(result)

    def test_isSuitable_fails_fatally(self):
        inputs = [self.bad_input, self.decoy_input]
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
        expected_strings = ["Microsoft", "xml",
                            os.path.basename(self.bad_input), "wrong", "file",
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

    def check_boolean_fileobject_method(self, func, bool2file_map):
        for expected, file_list in bool2file_map.items():
            for filename in file_list:
                if not os.path.isfile(filename):
                    raise ValueError(f"Could not find {filename} for testing.")
                with self.subTest(expected_bool=expected,
                                  file=os.path.basename(filename)):
                    with open(filename, "r") as handle:

                        result = func(handle)

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
