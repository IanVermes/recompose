#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/core.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase, InputFileTestCase
from helpers import xml

import exceptions

import unittest
import os


class Test_XMLBase_Class(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.klass = xml._XMLAsInputBase

    def test_instantiation(self):
        self.klass()


class Test_XMLAsInput_Class(InputFileTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.klass = xml.XMLAsInput
        cls.resource_dir = "resources/test_resources"
        if not os.path.isdir(cls.resource_dir):
            msg = (f"Could not setup test, directory '{cls.resource_dir}' was "
                    "not found.")
            raise ValueError(msg)

    def test_super_implementation(self):
        baseclass = xml._XMLAsInputBase
        childclass = self.klass

        base = baseclass()
        child = childclass()

        self.assertHasAttr(base, "_foo")
        self.assertHasAttr(child, "_foo")

        self.assertNotEqual(base._foo, child._foo)

    def test_instantiation(self):
        input = self.good_input

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
        expected_exception = exceptions.RecomposeError

        for input in inputs:
            with self.subTest(input=input):
                with self.assertRaises(expected_exception):
                    inputcheck.isSuitable(input, fatal=True)

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
        good_file = "resources/test_resources/valid_namespace.xml"
        bad_files = [f for f in os.listdir(self.resource_dir)
                             if f.startswith("invalid")]
        bad_files = [os.path.join(self.resource_dir, f) for f in bad_files]

        files = {True: [good_file],
                 False: bad_files}
        if not os.path.isfile(good_file):
            raise ValueError(f"Could not find the good file '{good_file}'")
        else:
            self.check_boolean_fileobject_method(func=method,
                                                 bool2file_map=files)


if __name__ == '__main__':
    unittest.main()
