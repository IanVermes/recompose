#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Parse the commandline line arguments for Recompose.

Copyright: Ian Vermes 2019
"""

import argparse
import os


class RecomposeArgParser(object):

    def __init__(self):
        self.output_basename = "output.xml"

    def default_output(self):
        basename = self.output_basename
        dirname = os.getcwd()
        filename = os.path.abspath(os.path.join(dirname, basename))
        return filename

    @staticmethod
    def is_file(filename):
        """Validate that the directory is genuine not just a string."""

        def file_or_exception(filename):
            if os.path.exists(filename):
                if os.path.isfile(filename):
                    result = filename
                elif os.path.isdir(filename):
                    msg = f"Expected a file not a directory, got '{filename}'."
                    result = argparse.ArgumentTypeError(msg)
                else:
                    result = TypeError(filename)
            else:
                msg = f"The location '{filename}' does not exist!"
                result = argparse.ArgumentTypeError(msg)
            return result

        return_obj = file_or_exception(filename)

        if isinstance(return_obj, Exception):
            raise return_obj
        else:
            return return_obj

    def _make_parser(self):
        desc = ("Read a Microsoft Word XML and produce a books-received "
                "XML as output.")
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument("input",
                            metavar="XML",
                            type=lambda x: self.is_file(x),
                            help="The xml file to process.")
        parser.add_argument("output",
                            nargs='?',
                            metavar="OUTPUT",
                            type=str,
                            default=self.default_output(),
                            help=("The output xml filename. If omitted will "
                                  "create a file called "
                                  f"'{self.output_basename}' in the current "
                                  "working directory.")
        )

        return parser

    def get_args(self):
        parser = self._make_parser()
        args = parser.parse_args()
        return args
