#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of resources directory.

Copyright: Ian Vermes 2019
"""

from tests.base_testcases import BaseTestCase

import unittest

import os
import glob


class TestResourcesPresent(BaseTestCase):
    """Check private files are where they should be.

    The files in recompose/resources root are private & off github but should
    be present regardless.
    """

    @classmethod
    def setUpClass(cls):
        cls.files = {"Pretty BR Autumn 2018.xml",
                     "069_02_autumn_2018_books_received.pdf",
                     "BR Autumn 2018.docx",
                     "jjs_schema_1.1.xsd",
                     "invlaid_input.xml",
                     "BR Autumn 2018.xml",
                     "BR Spring 2019 Track Changes.xml",
                     "BR Autumn 2018 UTF8.txt",
                     "BR Spring 2019 (final from ML).xml",
                     "BR Spring 2019 V5.9.xml",
                     "PreProcessed_italic.txt",
                     "PreProcessed_preitalic.txt",
                     "PreProcessed_postitalic.txt"}
        cls.dir = "./resources"

    def test_directory_present(self):
        self.assertTrue(os.path.isdir(self.dir))

    def test_files_present(self):
        any_file = "*.*"
        expected = self.files

        files_found = glob.glob(os.path.join(self.dir, any_file))
        basenames_found = set([os.path.basename(f) for f in files_found])

        self.assertSetEqual(basenames_found, expected)
        self.assertEqual(len(files_found), len(expected))


if __name__ == '__main__':
    unittest.main()
