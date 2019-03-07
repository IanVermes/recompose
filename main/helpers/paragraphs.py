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
import re
import abc
import operator
import textwrap
from functools import partial


class Processor(abc.ABC):
    """Abstract/base class for Processor subclasses."""
    # Tokens used in subclasses
    _COMMA = ","
    _COMMASPACE = ", "
    _OXFORDCOMMA = ", and"
    _OXFORDAND = _OXFORDCOMMA + " "
    _VALID_REPORT = (0, "")
    _INVALID_PLACEHOLDER = (1, "DETAIL TO ADD TO EXCEPTION STRING")  # TODO
    _CONDITIONAL_METHOD = "_cond"

    def __init__(self, source):
        self._oktype = PreProcessed
        self._raw_string = self._init_precondition(source)
        for attr in self._data_attrs:
            super().__setattr__(attr, None)
        self._assign_values()

    def _init_precondition(self, source):
        try:
            # We resolve natural strings in the attribute error.
            raw_string = getattr(source, self._pre_attr_name)
            if not isinstance(raw_string, str):
                raise TypeError()
        except AttributeError:
            if isinstance(source, self._oktype):
                raise
            else:
                if isinstance(source, str):
                    raw_string = source
                else:
                    msg = ("Parameter must be a string or "
                           f"{self._oktype.__name__}.")
                    raise TypeError(msg) from None
        except TypeError:
            msg = (f"Value of {self._oktype.__name__}.{self._pre_attr_name} "
                   "is not a string. Got: {type(raw_string)}")
            raise TypeError(msg) from None
        if not raw_string:
            raise ValueError("Empty string.")
        return raw_string

    @abc.abstractmethod
    def isValid(self):
        """Subclasses need documentation but can super() the implmentation."""
        try:
            report = self._structure_report
        except AttributeError:
            self._isValid()
            report = self._structure_report
        # TODO Perhaps a different method called reportValiditiy or
        # reportStructure could handle the underlying set of tuple results.
        if len(report) > 1:
            return False
        else:
            return self._VALID_REPORT in report

    def __repr__(self):
        """In general: <classname raw: ... at 0x...>."""
        template = "<{name} raw:\'{raw}\' at {hexid}>"
        kwargs = {"name": self.__class__.__name__,
                  "raw": self._raw_string,
                  "hexid": hex(id(self))}
        return template.format(**kwargs)

    @abc.abstractmethod
    def _isValid(self):
        pass

    @abc.abstractmethod
    def _assign_values(self):
        pass

    @property
    def validation_results(self):
        results = set()
        try:
            report = self._structure_report
        except AttributeError:
            self._isValid()
            report = self._structure_report
        return results.union(report)

    @classmethod
    @abc.abstractmethod
    def split(cls, string):
        pass


class ProcessorAuthors(Processor):
    """Processor for authorial data from a string or PreProcessed object.

    POSTCONDITION: value assignment to data attributes is dependent on the
    validity of the argument string/PreProcessed object, otherwise the
    attributes take a fill value.

    Attr:
        authors
        editors
        validation_results

    Methods:
        isValid
        isEditor

    Class Methods:
        split
        strip_editor
    """
    _pre_attr_name = "pre_italic"
    _data_attrs = set("authors editors".split())

    @classmethod
    def strip_editor(cls, string):
        """Strip the editorial notation from a string.

        >>> string = "Roberts, Lilly-Ann, and J.R.R. Tolkein (eds),"
        >>> ProcessorAuthors.strip_editor(string)
        'Roberts, Lilly-Ann, and J.R.R. Tolkein '
        >>> string = "Roberts, Lilly-Ann (ed.),"
        >>> ProcessorAuthors.strip_editor(string)
        'Roberts, Lilly-Ann '
        """
        base_editor_pattern = r"\(ed[\.s]\)"  # TODO CODE SMELL
        pattern_is_positional_editor = rf"({base_editor_pattern}\,$)"
        rgx_positional_editor = re.compile(pattern_is_positional_editor)
        new_string = rgx_positional_editor.sub("", string)
        return new_string

    @classmethod
    def split(cls, string, join_first=True):
        """Split a string with authors and editorial notations into a list.

        Kwargs:
            join_first(bool): True, by default, the first author is returned as
                a single string. Otherwise, the first author is a tuple composed
                of a firstname(s) and surname, preserving the nascent structure
                of the input string.

        >>> string = "Roberts, Lilly-Ann, and J.R.R. Tolkein (eds),"
        >>> ProcessorAuthors.split(string)
        ['Lilly-Ann Roberts', 'J.R.R. Tolkein']
        >>> ProcessorAuthors.split(string, join_first=False)
        [('Lilly-Ann', 'Roberts'), 'J.R.R. Tolkein']
        """
        result = []
        string = string.strip()
        string = cls.strip_editor(string)
        string = string.strip().strip(cls._COMMA)
        # Split an author after the oxford comma, if there is one.
        other_auths, *last = string.rsplit(cls._OXFORDAND, maxsplit=1)
        # From the remainder split into firstauthor_name1, name2 and other auths
        split_once = other_auths.split(cls._COMMASPACE, maxsplit=2)
        first_surname, first_name, *other_auths = split_once
        # Process the first author
        first = first_name, first_surname
        if join_first:
            first = " ".join(first)
        result.append(first)
        # Process the remaining other_auths
        if other_auths:
            other_auths = other_auths.pop()
            other_auths = other_auths.split(cls._COMMASPACE)
        result = result + other_auths + last
        return result

    def isValid(self):
        """Boolean check: does object pass validation?

        >>> wrong = ProcessorAuthors("Wrong, Borris L. ed,")
        >>> wrong.isValid()
        False
        >>> write = ProcessorAuthors("Write, Borris L. (ed.),")
        >>> write.isValid()
        True
        """
        return super().isValid()

    def _isValid(self):
        self._structure_report = set()

        main_flag = self._maincond_count_commas()
        if main_flag:
            prefix = self._CONDITIONAL_METHOD
            cond_methods = [getattr(self, name) for name in dir(self)
                            if name.startswith(prefix)]
            iter_bool = (m() for m in cond_methods)
            secondary_flag = all([b for b in iter_bool if b is not None])
            flag = secondary_flag and main_flag
        else:
            flag = main_flag
        if flag:
            self._structure_report.add(self._VALID_REPORT)
            return flag
        else:
            return flag

    def isEditor(self):
        """Boolean check: does the object have the editorial notation?

        >>> roberts = ProcessorAuthors("Roberts, Lilly-Ann,")
        >>> roberts.isEditor()
        False
        >>> poe = ProcessorAuthors("Allan Poe, Edgar (ed.),")
        >>> poe.isEditor()
        True
        """
        try:
            flag = self._has_editors
        except AttributeError:
            self._cond_editors()
            flag = self._has_editors
        return flag

    def _assign_values(self):
        if self.isValid():
            if self.isEditor():
                self.editors = self.split(self._raw_string)
                self.authors = list()
            else:
                self.authors = self.split(self._raw_string)
                self.editors = list()
        else:
            for attr in self._data_attrs:
                super().__setattr__(attr, list())

    def _maincond_count_commas(self):
        count_comma = self.__count_commas()
        flag = count_comma >= 2
        # TODO injected error code/error detail is generic PLACEHOLDER
        if not flag:
            self._structure_report.add(self._INVALID_PLACEHOLDER)
        return flag

    def __count_commas(self):
        return self._raw_string.count(self._COMMA)

    def _cond_seperators_balance(self):
        count_comma = self.__count_commas()
        count_commaspace = self._raw_string.count(self._COMMASPACE)
        flag = count_comma - count_commaspace == 1
        # TODO injected error code/error detail is generic PLACEHOLDER
        if not flag:
            self._structure_report.add(self._INVALID_PLACEHOLDER)
        return flag

    def _cond_ok_oxford_comma(self):
        if self.__count_commas() > 2:
            string = self._raw_string.lower()
            flag = string.count(self._OXFORDCOMMA) == 1
            # TODO injected error code/error detail is generic PLACEHOLDER
            if not flag:
                self._structure_report.add(self._INVALID_PLACEHOLDER)
        else:
            # None value has to be filtered
            flag = None
        return flag

    def _cond_endswith_comma(self):
        flag = self._raw_string.endswith(self._COMMA)
        # TODO injected error code/error detail is generic PLACEHOLDER
        if not flag:
            self._structure_report.add(self._INVALID_PLACEHOLDER)
        return flag

    def _cond_editors(self):
        pattern_is_editor_fuzzy = r"([\(\ ][Ee][Dd][Ss\.]?)"
        base_editor_pattern = r"\(ed[\.s]\)"
        pattern_is_editor = f"({base_editor_pattern})"
        pattern_is_positional_editor = rf"({base_editor_pattern}\,$)"
        rgx_editor_fuzzy = re.compile(pattern_is_editor_fuzzy)
        rgx_editor = re.compile(pattern_is_editor)
        rgx_positional_editor = re.compile(pattern_is_positional_editor)  # TODO CODE SMELL

        string = self._raw_string
        flag_position = rgx_positional_editor.search(string) is not None  # TODO CODE SMELL
        flag_count_is_one = len(rgx_editor.findall(string)) == 1
        # Save calculation to assignment for isEditor to call.
        self._has_editors = flag_position and flag_count_is_one
        # Whether there is an editor pattern at the end or not does not rule out other
        # mistakes, hence check:
        structurally_sound = True
        structurally_flawed = False

        if flag_position:
            if flag_count_is_one:
                ## Editor notification legitimately present.
                return structurally_sound
            else:
                # TODO injected error code/error detail is generic PLACEHOLDER
                ## Editor notification appears too often, not just at end.
                self._structure_report.add(self._INVALID_PLACEHOLDER)
                return structurally_flawed
        elif not flag_position:
            if rgx_editor.search(string) is not None:
                # TODO injected error code/error detail is generic PLACEHOLDER
                ## Editor appears but not at end.
                self._structure_report.add(self._INVALID_PLACEHOLDER)
                return structurally_flawed
            elif rgx_editor_fuzzy.search(string) is not None:
                # TODO injected error code/error detail is generic PLACEHOLDER
                ## Something that looks like Editor appears.
                self._structure_report.add(self._INVALID_PLACEHOLDER)
                return structurally_flawed
            else:
                ## Editor notification legitimately absent.
                return structurally_sound

    def _cond_auth_length(self):
        sane_length = 40
        authors = self.split(self._raw_string, join_first=True)
        flags = [len(a) <= sane_length for a in authors]
        flag = all(flags)
        # TODO injected error code/error detail is generic PLACEHOLDER
        if not flag:
            self._structure_report.add(self._INVALID_PLACEHOLDER)
        return flag

    def _cond_rogue_and(self):
        bare_and = " and "
        oxford_and = self._OXFORDAND
        count = self._raw_string.count
        flag = count(bare_and) == count(oxford_and)
        # TODO injected error code/error detail is generic PLACEHOLDER
        ## Distinguish error for _cond_ok_oxford_comma
        if not flag:
            self._structure_report.add(self._INVALID_PLACEHOLDER)
        return flag


class ProcessorTitle(Processor):
    """Processor for titular data from a string or PreProcessed object.

    POSTCONDITION: value assignment to data attributes is dependent on the
    validity of the argument string/PreProcessed object, otherwise the
    attributes take a fill value.

    Attr:
        title
        series
        validation_results

    Methods:
        isValid
        isSeries

    Class Methods:
        split
    """
    _pre_attr_name = "italic"
    _data_attrs = set("title series".split())

    @classmethod
    def split(cls, string):
        """Split a string with a title (and series) into a two member list.

        >>> no_series = "A noteworthy subject, with a subclause."
        >>> ProcessorTitle.split(no_series)
        ['A noteworthy subject, with a subclause', '']
        >>> with_series = "Illustrated puffins. "
        >>> ProcessorTitle.split(with_series)
        ['Illustrated puffins', 'Some journal: Volume III]
        """
        raise NotImplementedError()


    def isValid(self):
        """Boolean check: does object pass validation?

        >>> wrong = ProcessorTitle("Important subject matter,")
        >>> wrong.isValid()
        False
        >>> right = ProcessorTitle("Superior debugging 101.")
        >>> right.isValid()
        True

        >>> complex_wrong = ProcessorTile("Journal: Volume XI. Some title.")
        >>> complex_wrong.isValid()
        False
        >>> complex_right = ProcessorTile("Some title. Journal: Volume XI.")
        >>> complex_right.isValid()
        True
        """
        return super().isValid()

    def _isValid(self):
        self.__structure_result = None
        # TODO
        # cond_series_info True PASS
        # cond_series_info False PASS

        # cond_endswith_fullstop (True, False)
        # cond_colon_count (True)
        # cond_colon_preceded_by_fullstop (True)
        # cond_volume_preceded_by_fullstop (True)
        # cond_volume_ambiguity?

        # TODO - taken from ProcessorAuthors
        # self._structure_report = set()
        #
        # main_flag = self._maincond_count_commas()
        # if main_flag:
        #     prefix = self._CONDITIONAL_METHOD
        #     cond_methods = [getattr(self, name) for name in dir(self)
        #                     if name.startswith(prefix)]
        #     iter_bool = (m() for m in cond_methods)
        #     secondary_flag = all([b for b in iter_bool if b is not None])
        #     flag = secondary_flag and main_flag
        # else:
        #     flag = main_flag
        # if flag:
        #     self._structure_report.add(self._VALID_REPORT)
        #     return flag
        # else:
        #     return flag

    def isSeries(self):
        """Boolean check: does object have series info?

        >>> without_series = ProcessorTitle("Superior debugging 101.")
        >>> without_series.isSeries()
        False

        >>> with_series = ProcessorTile("Hope: a story. Some Journal: Volume I.")
        >>> complex_wrong.isSeries()
        True
        """
        raise NotImplementedError()

    def _assign_values(self):
        raise NotImplementedError()


class ProcessorMeta(Processor):
    """Processor for meta-data from a string or PreProcessed object."""
    _pre_attr_name = "post_italic"
    _data_attrs = set(("illustrator translator publisher publplace year "
                       "pages price isbn issn").split())

    def _isValid(self):
        self.__structure_result = None
        # cond_section_count < 2 FAIL
        # cond_section_count == 4 PASS
        # cond_section_count == 5 PASS
        # cond_section_count > 5 FAIL

        # cond_endswith_fullstop (4, 5)
        # cond_optional_section_struct (5)
        # cond_section_zero_is_pubplace (4, 5)
        # cond_section_one_is_pages (4, 5)
        # cond_section_two_is_price (4, 5)
        # cond_section_three_is_identifier (4, 5)


class PostProcessed(object):
    """A data-object that validates and greps a PreProcessed object."""
    _processor_types = [ProcessorAuthors, ProcessorTitle, ProcessorMeta]
    _data_attrs = set(itertools.chain.from_iterable(
                      p._data_attrs for p in _processor_types))

    def __init__(self, preprocessed):
        # Assign the Processor object programatically and map it with its own
        # data attributes.
        attr2processor = dict()
        for Processor in self._processor_types:
            attr_name = "_" + Processor.__name__.lower() + "_obj"
            obj = Processor(preprocessed)
            attr2processor.update({da: obj for da in Processor._data_attrs})
            super().__setattr__(attr_name, obj)

        # Assign the corresponding Processor object value for each specified
        # Class data attribute.
        # NB The implicit logic is: PostProcessor.attr <- Processor.attr
        for postprocessor_attr in PostProcessed._data_attrs:
            processor_obj = attr2processor[postprocessor_attr]
            processor_val = getattr(processor_obj, postprocessor_attr)
            # Ensure empty string replaces None or empty containers
            # if not processor_val:  # TODO - uncomment once integration test passes.
            #     processor_val = str()
            super().__setattr__(postprocessor_attr, processor_val)

        self._attr2processor = attr2processor


class PreProcessed(object):
    """Identify the italic and non-italic parts of an XML paragraph element.

    Attrs:
        pre_italic
        italic
        post_italic
        xpaths
    Methods:
        is_valid_italic_pattern
        get_italic_pattern
        identify_substrings
    """

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
