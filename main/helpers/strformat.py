#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Various string formatting tools for Recompose

Copyright: Ian Vermes 2019
"""

import re
import functools
import textwrap

PATTERN_BULLET_SPLIT = r"(?:[\d\*]+\)\ )"
PATTERN_BULLET_REPL = r"([\d\*]+\))"

PARAGR_WRAP = textwrap.TextWrapper(width=70,
                                   initial_indent=" " * 4,
                                   subsequent_indent=" " * 4)

BULLET_WRAP = textwrap.TextWrapper(width=70,
                                   initial_indent=" " * 8,
                                   subsequent_indent=" " * 10)


def format_string(string, has_bullets=False, numbers=True, padding=True):

    if has_bullets:
        bullet_spans = set(find_bullet_spans(string))
        substrings = enumerate_bullets(string, numbers=numbers)
    else:
        bullet_spans = set()
        substrings = {}
    normal_spans = set(find_non_bullet_spans(string))
    all_spans = normal_spans.union(bullet_spans)

    for span in all_spans:
        sub = substrings.get(span, get_substring(string, span))
        if padding:
            if span in bullet_spans:
                sub = BULLET_WRAP.fill(sub)
            else:
                sub = PARAGR_WRAP.fill(sub)
        substrings[span] = sub

    new_string = "".join([substrings[k] for k in sorted(substrings)])
    return new_string


def enumerate_bullets(string, numbers=True):
    bullet_template = "*)"
    number_template = "{i:1d})"
    spans = find_bullet_spans(string)
    rgx = re.compile(PATTERN_BULLET_REPL)

    if numbers:
        repl_map = {span: number_template.format(i=i) for i, span in enumerate(spans, start=1)}
    else:
        repl_map = {span: bullet_template for span in spans}

    result = {}
    for span, repl_bullet in repl_map.items():
        substring = string[span[0]:span[1]]
        new_substring = rgx.sub(repl=repl_bullet, string=substring, count=1)
        result[span] = new_substring

    return result


@functools.lru_cache(maxsize=128)
def find_bullet_spans(string):
    linebreak = "\n"
    rgx = re.compile(PATTERN_BULLET_SPLIT)
    starts = [m.start(0) for m in rgx.finditer(string)]

    intervals = []
    for i, start in enumerate(starts):

        try:
            stop = starts[i+1]
        except IndexError:
            substring = string[start:]
            if linebreak in substring:
                stop = substring.index(linebreak) + start
            else:
                stop = -1

        span = (start, stop)
        intervals.append(span)
    return intervals


def find_non_bullet_spans(string):
    bullet_spans = find_bullet_spans(string)
    normal_span = []
    first_stretch = (0, bullet_spans[0][0])  # Can be zero length splice.
    normal_span.append(first_stretch)
    for i, (start, stop) in enumerate(bullet_spans):
        normal_start = stop
        try:
            normal_stop = bullet_spans[i+1][0]
        except IndexError:
            normal_stop = len(string)
        if normal_start == normal_stop:
            continue
        else:
            span = (normal_start, normal_stop)
            normal_span.append(span)
    return normal_span


def get_substring(string, span):
    start, stop = span
    substring = string[start:stop]
    return substring
