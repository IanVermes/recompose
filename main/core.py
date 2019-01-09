#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Recompose Core.

Simple program that takes a JJS bibliographic .docx file (or .xml derivative),
parses it into bespoke JJS XML.

The bibliographic data in the .docx file lists numerous books and formatted with
a bibliographic style. The style is similar to the APA or Chicago style for
"a book in print" but with some extra information such as price and ISBN.

Each book bibliography is in its own paragraph, and hence seperating it from its
neighbours.

Each book bibliography is a string with varied punctuation and featuring
the following components:
* an author(s)
* title (in italics)
* publisher
* city of publisher
* year of publication
* pages(roman and arabic numerals)
* price
* ISBN

Copyright Ian Vermes 2019
"""

import exceptions

import os


class _TestingPrimitive():
    """This class is used by the package's test suit for initial validation."""

    @classmethod
    def verify_import_tester(cls):
        """Confirms that the module has been imported."""
        return True

    @classmethod
    def raise_package_error(cls):
        """Confirms that the module has a base exception."""
        package_base_eror = exceptions.RecomposeError()
        raise package_base_eror


def main():
    """Entry point."""
    pass


if __name__ == '__main__':
    main()
