#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""A collection of classes that unittest.TestCase and correct main package importing.

Copyright: Ian Vermes 2019
"""

import tests.context

import unittest
import itertools
import re
import shlex
import subprocess
import os
import difflib
import unicodedata

# To allow consistent imports of pkg modules
tests.context.main()


class BaseTestCase(unittest.TestCase):
    """Base testcase for the suite."""

    def assertStringsSimilar(self, a, b, ratio, msg=None):
        for i, arg in enumerate([a, b], start=1):
            if not isinstance(arg, str):
                msg = f"arg{i}:{arg} is {type(arg)} and not string."
                raise TypeError(msg)
        threshold = float(ratio)
        if threshold > 1.0 or threshold < 0.0:
            msg = (f"Ratio: {threshold:.3f} is not a value beween 0 and 1 "
                   "inclusive.")
            raise ValueError(msg)
        # Main
        comparison = difflib.SequenceMatcher(None, a, b)
        calc_ratio = comparison.ratio()
        if calc_ratio < threshold:
            assertmsg = (f"String a and b similarity is {calc_ratio:.3f} "
                         f"which is below the threshold of {threshold:.3f}.")
            if msg is not None:
                assertmsg += msg
            raise AssertionError(assertmsg)
        else:
            return


    def assertLengthInRange(self, source, min, max, msg=None):
        try:
            length = len(source)
        except TypeError:
            raise
        else:
            usermsg = f" {msg}." if msg else ""
        if min < 0:
            errmsg = f"min cannot be less than zero, got {min}."
            raise ValueError(errmsg)
        if max < min:
            errmsg = f"max cannot be less than min({min}), got {max}."
            raise ValueError(errmsg)
        # Check above upper bound
        if length > max:
            too_long = (f" * Too long! Upper limit={max}.")
        else:
            too_long = ""
        # Check below lower bound
        if length < min:
            too_short = (f" * Too short! Lower limit={min}.")
        else:
            too_short = ""
        if too_long or too_short:
            strings = [too_long, too_short]
            detail = "\n".join(filter(lambda x: bool(x), strings))
            assertmsg = f"Arg has length={length} and is outside of limits:\n"
            assertmsg += detail
            assertmsg += usermsg
            raise AssertionError(assertmsg)
        else:
            return

    def assertHasAttr(self, obj, attr, msg=None):
        if hasattr(obj, attr):
            return
        else:
            errmsg = f"{repr(obj)} has no attribute {repr(attr)}"
            if msg:
                errmsg += f" : {str(msg)}"
            raise AssertionError(errmsg)


    def assertSubstringsInString(self, substrings, string, msg=None):
        method = "IN"
        self._SubstringsInString_base(substrings, string, method, msg=msg)

    def assertSubstringsNotInString(self, substrings, string, msg=None):
        method = "NOT IN"
        self._SubstringsInString_base(substrings, string, method, msg=msg)

    def _SubstringsInString_base(self, substrings, string, method, msg=None):

        # Precondition
        if isinstance(substrings, str):
            substrings = [substrings]  # Rather than raise a type error.
        if not substrings:
            errmsg = f"Positional argument 1 is invalid: {repr(substrings)}"
            raise ValueError(errmsg)
        if not string:
            errmsg = f"Positional argument 2 is invalid: {repr(string)}"
            raise ValueError(errmsg)
        methods = ("IN", "NOT IN")
        if method not in methods:
            raise ValueError(f"Method arg not valid: chose from {methods}.")

        # Dependent setup:
        def spaceing(n_spaces):
            return "\n" + " " * n_spaces
        if method == "IN":
            line_0 = f"{len(substrings)} substrings were found in the string."
            line_1 = f"{spaceing(4)}Unexpectedly missing:"
            criteria_subs = [sub for sub in substrings if sub not in string]
        else:
            line_0 = f"{len(substrings)} substrings were absent from the string."
            line_1 = f"{spaceing(4)}Unexpectedly present:"
            criteria_subs = [sub for sub in substrings if sub in string]
        # General setup:
        count = len(criteria_subs)  # Expect zero to pass assertion

        # Main loop
        if count > 0:
            detail = "".join([(spaceing(8) + "- " + s) for s in criteria_subs])
            errmsg = "".join([f"{len(substrings) - count} out of ",
                              line_0, line_1, f"{detail}"])
            if msg:
                errmsg = errmsg + f"{spaceing(4)}Custom message : {msg}"
            raise AssertionError(errmsg)
        else:
            return

    def assertFileInDirectory(self, file, directory, msg=None):
        assert_method = "in"
        self._fileInOrNotInDirectory(file, directory,
                                     method=assert_method, msg=msg)

    def assertFileNotInDirectory(self, file, directory, msg=None):
        assert_method = "not in"
        self._fileInOrNotInDirectory(file, directory,
                                     method=assert_method, msg=msg)

    def _fileInOrNotInDirectory(self, file, directory, method, msg=None):
        # Preconditions
        if not file:
            errmsg = f"Filename is not valid: {repr(file)}."
            if file == "":
                errmsg += "Empty strings are forbidden."
            elif file is None:
                raise TypeError(errmsg)
            raise ValueError(errmsg)

        if not directory:
            directory = "."
        # Main
        funcs = {"in": self.assertIn, "not in": self.assertNotIn}
        try:
            assertion_func = funcs[method]
        except KeyError:
            errmsg = (f"Illegal value method={repr(method)}. Use 'in' for "
                       "self.assertIn or 'not in' for self.assertNotIn.")
            raise ValueError(errmsg)

        files = set(os.path.basename(f) for f in os.listdir(directory))
        file_basename = os.path.basename(file)
        if msg is not None:
            assertion_func(file_basename, files, msg=msg)
        else:
            assertion_func(file_basename, files)


class LoggingTestCase(BaseTestCase):
        # cls.config_file = getattr(helpers.logging, "__CONFIG_FILE")

    def setUp(self):
        import logging
        import logging.config
        self.logging_builtin = logging
        self.logging_builtin_config = logging.config

    def tearDown(self):
        self.logging_builtin.shutdown()

class UnicodeItalicTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        ascii_upper = (chr(i) for i in range(ord("A"), ord("Z") + 1))
        ascii_lower = (chr(i) for i in range(ord("a"), ord("z") + 1))
        ascii_digits = (chr(i) for i in range(ord("0"), ord("9") + 1))
        cls.only_ascii_letters = "".join(itertools.chain(ascii_upper,
                                                         ascii_lower))
        cls.only_ascii_digits = "".join(ascii_digits)
        cls.only_ascii = cls.only_ascii_letters + cls.only_ascii_digits
        cls.ascii_cat = set([unicodedata.category("A"),
                            unicodedata.category("a"),
                            unicodedata.category("0")])
        cls.rgx_hex_code = re.compile(r"([\dA-Fa-f]{1,7}$)")
        cls.empty_box_chr = chr(9633)
        cls.expected_length_letters = 52
        cls.expected_length_digits = 10
        cls.expected_length = cls.expected_length_letters + cls.expected_length_digits
        cls.check_class_variable_precondtions()

    @classmethod
    def check_class_variable_precondtions(cls):
        assert len(cls.only_ascii) == cls.expected_length, "Precondition"
        assert len(cls.only_ascii_letters) == cls.expected_length_letters, "Precondition"
        assert len(cls.only_ascii_digits) == cls.expected_length_digits, "Precondition"
        for char in cls.only_ascii:
            cat = unicodedata.category(char)
            assert cat in cls.ascii_cat, f"Precondition: {cat}"

        hexvalue = "123F"
        match = cls.rgx_hex_code.search(f"foobar {hexvalue}").group(1)
        assert match == hexvalue, "Precondition"


class InputFileTestCase(BaseTestCase):
    """setUpClass assigns frequently used inputs to instance attributes."""

    @classmethod
    def setUpClass(cls):
        cls.output = ""

        cls.good_input = "./resources/BR Autumn 2018.xml"
        cls.bad_input = "./resources/BR Autumn 2018.docx"
        cls.decoy_input = "./resources/invlaid_input.xml"
        cls.track_changes_input = "./resources/BR Spring 2019 Track Changes.xml"
        cls.good_input_accepted_changes = "./resources/BR Spring 2019 (final from ML).xml"
        files = (cls.good_input, cls.bad_input,
                 cls.decoy_input, cls.track_changes_input,
                 cls.good_input_accepted_changes)
        if not all(os.path.isfile(f) for f in files):
            raise FileNotFoundError("Missing file(s)!")

    @staticmethod
    def get_prefixed_name(element, namespaces=None):
        """Helper: get the name of the element as it appears in the XML"""
        if namespaces is None:
            try:
                namespaces = element.nsmap
            except AttributeError:
                tree = element.getroottree()
                namespaces = dict(set(tree.xpath("//namespace::*")))
        name = element.tag
        for prefix, uri in namespaces.items():
            formatted_uri = "{%s}" % uri
            if formatted_uri in name:
                if prefix is None:
                    msg = ("URI of element was found in namespace but prefix "
                           "is None!")
                    raise TypeError(msg)
                formatted_prefix = f"{prefix}:"
                name = name.replace(formatted_uri, formatted_prefix)
                break
        return name

    @staticmethod
    def get_element_depth(element):
        """Helper: get the absolute depth of an element."""
        depth = 0
        while element is not None:
            depth += 1
            element = element.getparent()
        return depth


class ParagraphsTestCase(InputFileTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from helpers import xml
        cls.input = xml.XMLAsInput()
        cls.input.isSuitable(cls.good_input)
        cls.text_filename = "resources/BR Autumn 2018 UTF8.txt"
        if not os.path.isfile(cls.text_filename):
            raise FileNotFoundError(cls.text_filename)


class ProcessorTestCase_Genuine(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls._strings = {}
        cls._str_files = {"pre_italic": "resources/PreProcessed_preitalic.txt",
                          "post_italic": "resources/PreProcessed_postitalic.txt",
                          "italic": "resources/PreProcessed_italic.txt"}
        for key, filename in cls._str_files.items():
            if os.path.exists(filename):
                with open(filename) as handle:
                    lines = [l.strip() for l in handle.readlines()]
                    cls._strings[key] = lines
            else:
                raise FileNotFoundError(filename)

        cls.strucural_arg = {"good": "", "bad": ""}


class CommandLineTestCase(BaseTestCase):

    def invoke_cmd_via_commandline(self, cmd, expected_status, msg=None):
        """Collects the stdout when invoking and validates the exit status."""
        status, stdout = subprocess.getstatusoutput(cmd)

        detail = f"\n *** captured stdout:\nrepr{stdout}"
        if expected_status == 0:
            msg = (f"'$ {cmd}': did not exit cleanly/validly.")
            msg += detail
            self.assertEqual(status, 0, msg=msg)
        elif 0 < expected_status < 3:
            msg = (f"'$ {cmd}': should have exited with an "
                   "error but exited cleanly.")
            msg += detail
            self.assertGreater(status, 0, msg=msg)
        else:
            msg = (f"Got expected_status={repr(expected_status)}, "
                   "not int: 0 <= i < 3.")
            msg += detail
            raise ValueError(msg)

        return stdout

    @classmethod
    def format_cmd(cls, cmd_template, template_kwargs, ignore_precond1=False):
        """Create a safe commandline command."""
        if not ignore_precond1:
            # Precondition 1
            curly_left = cmd_template.count(r"{")
            curly_right = cmd_template.count(r"}")
            key_count = len(template_kwargs)
            if curly_left != curly_right or key_count != curly_left:
                msg = ("The command template is formatted using 'new' Python "
                       "formatting and hence expects curly bracket notaion. "
                       "Furthermore, the number of substrings to inject in to the "
                       "template must match the number of positions for insertion.")
                raise TypeError(msg)
        else:
            # In some of the user stories surplus format strings are
            # deliberately provided, hence the option to skip this precondition
            pass

        # Precondition 2
        prefixes = ("file", "dir")
        bad_keys = []
        for key in template_kwargs:
            if any([key.startswith(p) for p in prefixes]):
                template_kwargs[key] = shlex.quote(template_kwargs.get(key))
            else:
                bad_keys.append(key)
        if bad_keys:
            msg = ("Template formating expects a dictionary with keys that "
                   f"start with '{prefixes}' but got the following bad keys: "
                   f"{repr(bad_keys)}")
            raise TypeError(msg)

        cmd = cmd_template.format(**template_kwargs)
        return cmd
