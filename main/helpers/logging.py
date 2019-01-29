#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Logging function for Recompose.

Copyright: Ian Vermes 2019
"""

import os
import logging
import sys

__CONFIG_FILE = "../../logger_setup.cfg"
__CONFIG_FILE = os.path.relpath(os.path.join(__file__, __CONFIG_FILE))
