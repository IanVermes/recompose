#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""A collection of classes that unittest.TestCase and correct main package importing.

Copyright: Ian Vermes 2019
"""

import tests.context

import unittest

# To allow consistent imports of pkg modules
tests.context.main()


class BaseTestCase(unittest.TestCase):
    """Base testcase for the suite."""
