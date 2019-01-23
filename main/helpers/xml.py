#!/usr/bin/env python3
# -*- coding: utf8 -*-
"""Various XML classes for Recompose.

_XMLAsInputBase - base class

XMLAsInput - class for verifying suitablity of an XML file for Recompose

Copyright: Ian Vermes 2019
"""

import exceptions

from lxml import etree

import os

EXPECTED_PREFIXES = set(['xml', 'pkg', 'wps', 'wne', 'wpi', 'wpg', 'w15', 'w14',
                         'w', 'w10', 'wp', 'wp14', 'v', 'm', 'r', 'o', 'mv',
                         'mc', 'mo', 'wpc', 'a', 'sl', 'ds', 'xsi', 'dcmitype',
                         'dcterms', 'dc', 'cp', 'b', 'vt', None])
SAMPLE_URIS = {"pkg": "http://schemas.microsoft.com/office/2006/xmlPackage",
               "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
               None: "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"}


class _XMLAsInputBase(object):
    """Base class for classes that interact with the XML input file.
    """
    def __init__(self):
        self._has_tree = False


class XMLAsInput(_XMLAsInputBase):
    """Check whether an input file is suitable.

    Methods:
        isSuitable
    Attr:
        root
    """

    def __init__(self):
        super().__init__()
        self.__suitable = False
        self.__tree = None
        self.__root = None

    @property
    def root(self):
        if self.__suitable:
            return self.__root
        else:
            method = self.isSuitable.__name__
            raise exceptions.InputOperationError(detail=method)

    def _sniff(self, fileobject):
        try:
            fileobject.seek(0, 0)
            lines = [fileobject.readline().strip() for _ in range(2)]
        except UnicodeDecodeError:
            boolean = False
        else:
            boolean = ("xml" in lines[0] and "progid=\"Word.Document\"" in lines[1])
        finally:
            fileobject.seek(0, 0)

        return boolean

    def _parse(self, fileobject):
        try:
            fileobject.seek(0, 0)
            etree.parse(fileobject)
        except (etree.XMLSyntaxError, UnicodeDecodeError):
            boolean = False
        else:
            boolean = True
        finally:
            fileobject.seek(0, 0)
        return boolean

    def _namespace(self, fileobject):
        query = "//namespace::*"

        try:
            fileobject.seek(0, 0)
            tree = etree.parse(fileobject)
            nsmap = {prefix: uri for prefix, uri in tree.xpath(query)}
            prefixes = set(nsmap)
            flag1 = prefixes == EXPECTED_PREFIXES
            flag2 = all([(nsmap.get(pre, "") == uri) for pre, uri in SAMPLE_URIS.items()])
            boolean = flag1 and flag2
        finally:
            fileobject.seek(0, 0)

        return boolean

    def _battery_test(self, fileobject):
        boolean = self._sniff(fileobject)
        if boolean:
            boolean = self._parse(fileobject)
        else:
            return boolean
        if boolean:
            boolean = self._namespace(fileobject)
        else:
            return boolean
        return boolean

    def __setup(self, filename):
        if not self.__suitable:
            return
        self.__tree = tree = etree.parse(filename)
        self.__root = root = tree.getroot()

    def isSuitable(self, filename, fatal=None):

        with open(filename, "r") as handle:
            suitable = self._battery_test(handle)

        if fatal and not suitable:
            detail = os.path.basename(filename)
            raise exceptions.InputFileError(detail=detail)
        else:
            self.__suitable = suitable
            self.__setup(filename)
            return suitable
