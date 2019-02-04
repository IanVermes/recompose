#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Logging function for Recompose.

Copyright: Ian Vermes 2019
"""
import exceptions

import os
import logging
import logging.config
import configparser
import functools


def _get_relpath_relative_to_this_py(filename):
    relative = os.path.join(__file__, filename)
    relative = os.path.relpath(relative)
    return relative


__CONFIG_FILE = _get_relpath_relative_to_this_py("../../logger_setup.cfg")
__DEFAULT_LOGFILENAME = _get_relpath_relative_to_this_py("../../../logs/recompose.log")


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
        logging.config.fileConfig(config, disable_existing_loggers=False)
    except Exception as err:
        detail = repr(err)
        raise exceptions.LoggingSetupError(detail=detail) from err
    return


def log_and_reraise(logger=None):
    """Decorator that logs exceptions as errors before reraising."""
    if logger is None:
        try:
            logger = LOGGER
        except NameError:
            logger = getLogger()
    else:
        if isinstance(logger, str):
            logger = getLogger(logger)
        elif isinstance(logger, (logging.RootLogger, logging.Logger)):
            logger = logger
        else:
            msg = f"Accepts logging.Logger or str not {type(logger)}"
            raise TypeError(msg)

    def middle(func):
        functools.wraps(func)

        def decorator(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except exceptions.RecomposeWarning as err:
                logger.warning(err)
                raise
            except exceptions.RecomposeError as err:
                logger.error(err)
                raise
            except Exception as err:
                logger.critical(err)
                raise
            else:
                return result
        return decorator
    return middle


def finish_logging():
    """Tidy up and end all logging operations."""
    logging.shutdown()
    return


def getLogger(name=None):
    """Convenince function to get the default logger."""
    if name is None:
        name = "recomposeLogger"
    return logging.getLogger(name)


def default_log_filename():
    """Convenince function to get the package default output detination."""
    return __DEFAULT_LOGFILENAME
