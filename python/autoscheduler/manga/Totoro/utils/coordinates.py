#!/usr/bin/env python
# encoding: utf-8
"""
coodinates.py

Created by José Sánchez-Gallego on 1 Apr 2014.
Licensed under a 3-clause BSD license.

Revision history:
    1 Apr 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function

import numpy as np


class RADec(object):

    def __init__(self, ra, dec, units=['hours', 'degrees']):

        if hasattr(ra, '__iter__'):
            assert hasattr(dec, '__iter__')
            assert len(ra) == len(dec)

        if hasattr(units, '__iter__'):
            assert
