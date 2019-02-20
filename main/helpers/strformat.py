#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Various string formatting tools for Recompose

Funcs:
    makeItalic

Copyright: Ian Vermes 2019
"""


import unicodedata


def makeItalic(string):
    """Convert a string into an italic equivalent.

    Accented letters are escaped to the Unicode empty box character. Whitespace
    are converted to visible charaters. Punctuation are kept the same.
    """
    fill = FILL_CHR  # Empty box.

    new_string = []
    for char in string:
        try:
            new_char = ITALIC_LETTER_MAP[char]
        except KeyError:
            if char in WHITESPACE_CHR_MAP:
                new_char = WHITESPACE_CHR_MAP[char]
            elif unicodedata.category(char) in PUNCTUATION_CAT_SET:
                new_char = char
            else:
                new_char = fill
        new_string.append(new_char)
    new_string = "".join(new_string)
    return new_string


def _get_font_letters(ord_CAP_A):
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


def _get_font_digits(ord_ZERO):
    mapping = {}
    for ord in range(ord_ZERO, ord_ZERO + 10):
        new_char = chr(ord)
        if not new_char.isprintable():
            msg = "Could not map '{}' to font equivalent."
            raise RuntimeError(msg)
        _, value = unicodedata.decomposition(new_char).split(" ")
        primitive_ord = int(value, base=16)
        mapping[chr(primitive_ord)] = new_char
    return mapping


def _fallback_letter_mapping():
    fallback_A = ord("A")
    fallback_a = ord("a")
    ascii_chars = [chr(i) for i in range(fallback_A, fallback_A + 26)]
    ascii_chars += [chr(i) for i in range(fallback_a, fallback_a + 26)]
    return {char: char for char in ascii_chars}


def _fallback_digit_mapping():
    fallback_ZERO = ord("0")
    ascii_chars = [chr(i) for i in range(fallback_ZERO, fallback_ZERO + 10)]
    return {char: char for char in ascii_chars}


def _get_best_italic_mapping():
    # Get the letter mapping:
    for font, ord_A in _FONT_A_POINTS:
        try:
            mapping = _get_font_letters(ord_CAP_A=ord_A)
        except RuntimeError:
            mapping = {}
            letter_font = None
        if mapping:
            letter_font = font
            break
    # Match a numerical font with the letter font
    if letter_font is not None:
        for font, ord_ZERO in _FONT_ZERO_POINTS.items():
            if font in letter_font:
                num_map = {}
            else:
                try:
                    num_map = _get_font_digits(ord_ZERO)
                except RuntimeError:
                    num_map = {}
            if num_map:
                break
    else:
        num_map = {}
    # Fallback if things went wrong
    if not mapping:
        mapping = _fallback_letter_mapping()
    if not num_map:
        num_map = _fallback_digit_mapping()
    # Add num_map options to main mapping:
    for char_orig, char_font in num_map.items():
        mapping[char_orig] = char_font
    return mapping


# Order as desired.
_FONT_A_POINTS = [(2, "MATHEMATICAL BOLD ITALIC", 119912),
                  (0, "MATHEMATICAL SANS-SERIF BOLD ITALIC", 120380),
                  (3, "MATHEMATICAL ITALIC", 119860),
                  (1, "MATHEMATICAL SANS-SERIF ITALIC", 120328)]
_FONT_A_POINTS = [(font, ord_A) for i, font, ord_A in sorted(_FONT_A_POINTS)]

_FONT_ZERO_POINTS = {"MATHEMATICAL BOLD": 120782,
                     "MATHEMATICAL SANS-SERIF BOLD": 120812}

FILL_CHR = chr(9633)  # Empty Box

ITALIC_LETTER_MAP = _get_best_italic_mapping()
WHITESPACE_CHR_MAP = {" ": chr(183), "\n": chr(182), "\t": chr(8677)}
PUNCTUATION_CAT_SET = set("Pc Pd Pe Pf Pi Po Ps Sk".split())
