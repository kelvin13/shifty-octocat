# coding: utf8
"""
    CSS Selectors based on XPath
    ============================

    This module supports selecting XML/HTML elements based on CSS selectors.
    See the `CSSSelector` class for details.


    :copyright: (c) 2007-2012 Ian Bicking and contributors.
                See AUTHORS for more details.
    :license: BSD, see LICENSE for more details.

"""

from .parser import (parse, Selector, FunctionalPseudoElement,
                              SelectorError, SelectorSyntaxError)
from .xpath import GenericTranslator, HTMLTranslator, ExpressionError


VERSION = '0.9.1'
__version__ = VERSION
