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

import itertools
import operator


class PreProcessed(object):

    _xpaths = None
    _allowed_pattern = (False, True, False)
    __query_r_elements = "w:r[descendant::w:t]"
    __query_bool_r_descendant_italic = "boolean(count(w:rPr/w:i) > 0)"
    __query_bool_node_is_paragraph = "(name() = 'w:p')"
    __query_bool_node_has_italic_and_text = ("(count(descendant::w:i) > 0) "
                                             "and "
                                             "(count(descendant::w:t) > 0)")
    __query_bool_node_proceded_italic = ("boolean(preceding-sibling::*//w:i "
                                         "and "
                                         ".//*[count(w:i) = 0])")
    __query_text_from_t = "w:t/text()"

    def __init__(self, paragraph):
        self.__paragraph = self._check_init_arg(paragraph)
        self.__pre_italic = None
        self.__italic = None
        self.__post_italic = None
        self.is_valid_italic_pattern(fatal=True)
        self.identify_substrings()

    def __str__(self):
        string = "".join([self.__pre_italic, self.__italic, self.__post_italic])
        string = string.strip()
        return string

    def _check_init_arg(self, paragraph):
        if not isinstance(paragraph, etree._Element):
            msg = f"Arg is not etree._Element type but {type(paragraph)}."
            raise TypeError(msg)
        # XPaths is set class wide and if XPaths was assigned by another
        # instance its left alone.
        self._set_xpaths(paragraph)
        # Check if element is paragraph and otherwise suitable
        tag_italic_query = self.__query_bool_node_has_italic_and_text
        current_element_query = self.__query_bool_node_is_paragraph
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

    def identify_substrings(self):
        element = self.__paragraph
        pre, italic, post = self._identify_substrings(element)
        self.__pre_italic = pre
        self.__italic = italic
        self.__post_italic = post

    @classmethod
    def _identify_substrings(cls, element, _memoize=True):

        def get_text(cls, subsequence, xpaths):
            find_text = xpaths.get(cls.__query_text_from_t)
            strings = (find_text(r_tag) for r_tag in subsequence)
            strings = itertools.chain.from_iterable(strings)
            return "".join(strings)

        if not _memoize:
            xpaths = xml.XPaths(element)
        elif cls._xpaths is None:
            xpaths = xml.XPaths(element)
        else:
            xpaths = cls._xpaths
        # Partition r elements into has italic & not-italic
        find_r_elems = xpaths.get(cls.__query_r_elements)
        r_elems = find_r_elems(element)
        is_italic = xpaths.get(cls.__query_bool_r_descendant_italic)
        packed_iters = cls._partition(is_italic, iterable=r_elems)
        r_non_italic, r_italic = packed_iters
        # Partition non-italic r elements into before and after italic
        is_after_italic = xpaths.get(cls.__query_bool_node_proceded_italic)
        packed_iters = cls._partition(is_after_italic, iterable=r_non_italic)
        r_non_italic_pre, r_non_italic_post = packed_iters
        # Generate text from iters
        pre_string = get_text(cls, r_non_italic_pre, xpaths)
        italic_string = get_text(cls, r_italic, xpaths)
        post_string = get_text(cls, r_non_italic_post, xpaths)
        return pre_string, italic_string, post_string

    def get_italic_pattern(self):
        element = self.__paragraph
        return self._get_italic_pattern(element)

    @classmethod
    def _get_italic_pattern(cls, element, _memoize=True):
        if not _memoize:
            xpaths = xml.XPaths(element)
        elif cls._xpaths is None:
            xpaths = xml.XPaths(element)
        else:
            xpaths = cls._xpaths
        # xpaths = xml.XPaths(element)
        find_r_elems_with_text = xpaths.get(cls.__query_r_elements)
        r_elements = find_r_elems_with_text(element)
        has_italic_child = xpaths.get(cls.__query_bool_r_descendant_italic)
        pattern = tuple(map(has_italic_child, r_elements))
        return pattern

    def is_valid_italic_pattern(self, fatal=False):
        element = self.__paragraph
        return self._is_valid_italic_pattern(element, fatal=fatal)

    @classmethod
    def _is_valid_italic_pattern(cls, element, fatal=False, _memoize=True):

        def format_detail(pattern):
            mapping = {True: "italic", False: "non-italic"}
            return ", ".join([mapping[b] for b in pattern])

        pattern = cls._get_italic_pattern(element, _memoize=_memoize)
        simple_pattern = tuple(cls._unique_justseen(pattern))
        is_valid = simple_pattern == cls._allowed_pattern
        if fatal and not is_valid:
            try:
                detail = format_detail(simple_pattern)
                err = exceptions.ParagraphItalicPatternWarning(detail=detail)
            except ValueError:
                print(f"*** simple_pattern: {repr(simple_pattern)}")
                print(f"*** pattern: {repr(pattern)}")
                print(f"*** detail: {repr(detail)}")
                raise
            raise err
        else:
            return is_valid

    @staticmethod
    def _unique_justseen(iterable, key=None):
        """List unique elements, preserving order. Remember only the element just seen."""
        return map(next, map(operator.itemgetter(1), itertools.groupby(iterable, key)))

    @staticmethod
    def _partition(pred, iterable):
        'Use a predicate to partition entries into false entries and true entries'
        # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
        t1, t2 = itertools.tee(iterable)
        return itertools.filterfalse(pred, t1), filter(pred, t2)

    @classmethod
    def _set_xpaths(cls, element):
        if cls._xpaths is None:
            cls._xpaths = xml.XPaths(element)

    @property
    def xpaths(self):
        return self._xpaths

    @property
    def pre_italic(self):
        return self.__pre_italic.strip()

    @property
    def italic(self):
        return self.__italic.strip()

    @property
    def post_italic(self):
        return self.__post_italic.strip()
