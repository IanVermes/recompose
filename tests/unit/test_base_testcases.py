#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of tests/base_testcases.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase, CommandLineTestCase, InputFileTestCase

from lxml import etree

import tempfile
import unittest
import os


class Test_BaseTestCase_AssertMethods_StringsSimilar(BaseTestCase):

    def test_assertion_method(self):
        method = self.assertStringsSimilar
        string_a = "x" * 40
        string_b_5050 = "x" * 20 + "y" * 20
        string_b_2575 = "x" * 10 + "y" * 30
        string_b_zero = "y" * 40
        b_data = {string_a: (1.0, "a vs a ratio: {mod_ratio:.2f}"),
                  string_b_5050: (0.5, "a vs b_5050 ratio: {mod_ratio:.2f}"),
                  string_b_2575: (0.25, "a vs b_2575 ratio: {mod_ratio:.2f}"),
                  string_b_zero: (0.0, "a vs b_zero ratio: {mod_ratio:.2f}")}

        for b, (exp_ratio, usage) in b_data.items():
            for modify in (0.0, 0.01, -0.01):
                mod_ratio = exp_ratio + modify
                with self.subTest(usage=usage.format(mod_ratio=mod_ratio)):
                    delta = abs(mod_ratio - exp_ratio)
                    delta_threshold = 0.00001
                    # If mod_ratio ~ exp_ratio: No Assertio
                    # If mod_ratio is greater than exp_ratio: Assert
                    # If mod_ratio is less than exp_ratio: No Assertion
                    try:
                        if delta < delta_threshold:
                            method(string_a, b, mod_ratio)
                        elif mod_ratio > exp_ratio:
                            with self.assertRaises(AssertionError):
                                method(string_a, b, mod_ratio)
                        else:
                            method(string_a, b, mod_ratio)
                    except ValueError:
                        pass  # Ignore OOB ratio related errors

    def test_assertion_preconditions(self):
        method = self.assertStringsSimilar
        string_a = "x" * 40
        string_b = "x" * 20 + "y" * 20
        # Ratio is out of bounds
        for oob in [1.1, -0.1]:
            with self.subTest(usage=f"Out of bound ratio: {oob}"):
                with self.assertRaises(ValueError):
                    method(string_a, string_b, oob)
        # Allow integers
        for int_ratio in [1, 0]:
            with self.subTest(usage=f"Ratio is int not float: {int_ratio}"):
                try:
                    method(string_a, string_b, int_ratio)
                except AssertionError:
                    pass  # Ignore method main functionality
        # Forbid non-strings
        string_c = "12345"
        string_d = 12345
        with self.subTest(usage="bad types"):
            with self.assertRaises(TypeError):
                method(string_c, string_d, 1.0)

class Test_BaseTestCase_AssertMethods_LengthInRange(BaseTestCase):

    def test_assertion_method(self):
        method = self.assertLengthInRange
        length = 30
        string = "x" * length
        errsmg_tooshort = "Too short!"
        errmsg_toolong = "Too long!"

        with self.subTest(usage="in range"):
            method(string, min=0, max=length*2)

        with self.subTest(usage="at max limit"):
            method(string, min=length-5, max=length)

        with self.subTest(usage="at min limit"):
            method(string, min=length, max=length+5)

        with self.subTest(usage="out of range - lower bound"):
            with self.assertRaises(AssertionError) as fail:
                method(string, min=length+1, max=length*2)
            self.assertIn(errsmg_tooshort, str(fail.exception))

        with self.subTest(usage="out of range - upper bound"):
            with self.assertRaises(AssertionError) as fail:
                method(string, min=0, max=length-1)
            self.assertIn(errmsg_toolong, str(fail.exception))

    def test_assertion_method_precondtions(self):
        class LengthLess(): pass
        length = 20
        string = "x" * length
        method = self.assertLengthInRange
        with self.subTest(problem="min less than zero"):
            with self.assertRaises(ValueError):
                method(string, length-length-1, 10)

        with self.subTest(problem="max less than min"):
            with self.assertRaises(ValueError):
                method(string, length, length-1)

        with self.subTest(problem="source has no len"):
            no_length = LengthLess
            with self.assertRaises(TypeError):
                method(no_length, length-1, length)

class Test_BaseTestCase_AssertMethods_HasAttr(BaseTestCase):

    def test_assertion_method(self):
        class Example():

            def __init__(self):
                self.foo = "foobar"

        example = Example()

        self.assertHasAttr(obj=example, attr="foo")

        with self.assertRaises(AssertionError):
            self.assertHasAttr(obj=example, attr="bar")


class Test_BaseTestCase_AssertMethods_Strings(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.string = """Lorem ipsum dolor sit amet, consectetur adipiscing
elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi
ut aliquip ex ea commodo consequat. Duis aute irure dolor in
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa
qui officia deserunt mollit anim id est laborum.
"""
        cls.all_subs = ["Lorem", "ipsum", "consequat", "dolor", "Excepteur",
                        "esse", "in", "est", "voluptate"]
        cls.some_overlap_subs = ["Lorem", "ipsum", "consequat", "foobar",
                                 "pedestrian", "doctor", "toilet"]
        cls.no_subs = ["foobar", "George", "president", "light", "down",
                       "extinguish", "fishing", "articulate", "petty"]
        cls.method_in = cls.assertSubstringsInString
        cls.method_notin = cls.assertSubstringsNotInString

    def test_all_substrings_present(self):
        subs = self.all_subs

        # Test assert substrings IN string
        with self.subTest(method=self.method_in.__name__):
            self.method_in(substrings=subs, string=self.string)

        # Test assert substrings NOT IN string
        with self.subTest(method=self.method_notin.__name__):
            with self.assertRaises(AssertionError) as failure:
                self.method_notin(substrings=subs, string=self.string)
            # Assertion error message test
            err_msg_subs = list(map(lambda x: x.lower(), subs))
            err_msg_subs.append("unexpectedly present")
            self.assertSubstringsInString(substrings=err_msg_subs,
                                          string=str(failure.exception).lower(),
                                          msg=f"orginal: {str(failure.exception)}")

    def test_some_substrings_present(self):
        subs = self.some_overlap_subs
        not_in_count = 4
        subs_notin = [s.lower() for s in subs[-not_in_count:]]
        subs_in = [s.lower() for s in (set(subs) - set(subs_notin))]

        # Test assert substrings IN string
        with self.subTest(method=self.method_in.__name__):
            with self.assertRaises(AssertionError) as fail:
                self.method_in(substrings=subs, string=self.string)
            # Assertion error message test: setup
            err_msg_subs = subs_notin
            err_msg_subs.extend([f"{len(subs_in)}", f"{len(subs)}",
                                 "unexpectedly missing"])
            # Assertion error message test
            self.assertSubstringsInString(substrings=err_msg_subs,
                                          string=str(fail.exception).lower(),
                                          msg=f"orginal: {str(fail.exception)}")

        # Test assert substrings NOT IN string
        with self.subTest(method=self.method_notin.__name__):
            with self.assertRaises(AssertionError) as fail:
                self.method_notin(substrings=subs, string=self.string)
            # Assertion error message test: setup
            err_msg_subs = subs_in
            err_msg_subs.extend([f"{len(subs_notin)}", f"{len(subs)}",
                                 "unexpectedly present"])
            # Assertion error message test
            self.assertSubstringsInString(substrings=err_msg_subs,
                                          string=str(fail.exception).lower(),
                                          msg=f"orginal: {str(fail.exception)}")

    def test_no_substrings_present(self):
        subs = self.no_subs
        not_in_count = len(subs)
        subs_notin = [s.lower() for s in subs[-not_in_count:]]

        # Test assert substrings IN string
        with self.subTest(method=self.method_in.__name__):
            with self.assertRaises(AssertionError) as fail:
                self.method_in(substrings=subs, string=self.string)
            # Assertion error message test: setup
            err_msg_subs = subs_notin
            err_msg_subs.extend(["0", f"{len(subs)}", "unexpectedly missing"])
            # Assertion error message test
            self.assertSubstringsInString(substrings=err_msg_subs,
                                          string=str(fail.exception).lower(),
                                          msg=f"orginal: {str(fail.exception)}")

        # Test assert substrings NOT IN string
        with self.subTest(method=self.method_notin.__name__):
            self.method_notin(substrings=subs, string=self.string)

    def test_empty_substrings(self):
        subs = []

        with self.assertRaises(ValueError):
            self.method_in(substrings=subs, string=self.string)
        with self.assertRaises(ValueError):
            self.method_notin(substrings=subs, string=self.string)

    def test_string_not_list_as_substring(self):
        subs_present = "Lorem ipsum dolor"
        subs_absent = "This archaic concept"

        # Test assert substrings IN string
        with self.subTest(method=self.method_in.__name__):
            self.method_in(substrings=subs_present,
                           string=self.string)
            with self.assertRaises(AssertionError):
                self.method_in(substrings=subs_absent,
                               string=self.string)

        # Test assert substrings NOT IN string
        with self.subTest(method=self.method_notin.__name__):
            self.method_notin(substrings=subs_absent,
                              string=self.string)
            with self.assertRaises(AssertionError):
                self.method_notin(substrings=subs_present,
                                  string=self.string)

    def test_empty_string(self):
        subs = self.some_overlap_subs

        with self.assertRaises(ValueError):
            self.method_in(substrings=subs, string="")
        with self.assertRaises(ValueError):
            self.method_notin(substrings=subs, string="")


class Test_BaseTestCase_AssertMethods_Files(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.extant_file = "/usr/bin/python"
        assert os.path.isfile(cls.extant_file)
        cls.imaginary_file = "/usr/bin/foofoobarbar"
        assert not os.path.isfile(cls.imaginary_file)

        cls.extant_dir = "/usr/bin"
        assert os.path.isdir(cls.extant_dir)

    def test_file_in_directory(self):
        filename = self.extant_file
        dirname = self.extant_dir

        self.assertFileInDirectory(file=filename, directory=dirname)

        with self.assertRaises(AssertionError):
            self.assertFileNotInDirectory(file=filename, directory=dirname)

    def test_file_not_in_directory(self):
        filename = self.imaginary_file
        dirname = self.extant_dir

        self.assertFileNotInDirectory(file=filename, directory=dirname)

        with self.assertRaises(AssertionError):
            self.assertFileInDirectory(file=filename, directory=dirname)

    def test_temp_file_in_directory(self):
        with tempfile.NamedTemporaryFile() as handle:
            filename = handle.name
            dirname = os.path.dirname(filename)

            self.assertTrue(os.path.exists(filename))
            self.assertFileInDirectory(file=filename, directory=dirname)

        # Context manager closes/deletes the tempfile
        self.assertTrue(os.path.exists(False))
        self.assertFileNotInDirectory(file=filename, directory=dirname)

    def test_filename_arg_is_empty_string(self):
        filename = ""
        dirname = os.path.dirname(filename)
        expected_substrings = ["empty string", "filename"]

        with self.assertRaises(ValueError) as fail_first:
            self.assertFileNotInDirectory(file=filename, directory=dirname)

        with self.assertRaises(ValueError) as fail_second:
            self.assertFileInDirectory(file=filename, directory=dirname)

        self.assertSubstringsInString(substrings=expected_substrings,
                                      string=str(fail_first.exception).lower())
        self.assertSubstringsInString(substrings=expected_substrings,
                                      string=str(fail_second.exception).lower())

    def test_directory_arg_is_empty_string(self):
        # Setup: Find a file in the current work directory or abort!
        for item in os.listdir(os.getcwd()):
            if os.path.isfile(item):
                target_file = os.path.basename(item)
                break
            else:
                continue
        else:
            errmsg = (f"To run this test, invoking unittest from commandline "
                      "must be done from a directory that has any file. If a "
                      "file can't be found in the current working directory "
                      "then the test cannot continue.")
            raise RuntimeError(errmsg)

        filename = os.path.basename(target_file)
        dirname = os.path.dirname(target_file)

        self.assertTrue(os.path.isfile(filename))
        self.assertEqual(dirname, "")

        self.assertFileInDirectory(file=filename, directory=dirname)

        with self.assertRaises(AssertionError):
            self.assertFileNotInDirectory(file=filename, directory=dirname)


class Test_InputFileTestCase_Helper_Method(InputFileTestCase):

    @classmethod
    def setUpClass(cls):
        cls.nsmap = {"g": "www.google.com", "w": "www.w3c.org"}
        xml_string = ("<g:doc  xmlns:g='www.google.com' xmlns:w='www.w3c.org'>"
                      "<g:a><w:b/><w:b/></g:a>"
                      "</g:doc>")
        cls.root = etree.fromstring(xml_string)
        cls.root = cls.root.getroottree()

    def test_get_prefixed_name(self):
        query = "//w:b[1]"
        element = self.root.xpath(query, namespaces=self.nsmap)[0]
        expected = "w:b"

        res = InputFileTestCase.get_prefixed_name(element, namespaces=self.nsmap)

        self.assertEqual(res, expected)

    def test_get_prefixed_name_no_namespace_kwarg(self):
        query = "//w:b[1]"
        element = self.root.xpath(query, namespaces=self.nsmap)[0]
        expected = "w:b"

        res = InputFileTestCase.get_prefixed_name(element)

        self.assertEqual(res, expected)

    def test_get_element_depth(self):
        query = "//w:b[1]"
        element = self.root.xpath(query, namespaces=self.nsmap)[0]
        depth = 3

        res = InputFileTestCase.get_element_depth(element)

        self.assertEqual(res, depth)


class Test_CommandLineTestCase_Itself(CommandLineTestCase):

    @classmethod
    def setUpClass(cls):
        cls.cmd_echo = "echo foobar"
        cls.cmd_template_ls = 'ls -l {filename}'

    def test_format_cmd_untouched(self):
        expected = 'echo foobar'
        formatted = self.format_cmd(self.cmd_echo, {})

        self.assertEqual(formatted, expected)

    def test_format_cmd(self):
        naughty_filename = 'somefile; rm -rf ~'
        expected = "ls -l \'somefile; rm -rf ~\'"
        forbidden = self.cmd_template_ls.format(filename=naughty_filename)

        substrings = {"filename": naughty_filename}
        formatted = self.format_cmd(self.cmd_template_ls, substrings)

        self.assertEqual(formatted, expected)
        self.assertNotEqual(formatted, forbidden)

    def test_format_cmd_complex(self):
        filename = os.path.expanduser('~/Desktop')
        template = "test -a {filename}; echo $?"
        expected = "test -a /Users/Ian/Desktop; echo $?"

        substrings = {"filename": filename}
        formatted = self.format_cmd(template, substrings)

        self.assertEqual(formatted, expected)

    def test_format_cmd_bad_template(self):
        substrings = {"fname": "~/Desktop"}
        bad_template = "ls -l {"

        with self.assertRaises(TypeError):
            self.format_cmd(bad_template, substrings)

    def test_format_cmd_bad_dict(self):
        substrings = {"fname": "~/Desktop"}

        with self.assertRaises(TypeError):
            self.format_cmd(self.cmd_template_ls, substrings)

    def test_invoke_cmd_passing(self):
        given_status = 0
        expected_stdout = "foobar"
        cmd = self.cmd_echo

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout)

    def test_invoke_cmd_passing_complex(self):
        given_status = 0
        expected_stdout = "0"
        cmd_template = "test -a {filename}; echo $?"
        filename = os.path.expanduser("/")

        cmd = self.format_cmd(cmd_template, {"filename": filename})

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout, msg=cmd)

    def test_invoke_cmd_failing_complex(self):
        given_status = 0
        # echo execution is successful but "1" reported by test
        expected_stdout = "1"
        cmd_template = "test -a {filename}; echo $?"
        filename = os.path.expanduser("~/FooBar")

        cmd = self.format_cmd(cmd_template, {"filename": filename})

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout, msg=repr(cmd))

    def test_invoke_cmd_failing(self):
        given_status = 1
        expected_stdout = "dirname: illegal option -- h\nusage: dirname path"
        cmd = "dirname -h"

        stdout = self.invoke_cmd_via_commandline(cmd, given_status)

        self.assertEqual(stdout, expected_stdout)

    def test_invoke_cmd_user_gives_wrong_status(self):
        given_status = 0  # cmd is failing so 1 is status
        cmd = "dirname -h"  # -h is not a legal parameter of dirname

        with self.assertRaises(AssertionError):
            self.invoke_cmd_via_commandline(cmd, given_status)


if __name__ == '__main__':
    unittest.main()
