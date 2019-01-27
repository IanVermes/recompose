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
from collections import UserDict

EXPECTED_PREFIXES = set(['xml', 'pkg', 'wps', 'wne', 'wpi', 'wpg', 'w15', 'w14',
                         'w', 'w10', 'wp', 'wp14', 'v', 'm', 'r', 'o', 'mv',
                         'mc', 'mo', 'wpc', 'a', 'sl', 'ds', 'xsi', 'dcmitype',
                         'dcterms', 'dc', 'cp', 'b', 'vt', None])
SAMPLE_URIS = {"pkg": "http://schemas.microsoft.com/office/2006/xmlPackage",
               "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
               None: "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"}

FIND_NAMESPACES_GET_PREFIX_URI = etree.XPath("//namespace::*")


class XPaths(UserDict):
    """Dictionary that maps xpath queries to etree.XPath with shared namespaces.

    Arg:
        source(etree._ElementTree or str): Tree or XML filename.
    Class methods:
        make_nsmap: From a tree or filename, find namespaces and map prefixes
                    to uris.
    Methods:
        add_xpath: From a xpath query, compile a namespaced etree.XPath
                   function and cache it for reuse.
        get_xpath: For an xpath query, fetch a etree.XPath function from the
                   cache or compiler. Memoizes the function if necessary.
        get: Convenience method of get_xpath method.
    Attr:
        nsmap(dict): XML namespace prefix -> URI.
    """

    def __init__(self, source):
        super().__init__()  # create UserDict.data and wrap around it.
        self.__tree = self.__get_tree(source)
        self.__notimplemented = ("This method is not accessible from class "
                                 "interface. Consider rewritting as wrapped "
                                 "class?.")
        self.nsmap = self.make_nsmap(self.__tree, replace=True)

    def add_xpath(self, query):
        try:
            xpath_func = etree.XPath(query, namespaces=self.nsmap)
        except etree.XPathSyntaxError as err:
            err_reason = err.args[0]
        else:
            err_reason = ""

        if err_reason:
            detail = f"Given reason: '{query}' -> {err_reason.lower()}."
            raise exceptions.XPathQueryError(detail=detail)
        else:
            self.data[query] = xpath_func

    def get_xpath(self, query):
        if query not in self:
            self.add_xpath(query)
        return self.data[query]

    def get(self, query):
        return self.get_xpath(query)

    @staticmethod
    def __get_tree(source):
        def tree2tree(source):
            return source

        def elem2tree(source):
            return source.getroottree()

        def string2tree(source):
            return etree.parse(source)

        types = {str: string2tree, etree._Element: elem2tree, etree._ElementTree: tree2tree}
        tree_maker = types.get(type(source), None)
        if tree_maker is None:
            msg = ("Only use filename strings or etree._ElementTree "
                   f"objects, got: {repr(type(source))}")
            raise TypeError(msg)
        else:
            tree = tree_maker(source)
            return tree

    @classmethod
    def make_nsmap(cls, source, replace=False, repl="ns0"):
        tree = cls.__get_tree(source)
        xpath_func = FIND_NAMESPACES_GET_PREFIX_URI
        nsmap = {pre: uri for pre, uri in xpath_func(tree)}
        if not replace:
            return nsmap
        else:
            if None in nsmap and repl in nsmap:
                raise exceptions.PrefixSubstitutionError(detail=repl)
            elif None in nsmap:
                nsmap[repl] = nsmap.pop(None)
                return nsmap
            else:
                return nsmap

    def setdefault(self, *args, **kwargs):
        raise NotImplementedError(self.__notimplemented)

    def update(self, *args, **kwargs):
        raise NotImplementedError(self.__notimplemented)



class _XMLAsInputBase(object):
    """Base class for classes that interact with the XML input file.
    """
    def __init__(self):
        self._has_tree = False


class XMLAsInput(_XMLAsInputBase):
    """Check whether an input file is suitable.

    Methods:
        isSuitable
        iter_paragraphs
    Attr:
        root
        tree
        nsmap
        xpaths
    """

    def __init__(self):
        super().__init__()
        self.__suitable = False
        self.__tree = None
        self.__root = None
        self.__xpaths = None
        self._find_paras_query = "//w:p"
        self._find_suitable_paras_query = "//w:p[(count(descendant::w:i) > 0) and (count(descendant::w:t) > 0)]"

    @property
    def root(self):
        if self.__suitable:
            return self.__root
        else:
            method = self.isSuitable.__name__
            raise exceptions.InputOperationError(detail=method)

    @property
    def tree(self):
        if self.__suitable:
            return self.__tree
        else:
            method = self.isSuitable.__name__
            raise exceptions.InputOperationError(detail=method)

    @property
    def nsmap(self):
        if self.__suitable:
            return self.__xpaths.nsmap
        else:
            method = self.isSuitable.__name__
            raise exceptions.InputOperationError(detail=method)

    @property
    def xpaths(self):
        if self.__suitable:
            return self.__xpaths
        else:
            method = self.isSuitable.__name__
            raise exceptions.InputOperationError(detail=method)

    def iter_paragraphs(self, force_all=False):
        if force_all:
            query = self._find_paras_query
        else:
            query = self._find_suitable_paras_query
        find_paras = self.xpaths.get(query)
        for para in find_paras(self.tree):
            yield para


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
        find_ns = FIND_NAMESPACES_GET_PREFIX_URI

        try:
            fileobject.seek(0, 0)
            tree = etree.parse(fileobject)
            nsmap = {prefix: uri for prefix, uri in find_ns(tree)}
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
        self.__root = tree.getroot()
        self.__xpaths = xpaths = XPaths(tree)
        xpaths.add_xpath(query=self._find_paras_query)
        xpaths.add_xpath(query=self._find_suitable_paras_query)

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
