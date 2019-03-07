#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""A collection of special testcases for multiple inheritence.

Copyright: Ian Vermes 2019
"""

import unittest

class ProcessorTestCase_Abstract(object):
    """To use, note the class order when doing multiple inheritence.

    >>> class NewTestCase(ProcessorTestCase_Abstract, unittest.TestCase): pass
    """

    def test_instantiation_with_string(self):
        Processor = self.Processor

        with self.subTest(criteria="empty string"):
            with self.assertRaises(ValueError):
                obj = Processor("")

        with self.subTest(criteria="wrong type"):
            with self.assertRaises(TypeError):
                obj = Processor(42)

    def test_instantiation_with_PreProcessed(self):
        attr_in_question = self.group
        bad_config = self.mock_config.copy()
        bad_config.pop(attr_in_question)
        wrong_config = self.mock_config.copy()
        wrong_value = 53
        wrong_config[attr_in_question] = wrong_value

        Processor = self.Processor

        crit = (f"{Processor.__name__} using a bad PreProcessed - no attr: "
                f"{attr_in_question}")
        with self.subTest(criteria=crit):
            bad_pre = self.MockPreProcessed("Some XML paragraph <w:p>")
            bad_pre.configure_mock(**bad_config)
            delattr(bad_pre, attr_in_question)
            self.assertFalse(hasattr(bad_pre, attr_in_question),
                             msg="Precondition")

            with self.assertRaises(TypeError):
                Processor(bad_pre)

        crit = (f"{Processor.__name__} using a bad PreProcessed - attr value "
                "wrongtype")
        with self.subTest(criteria=crit):
            wrong_pre = self.MockPreProcessed("Some XML paragraph <w:p>")
            wrong_pre.configure_mock(**wrong_config)
            self.assertHasAttr(wrong_pre, attr_in_question, msg="Precondition")
            self.assertEqual(getattr(wrong_pre, attr_in_question), wrong_value)

            with self.assertRaises(TypeError):
                Processor(wrong_pre)

        crit = (f"{Processor.__name__} using a good PreProcessed")
        with self.subTest(criteria=crit):
            good_pre = self.MockPreProcessed("Some XML paragraph <w:p>")
            good_pre.configure_mock(**self.mock_config)
            self.assertHasAttr(good_pre, attr_in_question, msg="Precondition")

            Processor(good_pre)

    def test_method_isValid_specific(self):
        subtest_info = {"criteria": "", "processor": self.Processor.__name__}
        # Good result  - tuple, zeroth value is zero
        # Bad result  - tuple, zeroth value is not zero
        passing_visible, passing_hidden = True, (0, "")
        failing_visible = False
        lowerbound_hidden_length = 1
        subtest_info["criteria"] = "arg:good structure"
        with self.subTest(**subtest_info):
            arg = self.strucural_arg["good"]
            processor_obj = self.Processor(arg)

            result_visible = processor_obj.isValid()
            result_hidden = processor_obj.validation_results

            self.assertTrue(result_visible)
            self.assertEqual(passing_visible, result_visible)
            self.assertEqual(lowerbound_hidden_length, len(result_hidden))
            self.assertIn(passing_hidden, result_hidden)

        subtest_info["criteria"] = "arg:bad structure"
        with self.subTest(**subtest_info):
            arg = self.strucural_arg["bad"]
            processor_obj = self.Processor(arg)

            result_visible = processor_obj.isValid()
            result_hidden = processor_obj.validation_results

            self.assertFalse(result_visible)
            self.assertEqual(failing_visible, result_visible)
            self.assertGreaterEqual(len(result_hidden), lowerbound_hidden_length)
            self.assertNotIn(passing_hidden, result_hidden)
            for hidden in result_hidden:
                self.assertIsInstance(hidden, tuple)
                self.assertIsInstance(hidden[0], int)
                self.assertIsInstance(hidden[1], str)

    def test_method_isValid_general(self):
        are_good = []
        are_bad = []
        for string in self.strings:

            processor_obj = self.Processor(string)
            result = processor_obj.isValid()
            reason = processor_obj.validation_results
            msg = f"  {result} -> {string}\n    {reason}"
            if result:
                are_good.append(msg)
            else:
                are_bad.append(msg)
        success_percent = len(are_good) / len(self.strings) * 100
        shortmsg = (f"***\n {self.Processor.__name__} - success rate: "
                    f"{success_percent:2.1f}%.")
        bad_strings = '\n'.join(are_bad)
        good_strings = '\n'.join(are_good)
        longmsg = (f"{shortmsg}"
                   f"\nFAILING:\n{bad_strings}"
                   f"\nPASSING:\n{good_strings}\n***")

        for percent in [25, 50, 75, 85, 95, 99]:
            self.assertGreaterEqual(success_percent, percent, msg=longmsg)

    def test_cls_method_split(self):
        self.fail("Overload this method.")



if __name__ == '__main__':
    import doctest
    doctest.testmod()
