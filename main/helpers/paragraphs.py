#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Various paragraph processing classes for Recompose.

PreProcessed - class that converts a paragraph element into 3 major substrings.
PostProcessed - class that validates and extracts data from a preprocessed obj.

Copyright: Ian Vermes 2019
"""

import exceptions
from helpers import xml

from lxml import etree
