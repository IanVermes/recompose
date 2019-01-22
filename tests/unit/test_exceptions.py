#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Unit test of main/helpers/xml.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase

import unittest
import os
import inspect
import sys

import importlib

try:
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
class Test_Exceptions(BaseTestCase):

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

                err = cls(arg_string)

                self.assertIn(arg_string, str(err))

        self.assertGreater(counter, 0, msg="No Exception classes tested!")

    def test_pkgexception_subclass_has_default_string(self):
        parent_cls = exceptions._CodedErrors
        counter = 0
        for cls in self.get_subclasses_only("exceptions", parent_cls):
            cls_name = cls.__name__
            counter += 1
            with self.subTest(cls_name=cls_name):

                default = exceptions.EXC_STRINGS.get(cls._strcode, "")

                err = cls()

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
                default = exceptions.EXC_STRINGS.get(cls._strcode, "")
                expected = " ".join([default, arg_string])

                err = cls(arg_string)

                self.assertSubstringsInString([default, expected], str(err))
                self.assertEqual(expected, str(err), msg=f"{repr(str(err))}")

        self.assertGreater(counter, 0, msg="No Exception classes tested!")






if __name__ == '__main__':
    unittest.main()
