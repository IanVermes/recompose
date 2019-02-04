#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/helpers/xml.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase

import testfixtures

import unittest
import unittest.mock
import os
import inspect
import sys

import importlib

try:  # importing exceptions causes module code to be executed
    import exceptions
except Exception:
    pass  # Test_Import gate keeps all other test cases.

class Test_Import(BaseTestCase):

    @staticmethod
    def cant_import():
        module = "exceptions"

        try:
            importlib.import_module(module)
        except Exception as err:
            detail = repr(err)
        else:
            detail = ""
        return detail

    def test_import_succeeds(self):

        error_detail = self.cant_import()

        assertmsg = ("There is an assertion because the condition is to "
                     "expect NO ERRORS when trying to 'import exceptions'. "
                     f"Import attempt raised an error: {error_detail}.")
        with self.assertRaises(ValueError, msg=assertmsg):
            if error_detail:
                # can_import captured an error
                pass
            else:
                # can_import had no errors, so let this assertion method pass
                raise ValueError("No import errors!")

@unittest.skipIf(Test_Import.cant_import(), reason="Can't import exceptions.")
class Test_ExitException(BaseTestCase):

    class DummyException(Exception):

        def __init__(self):
            string = """Lorem ipsum dolor sit amet, consectetur adipiscing
            elit, sed do eiusmod tempor incididunt ut labore et dolore magna
            aliqua. Ut enim ad minim veniam, quis nostrud exercitation
            ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis
            aute irure dolor in reprehenderit in voluptate velit esse cillum
            dolore eu fugiat nulla pariatur. Excepteur sint occaecat
            cupidatat non proident, sunt in culpa qui officia deserunt
            mollit anim id est laborum.
            """
            string = string.strip().replace("\n", " ")
            args = [string]
            super().__init__(*args)

    @classmethod
    def setUpClass(cls):
        cls.ExitExc = exceptions.RecomposeExit
        cls.some_error = cls.DummyException()

    def test_exitexception_exits_cleanly(self):
        error = self.some_error

        with testfixtures.OutputCapture():
            with self.assertRaises(SystemExit) as fail:
                _ = self.ExitExc(exception=error)

        self.assertEqual(fail.exception.code, 0)

    @unittest.mock.patch("exceptions.RecomposeExit._print_self")
    def test_instantiation_calls_print_method(self, mock_print_self):
        error = self.some_error

        with self.assertRaises(SystemExit):
            exceptions.RecomposeExit(exception=error)

        mock_print_self.assert_called()

    @unittest.mock.patch("exceptions.RecomposeExit.clean_exit")
    def test_instantiation_calls_exit_method(self, mock_clean_exit):
        error = self.some_error

        with testfixtures.OutputCapture() as captured:
            exceptions.RecomposeExit(exception=error)

        self.assertTrue(captured.output.getvalue())

        mock_clean_exit.assert_called()

    def test_exitexception_interface_args_become_kwarg(self):

        error = self.some_error
        with testfixtures.OutputCapture():
            with self.assertRaises(SystemExit):
                self.ExitExc(error)

    def test_exitexception_raises_with_bad_kwarg(self):
        some_value = "foobar"

        with self.assertRaises(TypeError):
            self.ExitExc(some_value)

    def test_exitexception_prints_to_stdout(self):
        error = self.some_error

        with testfixtures.OutputCapture(separate=True) as output:
            with self.assertRaises(SystemExit):
                self.ExitExc(error)

        stderr = output.stderr.getvalue().strip()
        stdout = output.stdout.getvalue().strip()
        self.assertEqual(len(stderr), 0)
        self.assertGreaterEqual(len(stdout), 1)

    def test_exitexception_reproduces_exception_string(self):
        error = self.some_error
        expected_substrings = str(error).split()

        with testfixtures.OutputCapture(separate=True) as output:
            with self.assertRaises(SystemExit):
                self.ExitExc(error)

        stdout = output.stdout.getvalue().strip()
        self.assertSubstringsInString(expected_substrings, stdout)

    def test_exitexception_stdout_string_has_correct_length(self):
        error = self.some_error
        min_bound = 50
        max_bound = 80
        min_bound_special = 0
        with testfixtures.OutputCapture(separate=True) as output:
            with self.assertRaises(SystemExit):
                self.ExitExc(error)

        stdout = output.stdout.getvalue().splitlines()

        special_lines = {0, 1, len(stdout) - 1}
        for i, line in enumerate(stdout):
            with self.subTest(line_index=i):
                if i in special_lines:
                    min = min_bound_special
                else:
                    min = min_bound
                self.assertLengthInRange(line, min, max_bound,
                                         msg=repr(line))

    def test_exitexception_stdout_has_indentation_and_useful_names(self):

        error = self.some_error
        line_1_indent = 4
        line_2_indent = line_1_indent
        line_rest_indent = line_1_indent + 2

        with testfixtures.OutputCapture(separate=True) as output:
            with self.assertRaises(SystemExit):
                self.ExitExc(error)

        stdout = output.stdout.getvalue().splitlines()

        with self.subTest(line="first (class name)"):
            line = stdout[0]
            exp_name = self.ExitExc.__name__
            self.assertIn(exp_name, line)
            self.assertFalse(line.startswith(" "))
        with self.subTest(line="second (err name)"):
            line = stdout[1]
            exp_str = f"Error: {error.__class__.__name__}"
            self.assertIn(exp_str, line)
            self.assertTrue(line.startswith(" "))
            self.assertTrue(line.startswith(" " * line_1_indent))
        with self.subTest(line="third (err reason)"):
            line = stdout[2]
            exp_str = f"Reason: {str(error)[:10]}"
            self.assertIn(exp_str, line)
            self.assertTrue(line.startswith(" "))
            self.assertTrue(line.startswith(" " * line_2_indent))
        for i in range(3, len(stdout)):
            rest_indent = " " * line_rest_indent
            with self.subTest(line="rest", i=3):
                line = stdout[i]
                self.assertTrue(line.startswith(" "))
                self.assertTrue(line.startswith(rest_indent))

@unittest.skipIf(Test_Import.cant_import(), reason="Can't import exceptions.")
class Test_Exceptions(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alternate_detail = "NECESSARY DETAIL STRING"


    def get_subclasses_only(self, module, parent_class):
        def subsample_pred(cls):
            flag1 = issubclass(cls, parent_class)
            # Confirm that the subclass is not the parent class
            flag2 = parent_class != inspect.getmro(cls)[0]
            return (flag1 and flag2)

        classes = inspect.getmembers(sys.modules[module], inspect.isclass)
        subclasses = [cls for name, cls in classes if subsample_pred(cls)]
        return subclasses

    def test_global_config_file(self):
        filename = exceptions.__dict__["__CONFIG_FILE"]
        self.assertTrue(os.path.isfile(filename))

    def test_global_strings(self):
        string_dict = exceptions.EXC_STRINGS
        self.assertIsInstance(string_dict, dict)


    def test_pkgexception_subclasses_STRCODE_attr(self):
        module = "exceptions"
        parent_cls = exceptions._CodedErrors
        class_attribute = "_strcode"
        subclasses = self.get_subclasses_only(module, parent_cls)

        for cls in subclasses:
            with self.subTest(cls_name=cls.__name__):
                self.assertHasAttr(cls, class_attribute,
                                   msg="Missing class attribute.")
                key = cls._strcode
                self.assertIn(key, exceptions.EXC_STRINGS)


    def test_pkgexception_subclass_accepts_string_args(self):
        parent_cls = exceptions._CodedErrors
        counter = 0
        for cls in self.get_subclasses_only("exceptions", parent_cls):
            cls_name = cls.__name__
            counter += 1
            with self.subTest(cls_name=cls_name):

                arg_string = "Foobar - this error text!"

                err = self.instantiate_exception(cls, arg_string)

                self.assertIn(arg_string, str(err))

        self.assertGreater(counter, 0, msg="No Exception classes tested!")

    def test_pkgexception_subclass_has_default_string(self):
        parent_cls = exceptions._CodedErrors
        counter = 0
        for cls in self.get_subclasses_only("exceptions", parent_cls):
            cls_name = cls.__name__
            counter += 1
            with self.subTest(cls_name=cls_name):

                default = self.get_default_string(cls, auto_format=True)

                err = self.instantiate_exception(cls)

                self.assertTrue(default, msg=f"{cls_name} no default string!")
                self.assertEqual(default, str(err), msg=f"{repr(str(err))}")

        self.assertGreater(counter, 0, msg="No Exception classes tested!")

    def test_pkgexception_subclass_has_default_string_with_arg(self):
        parent_cls = exceptions._CodedErrors
        counter = 0
        for cls in self.get_subclasses_only("exceptions", parent_cls):
            cls_name = cls.__name__
            counter += 1
            with self.subTest(cls_name=cls_name):

                arg_string = "Arg string goes second."
                default = self.get_default_string(cls, auto_format=True)
                expected = " ".join([default, arg_string])

                err = self.instantiate_exception(cls, arg_string)

                self.assertSubstringsInString([default, arg_string], str(err))
                self.assertEqual(expected, str(err), msg=f"{repr(str(err))}")

        self.assertGreater(counter, 0, msg="No Exception classes tested!")

    def get_default_string(self, exc_cls, auto_format=False):
        key = exc_cls._strcode
        string = exceptions.EXC_STRINGS.get(key, "")
        if auto_format and "{detail}" in string:
            string = string.format(detail=self.alternate_detail)
        return string

    def instantiate_exception(self, exc_cls, *args, detail=None):
        try:
            error = exc_cls(*args, detail=detail)
        except ValueError as err:
            errmsg = str(err)
            tolerate_substring = ("default message requires a string for the "
                                  "kwarg 'detail'")
            # Handle
            if tolerate_substring in errmsg and not detail:
                try:
                    error = exc_cls(*args, detail=self.alternate_detail)
                except ValueError:
                    raise
                else:
                    was_handled = True
            else:
                raise
        else:
            was_handled = False

        if was_handled:
            assertmsg = (f"This {error.__class__.__name__} exception has a "
                         "default string that requires a 'detail' kwarg. This "
                         "helper function wasn't provided a value for "
                         "'detail' but it tried to rescue the instantiation "
                         f"exception by providing '{self.alternate_detail}' "
                         "and then assertion testing this substring was "
                         "present in the returned error.")
            self.assertIn(self.alternate_detail, str(error), msg=assertmsg)
            return error
        else:
            return error


if __name__ == '__main__':
    unittest.main()
