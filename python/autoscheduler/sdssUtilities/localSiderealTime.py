#!/usr/bin/env python
# encoding: utf-8
"""
localSiderealTime.py

Created by José Sánchez-Gallego on 4 Sep 2014.
Licensed under a 3-clause BSD license.

Revision history:
    4 Sep 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from astropy import time
from astropy import units


class LocalSiderealTime(object):
    """Simple class to compute LST for a given location."""

    def __init__(self, *args, **kwargs):

        inputFormat = kwargs.setdefault('format', 'TAI')
        self.longitude = kwargs.setdefault('longitude', 254.179722)

        if inputFormat.upper() == 'TAI':
            self.time = time.Time(0, format='mjd', scale='tai') + \
                time.TimeDelta(args[0], format='sec', scale='tai')
        elif inputFormat.upper() == 'ISOT':
            self.time = time.Time(args[0], format='isot', scale='tai')
        elif inputFormat.upper() == 'JD':
            self.time = time.Time(args[0], format='jd', scale='tai')
        else:
            raise ValueError('format value not valid.')

    @property
    def degrees(self):
        self.time.delta_ut1_utc = 0.
        lst = self.time.sidereal_time('apparent',
                                      longitude=self.longitude * units.deg)
        return lst.deg

    def getHA(self, alpha):
        lst = self.degrees
        ha = (lst - alpha) % 360.
        if ha > 180.:
            ha -= 360
        return ha
