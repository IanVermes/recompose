#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Various paragraph processing classes for Recompose.

PreProcessed - class that converts a paragraph element into 3 major substrings.
PostProcessed - class that validates and extracts data from a preprocessed obj.

Other classes/funcs:
    get_paragraph_head
    process_paragraphs

Copyright: Ian Vermes 2019
"""

import exceptions
from helpers.strformat import makeItalic
from helpers import xml
from helpers import logging as pkg_logging

from lxml import etree

import itertools
import operator
import textwrap
from functools import partial


class PreProcessed(object):

    _xpaths = None
    _allowed_pattern = (False, True, False)
    __query_r_elements = "w:r[descendant::w:t]"
    __query_bool_r_descendant_italic = "boolean(count(w:rPr/w:i) > 0)"
    __query_bool_r_descendant_caps = "boolean(count(w:rPr/w:smallCaps) > 0)"
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
    def _get_string_from_r_elem_sequence(cls, r_sequence, xpaths):
        """Get and join the text tags from a in iterable of w:r elements.

        Does not consider if r elements are contiguous or otherwise.
        """
        def find_text(cls, r_elem, xpaths):
            get_text = xpaths.get(cls.__query_text_from_t)
            is_smallCaps = xpaths.get(cls.__query_bool_r_descendant_caps)
            strings = get_text(r_elem)
            if is_smallCaps(r_elem):
                strings = (s.upper() for s in strings)
            else:
                strings = iter(strings)
            return strings

        strings = (find_text(cls, r, xpaths) for r in r_sequence)
        strings = itertools.chain.from_iterable(strings)
        return "".join(strings)

    @classmethod
    def _identify_substrings(cls, element, _memoize=True):

        if not _memoize:
            xpaths = xml.XPaths(element)
        elif cls._xpaths is None:
            xpaths = xml.XPaths(element)
        else:
            xpaths = cls._xpaths

        get_string = cls._get_string_from_r_elem_sequence

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
        pre_string = get_string(r_non_italic_pre, xpaths)
        italic_string = get_string(r_italic, xpaths)
        post_string = get_string(r_non_italic_post, xpaths)
        return pre_string, italic_string, post_string

    def get_italic_pattern(self):
        element = self.__paragraph
        return self._get_italic_pattern(element)

    @classmethod
    def _get_italic_pattern(cls, element, _memoize=True):
        # _memoize kwarg + boiler plate is there to support unittesting
        if not _memoize:
            xpaths = xml.XPaths(element)
        elif cls._xpaths is None:
            xpaths = xml.XPaths(element)
        else:
            xpaths = cls._xpaths

        find_r_elems_with_text = xpaths.get(cls.__query_r_elements)
        r_elements = find_r_elems_with_text(element)
        has_italic_child = xpaths.get(cls.__query_bool_r_descendant_italic)
        pattern = tuple(map(has_italic_child, r_elements))
        return pattern

    def is_valid_italic_pattern(self, fatal=False):
        element = self.__paragraph
        italic = True
        return self._is_valid_italic_pattern(element,
                                             fatal=fatal,
                                             _font=italic)

    @classmethod
    def _is_valid_italic_pattern(cls, element, fatal=False, _memoize=True, _font=False):
        # _memoize kwarg + boiler plate is there to support unittesting

        def annotate_italic_space(index, groups):
            _, string = groups[index]
            repl = string.replace(" ", chr(9251))  # OPEN BOX
            context_length = 15
            spaceing = " " * 8
            ellipsis = "..."

            index_leftright = (index - 1, index + 1)
            leftright = []
            for i in index_leftright:
                try:
                    _, context = groups[i]
                except IndexError:
                    _, context = ""
                leftright.append(context)
            left, right = leftright
            reversed_left = left[::-1]
            left = textwrap.shorten(reversed_left, context_length,
                                    placeholder=ellipsis)[::-1]
            right = textwrap.shorten(right, context_length,
                                     placeholder=ellipsis)
            annotation = f"{spaceing}# SPACE! {left}{repl}{right}"
            return annotation

        def format_detail(groups, font=False):
            mapping = {True: "italic", False: "non-italic"}
            spaceing = " " * 4
            detail_pattern = []
            detail_faults = []
            bullet_template = "{i:<2d})"
            j = 0
            for i, (is_italic, string) in enumerate(groups):
                detail_pattern.append(mapping[is_italic])
                if is_italic:
                    j += 1
                    if font:
                        new_string = makeItalic(string)
                    else:
                        new_string = string
                    if string.isspace():
                        annotation = annotate_italic_space(i, groups)
                    else:
                        annotation = ""
                    bullet = bullet_template.format(i=j)
                    detail_faults.append((f"{spaceing}{bullet} italic: "
                                          f"{new_string}{annotation}"))

            detail_pattern = ", ".join(detail_pattern)
            detail_faults = "\n".join(detail_faults)
            detail = f"{detail_pattern}. Faults:\n{detail_faults}"
            return detail
        # Generate the simple pattern of the italics tags in the paragraph.
        # If they do not correspond to the expected pattern, raise a
        # detailed error.
        pattern = cls._get_italic_pattern(element, _memoize=_memoize)
        simple_pattern = tuple(cls._unique_justseen(pattern))
        is_valid = simple_pattern == cls._allowed_pattern
        if fatal and not is_valid:
            groups = cls._group_contiguous_text_by_font(element)
            detail = format_detail(groups, _font)
            err = exceptions.ParagraphItalicPatternWarning(detail=detail)
            raise err
        else:
            return is_valid

    @classmethod
    def _group_contiguous_text_by_font(cls, element, _memoize=True):
        # _memoize kwarg + boiler plate is there to support unittesting
        if not _memoize:
            xpaths = xml.XPaths(element)
        elif cls._xpaths is None:
            xpaths = xml.XPaths(element)
        else:
            xpaths = cls._xpaths

        find_r_elems = xpaths.get(cls.__query_r_elements)
        r_elems = find_r_elems(element)
        is_italic = xpaths.get(cls.__query_bool_r_descendant_italic)
        # Group r elements into italic & not-italic stretches
        stretches = []
        for italicflag, r_group in itertools.groupby(r_elems, key=is_italic):
            r_string = cls._get_string_from_r_elem_sequence(r_group, xpaths)
            flagged_string = (italicflag, r_string)
            stretches.append(flagged_string)
        return stretches

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

    @classmethod
    def _reset_xpaths(cls):
        """Principally called by unittest suite."""
        cls._xpaths = None


def process_paragraphs(paragraph_elements):
    logger = pkg_logging.getLogger()
    prelog_len = 30
    for i, element in enumerate(paragraph_elements, start=1):
        prelog = partial(get_paragraph_head, element, prelog_len, bullet_num=i)
        try:
            with pkg_logging.log_and_reraise(logger, prelog=prelog):
                pre = PreProcessed(element)
        except exceptions.RecomposeWarning:
            continue
        else:
            pass



def get_paragraph_head(source, maxlength, bullet_num=-1, bullet=False):
    """Return the paragraph text of specific length, optionally prefix a bullet.

    Args:
        source(str, PreProcessed, etree._Element)
        maxlength(int)
    Kwargs:
        bullet(bool): False by default, otherwise prefix paragraph text with
                      either '* )' or '##)' where # corresponds to a zero padded
                      integer.
        bullet_num(int): By default, the bullet is un-numerated, otherwise it
                         will take the bullet number.
    """
    if bullet_num > -1:
        bullet = True
    if not bullet:
        bullet_s = ""
    else:
        if bullet_num < 0:
            bullet_s = "* ) "
        else:
            bullet_s = f"{bullet_num:02d}) "

    if isinstance(source, PreProcessed):
        string = str(source.pre_italic)
    elif isinstance(source, etree._Element):
        string = source.xpath("string()")
    # TODO PostProcessed condition
    else:
        string = str(source)
    string = f"{bullet_s}{string}"
    if maxlength != 30:
        print(f"*** maxlength: {maxlength}")
    short = textwrap.shorten(string, width=maxlength, placeholder=" ...")
    return short
