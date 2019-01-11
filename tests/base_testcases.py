#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""A collection of classes that unittest.TestCase and correct main package importing.

Copyright: Ian Vermes 2019
"""

import tests.context

import unittest
import shlex
import subprocess
import os

# To allow consistent imports of pkg modules
tests.context.main()


class BaseTestCase(unittest.TestCase):
    """Base testcase for the suite."""

    def assertSubstringsInString(self, substrings, string, msg=None):
        # Precondition
        if isinstance(substrings, str):
            substrings = [substrings]  # Rather than raise a type error.
        if not substrings:
            errmsg = f"Positional argument 1 is invalid: {repr(substrings)}"
            raise ValueError(errmsg)
        if not string:
            errmsg = f"Positional argument 2 is invalid: {repr(string)}"
            raise ValueError(errmsg)
        # Main loop
        absent = [sub for sub in substrings if sub not in string]
        if len(absent) > 0:
            # The assertion has failed: some/all substrings absent from string
            def spaceing(n_spaces):
                return "\n" + " " * n_spaces
            detail = "".join([(spaceing(8) + "- " + s) for s in absent])
            errmsg = (f"{len(substrings) - len(absent)} out of "
                      f"{len(substrings)} substrings were found in the string."
                      f"{spaceing(4)}Unexpectly missing:"
                      f"{detail}")
            if msg:
                errmsg = errmsg + f"{spaceing(4)}Custom message : {msg}"
            raise AssertionError(errmsg)
        elif len(absent) == 0:
            # The assertion has passed: all substrings in string
            return

    def assertFileInDirectory(self, file, directory, msg=None):
        assert_method = "in"
        self._fileInOrNotInDirectory(file, directory,
                                     method=assert_method, msg=msg)

    def assertFileNotInDirectory(self, file, directory, msg=None):
        assert_method = "not in"
        self._fileInOrNotInDirectory(file, directory,
                                     method=assert_method, msg=msg)

    def _fileInOrNotInDirectory(self, file, directory, method, msg=None):
        # Preconditions
        if not file:
            errmsg = f"Filename is not valid: {repr(file)}."
            if file == "":
                errmsg += "Empty strings are forbidden."
            elif file is None:
                raise TypeError(errmsg)
            raise ValueError(errmsg)

        if not directory:
            directory = "."
        # Main
        funcs = {"in": self.assertIn, "not in": self.assertNotIn}
        try:
            assertion_func = funcs[method]
        except KeyError:
            errmsg = (f"Illegal value method={repr(method)}. Use 'in' for "
                       "self.assertIn or 'not in' for self.assertNotIn.")
            raise ValueError(errmsg)

        files = set(os.path.basename(f) for f in os.listdir(directory))
        file_basename = os.path.basename(file)
        if msg is not None:
            assertion_func(file_basename, files, msg=msg)
        else:
            assertion_func(file_basename, files)



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
