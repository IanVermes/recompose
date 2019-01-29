#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Logging function for Recompose.

Copyright: Ian Vermes 2019
"""

import os
import logging
import sys


def _get_relpath_relative_to_this_py(filename):
    relative = os.path.join(__file__, filename)
    relative = os.path.relpath(relative)
    return relative

__CONFIG_FILE = _get_relpath_relative_to_this_py("../../logger_setup.cfg")
__DEFAULT_LOGFILENAME = _get_relpath_relative_to_this_py("../../../logs/recompose.log")
