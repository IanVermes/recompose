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

Copyright: Ian Vermes 2019
"""
import exceptions
from helpers.argparse import RecomposeArgParser
from helpers.xml import XMLAsInput
from helpers.logging import setup_logging, finish_logging

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


def main(input_filename, output_filename):
    """Entry point."""
    input = XMLAsInput()
    try:
        input.isSuitable(input_filename, fatal=True)
    except exceptions.InputFileError as err:
        raise exceptions.RecomposeExit(exception=err) from None
    else:
        with open(output_filename, "w") as handle:
            handle.write("foo")
        return


def main_wrapper(log_filename=None, **kwargs):
    """Entry point with logging tidyed as necessary."""
    if log_filename:
        try:
            setup_logging(log_filename)
            main(**kwargs)
        finally:
            finish_logging()
    else:
        main(**kwargs)


if __name__ == '__main__':
    argparser = RecomposeArgParser()
    kwargs = vars(argparser.get_args())
    main_wrapper(**kwargs)
