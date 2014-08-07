#!/usr/bin/env python
# encoding: utf-8
"""
intervals.py

Created by José Sánchez-Gallego on 4 Aug 2014.
Licensed under a 3-clause BSD license.

Revision history:
    4 Aug 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
import numpy as np


def getIntervalIntersectionLength(aa, bb, wrapAt=360):
    """Returns the length of the instersection between two intervals aa and bb.
    """

    intersection = getIntervalIntersection(aa, bb, wrapAt=wrapAt)

    if intersection is False:
        return 0.0
    else:
        return (intersection[1] - intersection[0]) % wrapAt


def getIntervalIntersection(aa, bb, wrapAt=360):
    """Returns the intersection between two intervals."""

    if (bb[1] - bb[0]) % wrapAt > (aa[1] - aa[0]) % wrapAt:
        aa, bb = bb, aa

    if isPointInInterval(bb[0], aa) and isPointInInterval(bb[1], aa):
        return np.array([bb[0], bb[1]])

    if not isPointInInterval(bb[0], aa) and not isPointInInterval(bb[1], aa):
        return False

    if isPointInInterval(bb[0], aa):
        return np.array([bb[0], aa[1]])

    if isPointInInterval(bb[1], aa):
        return np.array([aa[0], bb[1]])


def isPointInInterval(point, ival, wrapAt=360):
    """Returns True if point in interval."""

    return (point - ival[0]) % wrapAt < (ival[1] - ival[0]) % wrapAt


def isIntervalInsideOther(aa, bb, wrapAt=360, onlyOne=False):
    """Checks if the interval aa (a numpy.ndarray of length 2) is inside bb."""

    p1 = ((aa[0] - bb[0]) % wrapAt < (bb[1]-bb[0]) % wrapAt)
    p2 = ((aa[1] - bb[0]) % wrapAt < (bb[1]-bb[0]) % wrapAt)

    if p1 and p2:
        return True
    elif onlyOne and (p1 or p2):
        return True

    return False
