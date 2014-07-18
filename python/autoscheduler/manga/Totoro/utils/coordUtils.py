#!/usr/bin/env python
# encoding: utf-8
"""
coordUtils.py

Created by José Sánchez-Gallego on 16 Apr 2014.
Licensed under a 3-clause BSD license.

An unsorted collection of functions and classes related to coordinate and
time transformation.

Revision history:
    16 Apr 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from astropysics import coords


class HA(coords.AngularCoordinate):

    def __init__(self, input):
        """A parser of AngularCoordinate in the range [-180, 180] degrees.

        Parameters
        ----------
        input
            An `astropysics.coords.AngularCoordinate` valid input.

        """

        super(HA, self).__init__(input, range=[-180, 180, 0])

    def __add__(self, aa):
        return HA(self.degrees + aa.degrees)

    def __sub__(self, aa):
        return HA(self.degrees - aa.degrees)
