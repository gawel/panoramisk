# -*- coding: utf-8 -*-
from .manager import Manager  # NOQA
try:
    from . import fast_agi  # NOQA
except SyntaxError:
    # not available in python2
    pass
