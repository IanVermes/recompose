#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Logging function for Recompose.

classes:
    LogSuppressOrReraise    - decorator/context manager

functions:
    setup_logging
    log_and_reraise         - decorator/context manager
    log_suppress_or_reraise - decorator/context manager
    finish_logging
    getLogger
    default_log_filename

Copyright: Ian Vermes 2019
"""
import exceptions

import os
import logging as py_logging
import contextlib
import logging.config as py_logging_config
import configparser


def _get_relpath_relative_to_this_py(filename):
    relative = os.path.join(__file__, filename)
    relative = os.path.relpath(relative)
    return relative


__CONFIG_FILE = _get_relpath_relative_to_this_py("../../logger_setup.cfg")
__DEFAULT_LOGFILENAME = _get_relpath_relative_to_this_py("../../../logs/recompose.log")


class LogSuppressOrReraise(contextlib.ContextDecorator):
    """Context manager or decorator - logs, raises & can suppress exceptions.

    Args:
        exceptions: Exception type(s) to suppress otherwise raise all others.
                    By default, does not suppress any exceptions.
    Kwarg:
        logger(str, logging.Logger): The name of a logger or logger object.
                    By default, uses the module logger if available otherwise
                    the package logger.
    Exceptions:
        TypeError
    """

    _DEBUG = False

    def __init__(self, *exceptions, logger=None):
        super().__init__()
        self.suppress_exceptions = set(self._flatten(*exceptions))
        self._assign_logger(logger)

    def _assign_logger(self, logger=None):
        if self._DEBUG:
            self.logger = py_logging.getLogger('dummyLogger')
            self.logger.addHandler(py_logging.NullHandler())
            return
        if logger is None:
            try:
                self.logger = LOGGER
            except NameError:
                self.logger = getLogger()
        else:
            if isinstance(logger, str):
                self.logger = getLogger(logger)
            elif isinstance(logger, (py_logging.RootLogger, py_logging.Logger)):
                self.logger = logger
            else:
                msg = f"Accepts logging.Logger or str not {type(logger)}"
                raise TypeError(msg)

    def _log_according_to_exc(self, exc):
        if not exc:
            return
        elif isinstance(exc, exceptions.RecomposeWarning):
            self.logger.warning(exc)
        elif isinstance(exc, exceptions.RecomposeError):
            self.logger.error(exc)
        else:
            self.logger.critical(exc)

    @classmethod
    def _flatten(cls, *args):
        output = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                output.extend(cls._flatten(*list(arg)))
            else:
                output.append(arg)
        return output

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._log_according_to_exc(exc=exc_value)
        return exc_type in self.suppress_exceptions


def setup_logging(log_filename=None):
    """Setup the logging module using config file.

    Optionally change the location of the log file.
    """
    def check_writeout_directory(log_filename):
        dirname = os.path.dirname(log_filename)
        if dirname == "":  # Ignore empty string dirname -- local output
            return
        else:
            if not os.path.exists(dirname):
                detail = f"no such directory '{dirname}' to write log file."
                raise exceptions.LoggingSetupError(detail=detail)
            else:
                return

    def check_config_file_exists(config_file):
        if os.path.isfile(config_file):
            return
        else:
            detail = f"no file called '{config_file}' was found."
            raise exceptions.LoggingSetupError(detail=detail)

    def get_rawconfig(config_filename, log_filename=None):
        config = configparser.RawConfigParser()
        # Values for overloading
        if log_filename:
            section = "handler_fileHandler"
            option = "args"
            value = f"(\'{log_filename}\', \'w\')"

        try:
            config.read(config_filename)
            if log_filename:
                config.set(section=section, option=option, value=value)
        except configparser.Error as err:
            detail = repr(err)
            raise exceptions.LoggingSetupError(detail=detail) from err
        return config

    config_filename = __CONFIG_FILE
    check_config_file_exists(config_filename)
    if not log_filename:
        log_filename = default_log_filename()
    check_writeout_directory(log_filename)
    config = get_rawconfig(config_filename, log_filename)

    try:
        py_logging_config.fileConfig(config, disable_existing_loggers=False)
    except Exception as err:
        detail = repr(err)
        raise exceptions.LoggingSetupError(detail=detail) from err
    return


def log_and_reraise(logger=None):
    """Context manager or decorator - logs & raises exceptions.

    Convenince function to support older implementation.
    """
    exceptions = []
    return LogSuppressOrReraise(*exceptions, logger=logger)


def log_suppress_or_reraise(*exceptions, logger=None):
    """Context manager or decorator - logs, raises and can suppress exceptions.

    Convenince function to support older implementation.
    """
    return LogSuppressOrReraise(*exceptions, logger=logger)


def finish_logging():
    """Tidy up and end all logging operations."""
    py_logging.shutdown()
    return


def getLogger(name=None):
    """Convenince function to get the default logger."""
    if name is None:
        name = "recomposeLogger"
    return py_logging.getLogger(name)


def default_log_filename():
    """Convenince function to get the package default output detination."""
    return __DEFAULT_LOGFILENAME
