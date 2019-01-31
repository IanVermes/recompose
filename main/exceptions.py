#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Recompose Exceptions

Copyright: Ian Vermes 2019
"""
import os
import configparser
__CONFIG_FILE = os.path.join(__file__, "..", "exception_strings.cfg")
__CONFIG_FILE = os.path.abspath(__CONFIG_FILE)

__CONFIG = configparser.ConfigParser()
__CONFIG.read(__CONFIG_FILE)
EXC_STRINGS = __CONFIG.defaults()


class RecomposeError(Exception):
    """Base exception for this package."""


class RecomposeWarning(Warning):
    """Base warning for this package."""


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


class InputFileTrackChangesError(_CodedErrors):
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


class ExampleWarning(_CodedWarning):
    _strcode = "example_warn"
