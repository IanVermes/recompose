#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Various string formatting tools for Recompose

Copyright: Ian Vermes 2019
"""


import unicodedata


def makeItalic(string):
    # fill = chr(9633)  # Empty box.

    new_string = []
    for char in string:
        try:
            new_char = ITALIC_LETTER_MAP[char]
        except KeyError:
            # if char in WHITESPACE_CHR_MAP:
            #     new_char = WHITESPACE_CHR_MAP[char]
            # elif unicodedata.category(char) in PUNCTUATION_CAT_SET:
            #     new_char = char
            # else:
            new_char = fill
        new_string.append(new_char)
    new_string = "".join(new_string)
    return new_string


def _get_italic_mapping(ord_CAP_A):
    mapping = {}
    for ord in range(ord_CAP_A, ord_CAP_A + 52):
        new_char = chr(ord)
        if not new_char.isprintable():
            msg = "Could not map '{}' to font equivalent."
            raise RuntimeError(msg)
        _, value = unicodedata.decomposition(new_char).split(" ")
        primitive_ord = int(value, base=16)
        mapping[chr(primitive_ord)] = new_char
    return mapping


def _get_best_italic_mapping(fallback=False):
    for font, ord_A in _FONT_A_POINTS:
        try:
            mapping = _get_italic_mapping(ord_CAP_A=ord_A)
        except RuntimeError:
            mapping = {}
        if mapping:
            break
    if not mapping and fallback:
        fallback_A = ord("A")
        fallback_a = ord("a")
        ascii_upper = [chr(i) for i in range(fallback_A, fallback_A + 26)]
        ascii_upper += [chr(i) for i in range(fallback_a, fallback_a + 26)]
        mapping = {char: char for char in ascii_upper}
    return mapping


_FONT_A_POINTS = [("MATHEMATICAL ITALIC", 119860),
                  ("MATHEMATICAL BOLD ITALIC", 119912),
                  ("MATHEMATICAL SANS-SERIF ITALIC", 120328),
                  ("MATHEMATICAL SANS-SERIF BOLD ITALIC", 120380)]

_FILL_CHR = chr(9633)  # Empty Box

ITALIC_LETTER_MAP = _get_best_italic_mapping()
