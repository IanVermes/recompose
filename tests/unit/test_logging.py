#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of main/helpers/logging.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import LoggingTestCase

import helpers.logging as pkg_logging
import exceptions

import testfixtures

import os
import configparser
import contextlib
import unittest
import tempfile
import collections
import random


def tearDownModule():
    logdir = "./logs"
    for file in os.listdir(logdir):
        os.remove(os.path.join(logdir, file))

class Test_Logging_Setup(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_file = getattr(pkg_logging, "__CONFIG_FILE")

    def test_has_config_file(self):
        config = self.config_file

        self.assertIsNotNone(config,
                             msg="module attibute for cfg not set/wrong.")
        self.assertTrue(os.path.isfile(config), msg=f"Cound not find {config}.")

    def test_config_parses(self):
        config = configparser.ConfigParser()

        try:
            config.read(self.config_file)
        except configparser.ParsingError as err:
            errmsg = repr(err)
        else:
            errmsg = ""

        assertmsg = f"Parsing {self.config_file} failed. Reason: {errmsg}"
        self.assertFalse(errmsg, msg=assertmsg)

    def test_config_setup_succeeds(self):
        try:
            self.logging_builtin_config.fileConfig(self.config_file)
        except Exception as err:
            errmsg = repr(err)
        else:
            errmsg = ""

        assertmsg = f"Parsing {self.config_file} failed. Reason: {errmsg}"
        self.assertFalse(errmsg, msg=assertmsg)

    def test_config_has_default_logfilename_option(self):
        option_name = "logfilename"
        config = configparser.ConfigParser()
        kwargs = {"section": config.default_section, "option": option_name}

        config.read(self.config_file)

        # Check option
        self.assertTrue(config.has_option(**kwargs))
        # Check value of option
        option_value = config.get(**kwargs)
        is_valid_dir = os.path.isdir(os.path.dirname(option_value))
        self.assertTrue(is_valid_dir,
                        msg=("Could not find the directory that "
                             f"{option_value} would reside in."))

    def test_config_filehandler_section_use_default_logfilename_option(self):
        option_name = "args"
        section_name = "handler_fileHandler"
        unformatted_value = "('%(logfilename)s', 'w')"
        config = configparser.ConfigParser()

        config.read(self.config_file)

        exp_kwargs = {"section": config.default_section, "option": "logfilename"}
        expected_substring = config.get(**exp_kwargs)
        res_kwargs = {"section": section_name, "option": option_name}
        res_value = config.get(**res_kwargs)

        with self.subTest(test="does_not_leave_unformatted"):
            self.assertNotEqual(res_value, unformatted_value)
        with self.subTest(test="does_include"):
            self.assertIn(expected_substring, res_value)
        with self.subTest(test="does_interpolate"):
            exp_mapping = {"logfilename": expected_substring}
            self.assertEqual(unformatted_value % exp_mapping, res_value)

    def test_helper_logging_module_has_its_own_default_logfilename(self):
        global_default_logfilename = getattr(pkg_logging, "__DEFAULT_LOGFILENAME")

        is_valid_dir = os.path.isdir(os.path.dirname(global_default_logfilename))

        self.assertTrue(is_valid_dir, msg=("Could not find the directory that "
                                           f"{global_default_logfilename} "
                                           "would reside in."))


class Test_HelperLogging_Runtime_Behaviour(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        config_file = getattr(pkg_logging, "__CONFIG_FILE")
        cls.config = config = configparser.ConfigParser()
        cls.config.read(config_file)
        cls.config_default_log = config.get(config.default_section,
                                            "logfilename")
        cls.module_default_log = getattr(pkg_logging,
                                         "__DEFAULT_LOGFILENAME")

    def setUp(self):
        super().setUp()
        self.remove_these = []

    def tearDown(self):
        super().tearDown()

        for file in self.remove_these:
            if os.path.exists(file):
                os.remove(file)

    def precondition(self, other_file=None):
        files = [self.config_default_log, self.module_default_log]
        if other_file is not None:
            files.append(other_file)
        for unexpected_file in files:
            self.assertFalse(os.path.exists(unexpected_file),
                             msg=("File found & not tidied by earlier test: "
                                  f"{unexpected_file}"))

    def test_setup_function_overloads_config_logfilename_DEFAULT(self):
        self.precondition()
        expected = self.module_default_log
        self.remove_these.append(expected)

        with testfixtures.OutputCapture() as _:
            pkg_logging.setup_logging()
            pkg_logging.finish_logging()

        self.assertFalse(os.path.exists(self.config_default_log))
        self.assertTrue(os.path.exists(expected))

    def test_setup_function_overloads_config_logfilename_USERCHOICE(self):

        with tempfile.TemporaryDirectory() as dirname:
            user_defined_logfilename = os.path.join(dirname, "foobar.log")
            self.precondition(other_file=user_defined_logfilename)

            with testfixtures.OutputCapture() as _:
                pkg_logging.setup_logging(user_defined_logfilename)
                pkg_logging.finish_logging()

            self.assertFalse(os.path.exists(self.config_default_log))
            self.assertFalse(os.path.exists(self.module_default_log))
            self.assertTrue(os.path.exists(user_defined_logfilename))

    def test_setup_function_raises_package_error_with_bad_config(self):
        self.precondition()
        expected_exception = exceptions.LoggingSetupError
        expected_substrings = ["Could", "not", "setup", "logging"]

        dirname = tempfile.TemporaryDirectory()
        dirname.cleanup()  # Explictly closed to provide a non-existant dir
        bad_logfilename = os.path.join(dirname.name, "foo.log")
        self.assertFalse(os.path.exists(os.path.dirname(bad_logfilename)))

        with self.assertRaises(expected_exception) as fail:
            pkg_logging.setup_logging(bad_logfilename)
        pkg_logging.finish_logging()
        self.assertSubstringsInString(expected_substrings, str(fail.exception))

    def test_setup_function_sets_root_logger_to_INFO_level(self):
        import logging
        self.addCleanup(pkg_logging.finish_logging)
        self.remove_these.append(self.config_default_log)
        self.remove_these.append(self.module_default_log)
        expected_level = logging.INFO
        pkg_logging.setup_logging()

        # Test reporting function
        default_level = pkg_logging.get_default_logging_level()
        self.assertEqual(default_level, expected_level)

        # Test package
        pkg_logger = pkg_logging.getLogger()
        self.assertEqual(pkg_logger.name, "recomposeLogger")
        self.assertGreaterEqual(pkg_logger.level, expected_level)

        # Test builtin/root
        builtin_logger = logging.getLogger()
        self.assertEqual(builtin_logger.name, "root")
        self.assertGreaterEqual(pkg_logger.level, expected_level)

    def test_setup_function_has_kwarg_to_suppress_logging_False(self):
        self.addCleanup(pkg_logging.finish_logging)
        self.remove_these.append(self.config_default_log)
        self.remove_these.append(self.module_default_log)

        should_suppress = False
        message = f"FOOBAR - suppress kwarg is {should_suppress}"

        with testfixtures.OutputCapture() as output:
            pkg_logging.setup_logging(suppress=should_suppress)
            logger = pkg_logging.getLogger()
            logger.critical(message)
        self.assertTrue(output.captured)
        self.assertIn(message, output.captured)

    def test_setup_function_has_kwarg_to_suppress_logging_True(self):
        self.addCleanup(pkg_logging.finish_logging)
        self.remove_these.append(self.config_default_log)
        self.remove_these.append(self.module_default_log)

        should_suppress = True
        message = f"FOOBAR - suppress kwarg is {should_suppress}"

        with testfixtures.OutputCapture() as output:
            pkg_logging.setup_logging(suppress=should_suppress)
            logger = pkg_logging.getLogger()
            logger.critical(message)
        self.assertEqual("", output.captured)
        self.assertNotIn(message, output.captured)

    def test_func_changes_logging_level(self):
        self.addCleanup(pkg_logging.finish_logging)
        self.remove_these.append(self.config_default_log)
        self.remove_these.append(self.module_default_log)
        pkg_logging.setup_logging()

        expected_level = pkg_logging.get_default_logging_level()
        pkg_logger = pkg_logging.getLogger()
        initial_level = pkg_logger.level
        self.assertEqual(expected_level, initial_level)

        new_level = "CRITICAL"
        pkg_logging.setLevel(new_level)
        intermediate_level = pkg_logger.level
        self.assertNotEqual(initial_level, intermediate_level)
        self.assertEqual(new_level, pkg_logging.get_current_logging_level_by_name())

        pkg_logging.setLevel(initial_level)
        penultimate_level = pkg_logger.level
        self.assertEqual(initial_level, penultimate_level)

        new_level = "ERROR"
        pkg_logging.setLevel("ERROR")
        final_level = pkg_logger.level
        self.assertNotEqual(penultimate_level, final_level)
        self.assertEqual(new_level, pkg_logging.get_current_logging_level_by_name())

        reset_level = pkg_logging.reset_logging_level()
        self.assertNotEqual(final_level, reset_level)
        self.assertEqual(initial_level, reset_level)

    def test_decorator_raises_exceptions(self):
        decorator = pkg_logging.log_and_reraise
        expected_exception = ValueError

        @decorator()
        def example_func():
            raise expected_exception("generic message")

        with self.assertLogs():
            with self.assertRaises(expected_exception):
                example_func()

    def test_decorator_also_is_context_manager(self):
        decorator_cm = pkg_logging.log_and_reraise
        expected_exception = ValueError

        def undecorated_func():
            raise expected_exception("generic message")

        with self.assertLogs():
            with self.assertRaises(expected_exception):
                # Actual operation
                with decorator_cm():
                        undecorated_func()

    def test_decorator_takes_a_prelogger_kwarg(self):
        decorator_cm = pkg_logging.log_and_reraise
        expected_exception = ValueError

        def undecorated_func():
            raise expected_exception("generic message")

        prelogger_str = "This message before a Critical"
        def prelogger_func():
            return "This message (derived from a callable) before a Critical."

        # Test prelog as a str
        with self.subTest(prelogger="is string"):
            with self.assertLogs():
                with self.assertRaises(expected_exception):
                    # Actual operation
                    with decorator_cm(prelog=prelogger_str):
                        undecorated_func()
        # Test prelog as a callable
        with self.subTest(prelogger="is func"):
            with self.assertLogs():
                with self.assertRaises(expected_exception):
                    # Actual operation
                    with decorator_cm(prelog=prelogger_func):
                        undecorated_func()

    def test_decorator_prelogger_logs_before_expected_log_record(self):
        decorator_cm = pkg_logging.log_and_reraise
        expected_exception = ValueError
        expected_exception_str = "generic message"

        def undecorated_func():
            raise expected_exception(expected_exception_str)

        prelogger_str = "This message before a Critical"

        with self.assertLogs() as captured:
            with self.assertRaises(expected_exception):
                # Actual operation
                with decorator_cm(prelog=prelogger_str):
                    undecorated_func()
            self.assertEqual(len(captured.output), 2)
            line_0, line_1 = captured.output
            self.assertIn(prelogger_str, line_0)
            self.assertIn(expected_exception_str, line_1)

    def test_decorator_can_suppress_specified_exceptions(self):
        decorator_cm = pkg_logging.log_suppress_or_reraise
        to_suppress = TypeError

        @decorator_cm(to_suppress)
        def decorated_func():
            raise to_suppress("generic message")

        def undecorated_func():
            raise to_suppress("generic message")

        with self.subTest(implementation="context manager"):
            with self.assertLogs():
                try:
                    with decorator_cm(to_suppress):
                        undecorated_func()
                except to_suppress:
                    passes_test = False
                else:
                    passes_test = True
            self.assertTrue(passes_test)

        with self.subTest(implementation="decorator"):
            with self.assertLogs():
                try:
                    decorated_func()
                except to_suppress:
                    passes_test = False
                else:
                    passes_test = True
            self.assertTrue(passes_test)

    def test_decorator_can_raises_unspecified_exceptions(self):
        decorator_cm = pkg_logging.log_suppress_or_reraise
        to_suppress = TypeError
        unexpected_exc = ValueError

        @decorator_cm(to_suppress)
        def decorated_func():
            raise unexpected_exc("generic message")

        def undecorated_func():
            raise unexpected_exc("generic message")

        with self.subTest(implementation="context manager"):
            with self.assertLogs():
                with self.assertRaises(unexpected_exc):
                        with decorator_cm(to_suppress):
                            undecorated_func()

        with self.subTest(implementation="decorator"):
            with self.assertLogs():
                with self.assertRaises(unexpected_exc):
                        decorated_func()

    def test_decorator_logs_package_exceptions_as_errors(self):
        decorator = pkg_logging.log_and_reraise
        expected_exception = exceptions.RecomposeError
        logger = self.logging_builtin.getLogger("exampleLogger")

        @decorator(logger)
        def example_func():
            raise expected_exception("generic error message")

        self.check_decorator(func=example_func,
                             level="ERROR",
                             exception_type=expected_exception)

    def test_decorator_logs_package_warnings_as_warnings(self):
        decorator = pkg_logging.log_and_reraise
        expected_exception = exceptions.RecomposeWarning
        logger = self.logging_builtin.getLogger("exampleLogger")

        @decorator(logger)
        def example_func():
            raise expected_exception("generic warning message")

        self.check_decorator(func=example_func,
                             level="WARNING",
                             exception_type=expected_exception)

    def test_decorator_logs_nonpackage_exceptions_as_critical(self):
        decorator = pkg_logging.log_and_reraise
        expected_exception = ValueError
        logger = self.logging_builtin.getLogger("exampleLogger")

        @decorator(logger)
        def example_func():
            raise expected_exception("ValueError message")

        self.check_decorator(func=example_func,
                             level="CRITICAL",
                             exception_type=expected_exception)

    def check_decorator(self, func=None, level=None, exception_type=None):
        with self.assertLogs() as captured:
            with self.assertRaises(exception_type):
                func()
        self.assertEqual(len(captured.records), 1)
        log_event = captured.records[0]
        self.assertEqual(log_event.levelname, level)


class Test_LoggerWrapper(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.message = f"Message from {cls.__name__}."
        cls.default_log_filename = pkg_logging.default_log_filename()
        cls.coded_levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30,
                            "ERROR": 40, "CRITICAL": 50}
        cls.recorded_names = set()

    def setUp(self):
        while True:
            unique_name = "loggerRandom#" + str(int(random.random() * 10e6))
            if unique_name not in self.recorded_names:
                self.recorded_names.add(unique_name)
                break
        self.random_name = unique_name

    def tearDown(self):
        if os.path.exists(self.default_log_filename):
            os.remove(self.default_log_filename)

    def test_wrapped_logger_has_original_logger(self):
        import logging
        logger = logging.getLogger()
        logger_attr = "logger"

        wrapped_logger = pkg_logging.LoggerWrapper(logger)

        self.assertHasAttr(wrapped_logger, logger_attr)
        self.assertIs(getattr(wrapped_logger, logger_attr), logger)

    def test_wrapped_logger_shares_interface(self):
        import logging
        logger = logging.getLogger()
        attrs = ("debug info warning error critical exception "
                 "name level").split()

        wrapped_logger = pkg_logging.LoggerWrapper(logger)

        for attr in attrs:
            with self.subTest(expected_attr=attr):
                self.assertHasAttr(logger, attr, msg="Precondition!")
                self.assertHasAttr(wrapped_logger, attr)

    def test_wrapped_logger_logs(self):
        import logging
        logger = logging.getLogger()
        levels = "DEBUG INFO WARNING ERROR CRITICAL".split()

        wrapped_logger = pkg_logging.LoggerWrapper(logger)
        # Preconditon: agnostic of logger setting, essentially tests the
        # handlers.
        pkg_logging.setLevel("DEBUG")

        for level in levels:
            with self.subTest(level=level):
                self.wrapped_logger_logs(wrapped_logger, level)

    def test_wrapped_logger_logs_after_setup_by_level(self):
        self.assertFalse(os.path.exists(self.default_log_filename),
                         msg="Precondition.")

        pkg_logging.setup_logging()
        self.addCleanup(pkg_logging.finish_logging)
        levels = "DEBUG INFO WARNING ERROR CRITICAL".split()

        wrapped_logger = pkg_logging.getLogger()
        # Preconditon: agnostic of logger setting, essentially tests the
        # handlers.
        pkg_logging.setLevel("DEBUG")

        for level in levels:
            with self.subTest(level=level):
                self.wrapped_logger_logs(wrapped_logger, level)

    def test_wrapped_logger_logs_after_setup_to_destinations(self):
        self.assertFalse(os.path.exists(self.default_log_filename),
                         msg="Precondition.")
        levels = "DEBUG INFO WARNING ERROR CRITICAL".split()

        with testfixtures.OutputCapture(separate=True) as streams:
            pkg_logging.setup_logging()
            self.addCleanup(pkg_logging.finish_logging)

            wrapped_logger = pkg_logging.getLogger()
            # Preconditon: agnostic of logger setting, essentially tests the
            # handlers.
            pkg_logging.setLevel("DEBUG")

            for level in levels:
                wrapped_logger.log(self.coded_levels[level], self.message)

        with self.subTest(criteria="logs all levels to file"):
            self.wrapped_logger_has_logged_to_file(levels)

        with self.subTest(criteria="logs to stderr not stdout"):
            stdout = streams.stdout.getvalue().strip()
            stderr = streams.stderr.getvalue().strip()
            self.assertEqual(len(stdout), 0)
            self.assertGreaterEqual(len(stderr), 1)
            self.assertIn(self.message, stderr)

        with self.subTest(criteria="logs specific levels to stderr"):
            expected_levels = "ERROR CRITICAL".split()
            unexpected_levels = "DEBUG INFO WARNING ".split()
            self.assertSubstringsInString(expected_levels, stderr)
            self.assertSubstringsNotInString(unexpected_levels, stderr)

    def test_wrapped_logger_autologs_exceptions_specially(self):
        import logging
        logger = logging.getLogger(self.random_name)
        logger.setLevel("WARNING")
        msg = self.message
        msg_warn = msg + str(hash("WARNING"))
        msg_err = msg + str(hash("ERROR"))
        msg_crit = msg + str(hash("CRITICAL"))
        errors = {"ERROR": exceptions.RecomposeError(msg_warn),
                  "WARNING": exceptions.RecomposeWarning(msg_err),
                  "CRITICAL": Exception(msg_crit)}

        wrapped_logger = pkg_logging.LoggerWrapper(logger)

        for level, error in errors.items():
            with self.subTest(log_exc_expecting=error):
                with self.assertLogs() as captured:
                    wrapped_logger.autolog(error)
                expected = [level, str(error)]
                output = captured.output.pop()
                self.assertSubstringsInString(expected, output)


    def test_wrapped_logger_autologs_after_setup_exceptions_specially(self):
        pkg_logging.setup_logging()
        self.addCleanup(pkg_logging.finish_logging)
        msg = self.message
        errors = {"ERROR": exceptions.RecomposeError(msg),
                  "WARNING": exceptions.RecomposeWarning(msg),
                  "CRITICAL": Exception(msg)}

        wrapped_logger = pkg_logging.getLogger()

        for level, error in errors.items():
            with self.subTest():
                with self.assertLogs(wrapped_logger.logger):
                    wrapped_logger.autolog(error)


    def test_wrapped_logger_autologs_nonExceptions_with_logger_level(self):
        expected_level = "WARNING"
        import logging
        logger = logging.getLogger(self.random_name)
        logger.setLevel(expected_level)

        wrapped_logger = pkg_logging.LoggerWrapper(logger)

        self.assertEqual(wrapped_logger.level,
                         self.coded_levels.get(expected_level),
                         msg="Precondition")
        with self.assertLogs(logger=wrapped_logger.logger, level=expected_level):
            wrapped_logger.autolog(self.message)

    def test_wrapped_logger_autologs_nonExceptions_with_specified_level(self):
        expected_level = "DEBUG"
        import logging
        logger = logging.getLogger(self.random_name)

        wrapped_logger = pkg_logging.LoggerWrapper(logger)

        self.assertNotEqual(wrapped_logger.level,
                            self.coded_levels.get(expected_level),
                            msg="Precondition")
        with self.assertLogs(logger=wrapped_logger.logger, level=expected_level):
            wrapped_logger.autolog(self.message, level=expected_level)

    def test_getLogger_returns_wrapped_logger(self):
        import logging
        pkg_logging.setup_logging()
        self.addCleanup(pkg_logging.finish_logging)

        logger = pkg_logging.getLogger()

        self.assertIsInstance(logger, logging.LoggerAdapter)
        self.assertIsInstance(logger, pkg_logging.LoggerWrapper)

    def wrapped_logger_logs(self, logger, level):
        message = self.message
        encoded_level = self.coded_levels[level]
        if encoded_level >= logger.level:
            with self.assertLogs(logger.logger, level):
                logger.log(encoded_level, message)
        else:
            try:
                with self.assertLogs(logger.logger, level):
                    logger.log(encoded_level, message)
            except AssertionError:
                assertmsg = ""
            else:
                assertmsg = (f"Logger '{logger}' should not have logged "
                             "and yet it did.")
            if assertmsg:
                self.fail(assertmsg)

    def wrapped_logger_has_logged_to_file(self, levels):
        self.assertTrue(os.path.exists(self.default_log_filename),
                        msg="Precondition")
        with open(self.default_log_filename) as handle:
            text = handle.read()
        self.assertSubstringsInString(set(levels), text)
        counter = collections.Counter(levels)
        for level, expected_count in counter.items():
            with self.subTest(counting_records=f"{level} -> {expected_count}"):
                self.assertEqual(text.count(level), expected_count)


class Test_Logging_Runtime_Behaviour(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_file = getattr(pkg_logging, "__CONFIG_FILE")

    def setUp(self):
        super().setUp()
        self.remove_these = []

    def tearDown(self):
        super().tearDown()
        for file in self.remove_these:
            if os.path.exists(file):
                os.remove(file)

    def get_log_filename(self, logger):
        catch_type = self.logging_builtin.FileHandler
        output = [h.baseFilename for h in logger.handlers
                      if isinstance(h, catch_type)]
        filename = output.pop()
        self.remove_these.append(filename)
        return filename

    def test_recomposeLogger_correct_destinations(self):

        # Expected values
        debug_msg = "1debug1"
        info_msg = "2info2"
        warning_msg = "3warning3"
        error_msg = "4error4"
        should_be_in_stderr = [error_msg]
        should_be_in_logfile = [error_msg, warning_msg, info_msg, debug_msg]

        with testfixtures.OutputCapture(separate=True) as output:
            # Setup logging
            self.logging_builtin_config.fileConfig(self.config_file,
                disable_existing_loggers=True
                )
            logger = self.logging_builtin.getLogger("recomposeLogger")
            # Set the level to DEBUG as we want to just test the handlers.
            logger.setLevel(10)
            # Do logging
            logger.debug(debug_msg)
            logger.info(info_msg)
            logger.warning(warning_msg)
            logger.error(error_msg)
        # Logging postcondition
        logfile = self.get_log_filename(logger)
        stderr = output.stderr.getvalue().strip()
        stdout = output.stdout.getvalue().strip()

        # Test for stdout
        with self.subTest(output="stdout"):
            self.assertEqual(stdout, "")

        # Test for stderr
        with self.subTest(output="stderr"):
            self.assertSubstringsInString(should_be_in_stderr, stderr)

        # Test for logfile
        self.logging_builtin.shutdown()
        with self.subTest(output=os.path.basename(logfile)):
            self.assertTrue(os.path.isfile(logfile))
            with open(logfile) as handle:
                lines = handle.readlines()
                length = len(lines)
                log_lines = "".join(lines).strip()
            self.assertSubstringsInString(should_be_in_logfile, log_lines,
                                          msg=f"Looking in {logfile}")
            self.assertEqual(length, len(should_be_in_logfile))
