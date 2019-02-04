#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Recompose Exceptions

Copyright: Ian Vermes 2019
"""

import os
import configparser
import textwrap
import sys

__CONFIG_FILE = os.path.join(__file__, "..", "exception_strings.cfg")
__CONFIG_FILE = os.path.abspath(__CONFIG_FILE)

__CONFIG = configparser.ConfigParser()
__CONFIG.read(__CONFIG_FILE)
EXC_STRINGS = __CONFIG.defaults()


class RecomposeError(Exception):
    """Base exception for this package."""


class RecomposeWarning(Warning):
    """Base warning for this package."""


class RecomposeExit(RecomposeError):

    def __init__(self, *args, exception=None):
        if exception is None and len(args):
            exception = args[0]
        if exception is None or not isinstance(exception, Exception):
            cls_name = self.__class__.__name__
            msg = f"{cls_name} was called without an exception."
            raise TypeError(msg)
        else:
            string = self._printable_string(exception)
            new_args = [string]
            super().__init__(*new_args)
            self._print_self()
            self.clean_exit()

    @staticmethod
    def _hanging_indent(string):
        dedented_text = textwrap.dedent(string).strip()
        string = textwrap.fill(dedented_text,
                               initial_indent="\n" + " " * 4,
                               subsequent_indent=" " * 6,
                               width=80)
        return string

    @staticmethod
    def _deep_hanging_indent(string):
        dedented_text = textwrap.dedent(string).strip()
        string = textwrap.fill(dedented_text,
                               initial_indent="\n" + " " * 6,
                               subsequent_indent=" " * 8,
                               width=80)
        return string

    def _print_self(self):
        string = f"{self.__class__.__name__}:{str(self)}"
        print(string)

    def _printable_string(self, exception):
        exc_name = exception.__class__.__name__
        args = exception.args
        string = self._hanging_indent(f"Error: {exc_name}")
        reason_template = "Reason: {value}"
        nul_value = "-none given-"
        if len(args) == 0:
            value = nul_value
        elif len(args) == 1:
            if not args[0]:
                value = nul_value
            else:
                value = str(args[0])
        else:
            value = [f"arg{i:2d}: {a}" for i, a in enumerate(args)]
            value = "".join(map(self.__deep_hanging_indent, value))
        reason = reason_template.format(value=value, numbers=False)
        string += self._hanging_indent(reason)
        return string

    @staticmethod
    def clean_exit(code=0):
        sys.exit(code)


class __Coded():

    def __init__(self, *args, detail=None):
        if not self._strcode:
            errmsg = (f"Exception {self.__class__.__name__} has no value for "
                      "_strcode class attribute.")
            raise ValueError(errmsg)
        default_string = EXC_STRINGS[self._strcode]
        # Challenge detail foramtting
        needs_detail_format = "{detail}" in default_string
        if not detail and needs_detail_format:
            errmsg = (f"Exception {self.__class__.__name__} default message "
                      "requires a string for the kwarg 'detail'. Unformatted "
                      f"message:\n{repr(default_string)}.")
            raise ValueError(errmsg)
        # Intercept arguments
        if any(args):
            first_arg = str(args[0])
            first_arg = f"{default_string} {first_arg}"
            args = (first_arg, *args[1:])
        else:
            first_arg = default_string
        # Add detail
        if detail is not None:
            if needs_detail_format:
                first_arg = first_arg.format(detail=detail)
            else:
                first_arg = f"{first_arg} Detail: {detail}"
        args = (first_arg, *args[1:])
        super().__init__(*args)


class _CodedErrors(__Coded, RecomposeError):
    _strcode = None


class _CodedWarning(__Coded, RecomposeWarning):
    _strcode = None


class InputFileError(_CodedErrors):
    """For when the input file is not correct."""
    _strcode = "input_type"


class InputFileTrackChangesError(InputFileError):
    _strcode = "input_trackchanges"


class InputOperationError(_CodedErrors, RuntimeError):
    """Tried to use methods before calling the check method of the class."""
    _strcode = "input_check_skipped"


class PrefixSubstitutionError(_CodedErrors, ValueError):
    """Tried to replace None with an already assigned prefix."""
    _strcode = "prefix_clash"


class XPathQueryError(_CodedErrors, ValueError):
    """The XPath query is incorrectly formed."""
    _strcode = "xpath_invalid_syntax"


class LoggingSetupError(_CodedErrors):
    """Logging could not be customised: config, parse or file error."""
    _strcode = "logging_setup"


class PreProcessedValueError(_CodedErrors, ValueError):
    """If the class is initialised with the wrong element."""
    _strcode = "preprocessed_init"

class ParagraphItalicPatternWarning(_CodedWarning):
    """Paragraph lacks the normal non-italic, italic, not-italic pattern."""
    _strcode = "preprocessed_italic_pattern"

class ExampleWarning(_CodedWarning):
    _strcode = "example_warn"
