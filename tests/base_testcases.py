#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""A collection of classes that unittest.TestCase and correct main package importing.

Copyright: Ian Vermes 2019
"""

import tests.context

import unittest
import shlex
import subprocess

# To allow consistent imports of pkg modules
tests.context.main()


class BaseTestCase(unittest.TestCase):
    """Base testcase for the suite."""

    def assertFileInDirectory(self, file, directory, msg=None):
        pass

    def assertFileNotInDirectory(self, file, directory, msg=None):
        pass


class CommandLineTestCase(BaseTestCase):

    def invoke_cmd_via_commandline(self, cmd, expected_status):
        """Collects the stdout when invoking and validates the exit status."""
        status, stdout = subprocess.getstatusoutput(cmd)

        if expected_status == 0:
            self.assertEqual(status, 0,
                             msg=f"'$ {cmd}': did not exit cleanly/validly.")
        elif 0 < expected_status < 3:
            self.assertGreater(status, 0,
                               msg=(f"'$ {cmd}': should have exited with an "
                                    "error but exited cleanly."))
        else:
            msg = (f"Got expected_status={repr(expected_status)}, "
                   "not int: 0 <= i < 3.")
            raise ValueError(msg)

        return stdout

    @classmethod
    def format_cmd(cls, cmd_template, template_kwargs):
        """Create a safe commandline command."""
        # Precondition 1
        curly_left = cmd_template.count(r"{")
        curly_right = cmd_template.count(r"}")
        key_count = len(template_kwargs)
        if curly_left != curly_right or key_count != curly_left:
            msg = ("The command template is formatted using 'new' Python "
                   "formatting and hence expects curly bracket notaion. "
                   "Furthermore, the number of substrings to inject in to the "
                   "template must match the number of positions for insertion.")
            raise TypeError(msg)

        # Precondition 2
        prefixes = ("file", "dir")
        bad_keys = []
        for key in template_kwargs:
            if any([key.startswith(p) for p in prefixes]):
                template_kwargs[key] = shlex.quote(template_kwargs.get(key))
            else:
                bad_keys.append(key)
        if bad_keys:
            msg = ("Template formating expects a dictionary with keys that "
                   f"start with '{prefixes}' but got the following bad keys: "
                   f"{repr(bad_keys)}")
            raise TypeError(msg)

        cmd = cmd_template.format(**template_kwargs)
        return cmd
