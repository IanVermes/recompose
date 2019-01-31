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


class PreProcessed(object):

    _xpaths = None

    def __init__(self, paragraph):
        self.__paragraph = self._check_init_arg(paragraph)

    def _check_init_arg(self, paragraph):
        if not isinstance(paragraph, etree._Element):
            msg = f"Arg is not etree._Element type but {type(paragraph)}."
            raise TypeError(msg)
        # Check if element is paragraph and otherwise suitable
        tag_italic_query = ("(count(descendant::w:i) > 0) and "
                               "(count(descendant::w:t) > 0)")
        current_element_query = "(name() = 'w:p')"
        # query = f"({current_element_query} and {tag_italic_query})"
        if self.xpaths is None:
            self._set_xpaths(paragraph)
        has_italic_and_text = self.xpaths.get(tag_italic_query)
        has_italic_and_text = has_italic_and_text(paragraph)
        is_paragraph_node = self.xpaths.get(current_element_query)
        is_paragraph_node = is_paragraph_node(paragraph)
        flags = (has_italic_and_text, is_paragraph_node)
        if all(flags):
            return paragraph
        else:
            elem_name = paragraph.xpath('name()')
            details = {
             (False, False): (f"{self.__class__.__name__} as it has neither "
                              "italic nor text tags and is not a w:p "
                              f"but {elem_name}"),
             (True, False): (f"{self.__class__.__name__} as it is not a w:p "
                             f"element but {elem_name}"),
             (False, True): f"{self.__class__.__name__} as it has neither "
                            "italic nor text tags)"}
            detail = details[flags]
            raise exceptions.PreProcessedValueError(detail=detail)

    @classmethod
    def _set_xpaths(cls, element):
        cls._xpaths = xml.XPaths(element)

    @property
    def xpaths(self):
        return self._xpaths
