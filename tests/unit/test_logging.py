#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of main/helpers/logging.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import LoggingTestCase

import helpers.logging
import exceptions

import testfixtures

import os
import configparser
import unittest
import tempfile


def tearDownModule():
    logdir = "./logs"
    for file in os.listdir(logdir):
        os.remove(os.path.join(logdir, file))

class Test_Logging_Setup(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_file = getattr(helpers.logging, "__CONFIG_FILE")

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
        global_default_logfilename = getattr(helpers.logging, "__DEFAULT_LOGFILENAME")

        is_valid_dir = os.path.isdir(os.path.dirname(global_default_logfilename))

        self.assertTrue(is_valid_dir, msg=("Could not find the directory that "
                                           f"{global_default_logfilename} "
                                           "would reside in."))


class Test_HelperLogging_Runtime_Behaviour(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        config_file = getattr(helpers.logging, "__CONFIG_FILE")
        cls.config = config = configparser.ConfigParser()
        cls.config.read(config_file)
        cls.config_default_log = config.get(config.default_section,
                                            "logfilename")
        cls.module_default_log = getattr(helpers.logging,
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
        self.assertFalse(os.path.exists(self.config_default_log))
        self.assertFalse(os.path.exists(self.module_default_log))
        if other_file is not None:
            self.assertFalse(os.path.exists(other_file))

    def test_setup_function_overloads_config_logfilename_DEFAULT(self):
        self.precondition()
        expected = self.module_default_log
        self.remove_these.append(expected)

        with testfixtures.OutputCapture() as _:
            helpers.logging.setup_logging()
            helpers.logging.finish_logging()

        self.assertFalse(os.path.exists(self.config_default_log))
        self.assertTrue(os.path.exists(expected))

    def test_setup_function_overloads_config_logfilename_USERCHOICE(self):

        with tempfile.TemporaryDirectory() as dirname:
            user_defined_logfilename = os.path.join(dirname, "foobar.log")
            self.precondition(other_file=user_defined_logfilename)

            with testfixtures.OutputCapture() as _:
                helpers.logging.setup_logging(user_defined_logfilename)
                helpers.logging.finish_logging()

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
            helpers.logging.setup_logging(bad_logfilename)
        helpers.logging.finish_logging()
        self.assertSubstringsInString(expected_substrings, str(fail.exception))

    def test_decorator_raises_exceptions(self):
        decorator = helpers.logging.log_and_reraise
        expected_exception = ValueError

        @decorator()
        def example_func():
            raise expected_exception("generic message")

        with self.assertRaises(expected_exception):
            with self.assertLogs():
                example_func()

    def test_decorator_logs_package_exceptions_as_errors(self):
        decorator = helpers.logging.log_and_reraise
        expected_exception = exceptions.RecomposeError
        logger = self.logging_builtin.getLogger("exampleLogger")

        @decorator(logger)
        def example_func():
            raise expected_exception("generic error message")

        self.check_decorator(func=example_func,
                             level="ERROR",
                             exception_type=expected_exception)

    def test_decorator_logs_package_warnings_as_warnings(self):
        decorator = helpers.logging.log_and_reraise
        expected_exception = exceptions.RecomposeWarning
        logger = self.logging_builtin.getLogger("exampleLogger")

        @decorator(logger)
        def example_func():
            raise expected_exception("generic warning message")

        self.check_decorator(func=example_func,
                             level="WARNING",
                             exception_type=expected_exception)

    def test_decorator_logs_nonpackage_exceptions_as_critical(self):
        decorator = helpers.logging.log_and_reraise
        expected_exception = ValueError
        logger = self.logging_builtin.getLogger("exampleLogger")

        @decorator(logger)
        def example_func():
            raise expected_exception("ValueError message")

        self.check_decorator(func=example_func,
                             level="CRITICAL",
                             exception_type=expected_exception)

    def check_decorator(self, func=None, level=None, exception_type=None):
        with self.assertRaises(exception_type):
            with self.assertLogs() as captured:
                func()
        self.assertEqual(len(captured.records), 1)
        log_event = captured.records[0]
        self.assertEqual(log_event.levelname, level)


class Test_Logging_Runtime_Behaviour(LoggingTestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_file = getattr(helpers.logging, "__CONFIG_FILE")

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
