#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Logging function for Recompose.

classes:
    LogSuppressOrReraise    - decorator/context manager
    LoggerWrapper

convenience funcs:
    setLevel
    getLogger

package level funcs:
    setup_logging
    finish_logging

functions:
    default_log_filename
    get_current_logging_level
    get_default_logging_level
    log_and_reraise          - decorator/context manager
    log_suppress_or_reraise  - decorator/context manager
    reset_logging_level
    set_logging_level


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
__DEFAULT_LOGGER_NAME = "recomposeLogger"
__DEFAULT_LOGGING_LEVEL = py_logging.NOTSET

class LogSuppressOrReraise(contextlib.ContextDecorator):
    """Context manager or decorator - logs, raises & can suppress exceptions.

    Args:
        exceptions: Exception type(s) to suppress otherwise raise all others.
                    By default, does not suppress any exceptions.
    Kwarg:
        logger(str, logging.Logger): The name of a logger or logger object.
                    By default, uses the module logger if available otherwise
                    the package logger.
        prelog(str, callable): Before the exception is logged, log some extra
                    information. This could a string or a callable. Expensive
                    or dynamic strings could be curried into a function.
    Exceptions:
        TypeError
    """

    _DEBUG = False

    def __init__(self, *exceptions, logger=None, prelog=None):
        super().__init__()
        self.suppress_exceptions = set(self._flatten(*exceptions))
        self._assign_logger(logger)
        self._prelog = prelog

    def _assign_logger(self, logger=None):
        if self._DEBUG:
            logger = LoggerWrapper(py_logging.getLogger('dummyLogger'))
            logger.logger.addHandler(py_logging.NullHandler())
            self.logger = logger
            return
        if logger is None:
            try:
                self.logger = LOGGER
            except NameError:
                self.logger = getLogger()
        else:
            if isinstance(logger, str):
                self.logger = getLogger(logger)
            elif isinstance(logger, LoggerWrapper):
                self.logger = logger
            elif isinstance(logger, (py_logging.RootLogger, py_logging.Logger)):
                self.logger = LoggerWrapper(logger)
            else:
                msg = f"Accepts logging.Logger or str not {type(logger)}"
                raise TypeError(msg)

    def _log_according_to_exc(self, exc):
        if not exc:
            return
        else:
            self._log_prelog_object()
            self.logger.autolog(exc)

    def _log_prelog_object(self, level=None):
        if self._prelog is None or not self._prelog:
            return
        else:
            autolog_kwargs = {}
            if level is None:
                autolog_kwargs["level"] = "INFO"
            else:
                autolog_kwargs["level"] = level
            try:
                autolog_kwargs["source"] = self._prelog()
            except TypeError:
                if isinstance(self._prelog, str):
                    autolog_kwargs["source"] = self._prelog
                elif isinstance(self._prelog, (list, tuple)):
                    autolog_kwargs["source"] = self._prelog[0]
                    autolog_kwargs["level"] = self._prelog[1]
                else:
                    raise
            if not isinstance(autolog_kwargs["source"], str):
                msg = ("Expected prelog to be a string returning callable"
                       f"or a string not {type(self._prelog)}.")
                raise TypeError(msg)
            else:
                self.logger.autolog(**autolog_kwargs)

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


class LoggerWrapper(py_logging.LoggerAdapter):
    """A logger adapter that logs package exceptions appropiately by level.

    Shares the same interface as a logger.

    Init:
        logger(logging.Logger or logging.RootLogger)

    Methods:
        autolog: Log exceptions with the appropiate level, otherwise log the
                 message/object at level set by the logger, unless the level is
                 otherwise specified.
    """

    def __init__(self, logger):
        extra = {}
        super().__init__(logger, extra)

    def __repr__(self):
        clsname = f"Wrapped{self.logger.__class__.__name__}"
        level = py_logging.getLevelName(self.logger.level)
        return f"<{clsname} {self.logger.name} ({level})>"

    @property
    def level(self):
        return self.logger.level

    def autolog(self, source, level=None, **kwargs):
        """Log the stringable object at an appropiate level.

        The level of the logging record is in general the same as the logger
        level unless it is an exception which hav predefined levels or if the
        level kwarg is specified, in which case the interface is like that of
        logger.log.

        Exceptions are logged as WARNING or greater, with package warnings
        a WARNING, package errors an ERROR and all other exceptions CRITICAL.

        Args:
            source: Strings, exceptions, or objects that are stringable.
        Kwargs:
            level: Numeric code or string code, if specified, otherwise default
                   is to use logger.level or follow exception rules (see above).
            **kwargs: Whichever kwargs logger.log permits.
        """
        if isinstance(source, exceptions.RecomposeWarning):
            self.warning(source, **kwargs)
        elif isinstance(source, exceptions.RecomposeError):
            self.error(source, **kwargs)
        elif isinstance(source, Exception):
            self.critical(source, **kwargs)
        else:
            if level is None:
                self.log(self.logger.level, source, **kwargs)
            else:
                try:
                    self.log(level, source, **kwargs)
                except TypeError:
                    logger_method = getattr(self.logger, level.lower())
                    logger_method(source, **kwargs)


def setup_logging(log_filename=None, suppress=False):
    """Setup the logging module to use a config file or suppress all logging.

    Kwargs:
        log_filename(str, None): By default use the logfile location specified
            by the module, otherwise give a pathlike string with existing
            directories.
        suppress(bool): By default enable logging with the LoggingHandlers
            defined by the logging config. Otherwise 'prevent' logging all
            records to streams or files.
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

    if suppress is False:
        global __DEFAULT_LOGGING_LEVEL
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
    elif suppress is True:
        root_logger = py_logging.root
        root_logger.addHandler(py_logging.NullHandler())
    global __DEFAULT_LOGGING_LEVEL
    __DEFAULT_LOGGING_LEVEL = py_logging.root.level
    return


def log_and_reraise(logger=None, prelog=None, **kwargs):
    """Context manager or decorator - logs & raises exceptions.

    Convenince function to support older implementation.
    """
    exceptions = []
    return LogSuppressOrReraise(*exceptions, logger=logger, prelog=prelog, **kwargs)


def log_suppress_or_reraise(*exceptions, logger=None, prelog=None, **kwargs):
    """Context manager or decorator - logs, raises and can suppress exceptions.

    Convenince function to support older implementation.
    """
    return LogSuppressOrReraise(*exceptions, logger=logger, prelog=prelog, **kwargs)


def finish_logging():
    """Tidy up and end all logging operations."""
    py_logging.shutdown()
    return


def getLogger(name=None):
    """Convenince function to get the default logger."""
    if name is None:
        name = __DEFAULT_LOGGER_NAME
    logger = LoggerWrapper(py_logging.getLogger(name))
    return logger


def default_log_filename():
    """Convenince function to get the package default output detination."""
    return __DEFAULT_LOGFILENAME


def get_default_logging_level():
    """Convenince function to get the package default logging level."""
    return __DEFAULT_LOGGING_LEVEL


def get_current_logging_level():
    """Convenince function to get the package default output detination."""
    logger = getLogger()
    return logger.level


def setLevel(level):
    """Convenince function to set level for the root and package logger."""
    set_logging_level(level)


def set_logging_level(level):
    """Convenince function to set level for the root and package logger."""
    if isinstance(level, str):
        level = getattr(py_logging, level.upper())
    py_logging.root.setLevel(level)
    logger = getLogger()
    logger.setLevel(level)


def reset_logging_level():
    """Convenince function to reset the level of the root and package logger."""
    set_logging_level(get_default_logging_level())
    return get_current_logging_level()
