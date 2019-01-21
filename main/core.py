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
    input.is_suitable(input_filename, fatal=True)
    ext = os.path.splitext(input_filename)[1]
    if ext != ".xml":
        msg = (f"The file '{os.path.basename(input_filename)}' is incompatible"
               "with this program. Please use Microsoft Word to generate a"
               "suitable XML file. This can be accomplised as follows: 1) Open"
               "the document in Microsoft Word, 2) in the menubar go to 'File'"
               "> 'Save As...' to open as dialog window, 3) choose the 'File"
               "Format' called XML from the spinner at the bottom of the dialog"
               "window, 4) choose a suitable location to save the file, 5)"
               " click 'Save'.\nNow run this program again with the new XML"
               "file.")
        raise TypeError(msg)
    else:
        with open(output_filename, "w") as handle:
            handle.write("foo")
        return


if __name__ == '__main__':
    argparser = RecomposeArgParser()
    args = argparser.get_args()
    kwargs = {"xml_filename": args.input, "output_filename": args.output}
    main(**kwargs)
