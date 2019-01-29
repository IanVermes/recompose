#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Unit test of main/helpers/logging.py.

Copyright: Ian Vermes 2019
"""
from tests.base_testcases import BaseTestCase

import helpers.logging

import testfixtures

import os
import configparser
import unittest


def tearDownModule():
    logdir = "./logs"
    for file in os.listdir(logdir):
        os.remove(os.path.join(logdir, file))

class Test_Logging_Setup(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_file = getattr(helpers.logging, "__CONFIG_FILE")

    def setUp(self):
        import logging
        import logging.config
        self.logging_builtin = logging
        self.logging_builtin_config = logging.config

    def tearDown(self):
        self.logging_builtin.shutdown()


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


class Test_Logging_Runtime_Behaviour(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_file = getattr(helpers.logging, "__CONFIG_FILE")

    def setUp(self):
        import logging
        import logging.config
        self.logging_builtin = logging
        self.logging_builtin_config = logging.config
        self.remove_these = []

    def tearDown(self):
        self.logging_builtin.shutdown()
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
