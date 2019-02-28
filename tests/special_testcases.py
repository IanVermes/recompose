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

    def test_instantiation_general(self):
        Processor = self.Processor

        with self.subTest(criteria="empty string"):
            with self.assertRaises(ValueError):
                obj = Processor("")

        with self.subTest(criteria="wrong type"):
            with self.assertRaises(TypeError):
                obj = Processor(42)

    def test_instantiation_pre(self):
        attr_in_question = self.group
        bad_config = self.mock_config.copy()
        bad_config.pop(attr_in_question)
        wrong_config = self.mock_config.copy()
        wrong_value = 53
        wrong_config[attr_in_question] = wrong_value

        with self.subTest(criteria=f"Bad PreProcessed - no attr: {attr_in_question}"):
            bad_pre = self.MockPreProcessed("Some XML paragraph <w:p>")
            bad_pre.configure_mock(**bad_config)
            delattr(bad_pre, attr_in_question)
            self.assertFalse(hasattr(bad_pre, attr_in_question),
                             msg="Precondition")

            with self.assertRaises(TypeError):
                self.Processor(bad_pre)

        with self.subTest(criteria=f"Bad PreProcessed - attr value wrongtype"):
            wrong_pre = self.MockPreProcessed("Some XML paragraph <w:p>")
            wrong_pre.configure_mock(**wrong_config)
            self.assertHasAttr(wrong_pre, attr_in_question, msg="Precondition")
            self.assertEqual(getattr(wrong_pre, attr_in_question), wrong_value)

            with self.assertRaises(TypeError):
                self.Processor(wrong_pre)

        with self.subTest(criteria=f"Good PreProcessed"):
            good_pre = self.MockPreProcessed("Some XML paragraph <w:p>")
            good_pre.configure_mock(**self.mock_config)
            self.assertHasAttr(good_pre, attr_in_question, msg="Precondition")

            self.Processor(good_pre)

    def test_method_hasGoodStructure(self):
        subtest_info = {"criteria": "", "processor": self.Processor.__name__}
        # Good result  - tuple, zeroth value is zero
        # Bad result  - tuple, zeroth value is not zero
        passing_result = (0, "")
        subtest_info["criteria"] = "arg:good structure"
        with self.subTest(**subtest_info):
            arg = self.strucural_arg["good"]
            processor_obj = self.Processor(arg)

            result = processor_obj.hasGoodStructure()

            self.assertTupleEqual(result, passing_result)

        subtest_info["criteria"] = "arg:bad structure"
        with self.subTest(**subtest_info):
            arg = self.strucural_arg["bad"]
            processor_obj = self.Processor(arg)

            result = processor_obj.hasGoodStructure()
            self.assertNotEqual(result, passing_result)
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], int)
            self.assertIsInstance(result[1], str)

    def test_cls_method_split(self):
        self.fail("Overload this method.")



if __name__ == '__main__':
    import doctest
    doctest.testmod()
