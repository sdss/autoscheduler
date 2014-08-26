#!/usr/bin/env python
# encoding: utf-8
"""
utils.py

Created by José Sánchez-Gallego on 15 May 2014.
Licensed under a 3-clause BSD license.

Revision history:
    15 May 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
import numpy as np
from .. import config
from astropysics import obstools
from .. import log


def mlhalimit(dec):
    """Returns HA limits.

    Calculates the maximum HAs acceptable for a list of declinations.
    Uses the polinomial fit by David Law and a omega limit of 0.5.

    """

    funcFit = np.array([1.59349, 0.109658, -0.00607871,
                        0.000185393, -2.54646e-06, 1.16686e-08])[::-1]

    dec = np.atleast_1d(dec)
    halimit = np.abs(np.polyval(funcFit, dec))

    halimit[np.where((dec < -10) | (dec > 80))] = 0.0

    if len(halimit) == 1:
        return halimit[0] * 15
    else:
        return halimit * 15


def computeAirmass(dec, ha, lat=config['observatory']['latitude'],
                   correct=[75., 10.]):
    """Calculates the airmass for a given declination and HA (in degrees).

    By default, assumes that the latitude of the observation is the one set
    in the configuration file. If correct is defined, abs(HA) anggles greater
    than correct[0] are given a flat value correct[1].
    """

    dec = np.atleast_1d(dec)
    ha = np.atleast_1d(ha) % 360.

    if ha > 180:
        ha -= 360

    airmass = (np.sin(lat * np.pi / 180.) * np.sin(dec * np.pi / 180.) +
               np.cos(lat * np.pi / 180.) * np.cos(dec * np.pi / 180.) *
               np.cos(ha * np.pi / 180.)) ** (-1)

    if correct is not None:
        airmass[np.abs(ha) > correct[0]] = correct[1]

    if len(airmass) == 1:
        return airmass[0]
    else:
        return airmass


def isPlateComplete(inp, format='plate_id'):
    """Returns if a plate is complete using the MaNGA logic."""

    from ..dbclasses import Plate

    format = format.lower()

    if format in ['plate_pk', 'pk']:
        plate = Plate(inp, format='pk', rearrageExposures=True)
    elif format in ['plate_id', 'id']:
        plate = Plate.fromPlateID(inp, rearrageExposures=True)

    return plate.isComplete


def getAPOcomplete(inp, format='plate_id'):
    """Returns a dictionary with the APOcomplete output."""

    from ..dbclasses import Plate
    from collections import OrderedDict

    format = format.lower()
    inp = np.atleast_1d(inp)

    APOcomplete = OrderedDict()

    for ii in inp:

        if format in ['plate_pk', 'pk']:
            plate = Plate(ii, format='pk', rearrangeExposures=False)
        elif format in ['plate_id', 'id']:
            plate = Plate.fromPlateID(ii, rearrangeExposures=False)

        APOcomplete[plate.plate_id] = []

        for set in plate.sets:
            for exp in set.exposures:

                mjd = exp.getMJD()
                ss = set.pk
                dPos = exp.ditherPosition.upper()
                nExp = exp.exposure_no

                APOcomplete[plate.plate_id].append(
                    [plate.plate_id, mjd, ss, dPos, nExp])

    return APOcomplete


def createSite(longitude=None, latitude=None, altitude=None,
               name=None, verbose=False, **kwargs):
    """Returns an astropysics.obstools.site instance. By default, uses the
    coordinates for APO."""

    if None in [longitude, latitude, altitude, name]:
        assert 'observatory' in config.keys()

    longitude = config['observatory']['longitude'] \
        if longitude is None else longitude
    latitude = config['observatory']['latitude'] \
        if latitude is None else latitude
    altitude = config['observatory']['altitude'] \
        if altitude is None else altitude

    if name is None:
        if 'name' not in config['observatory']:
            name = ''
        else:
            name = config['observatory']['name']

    site = obstools.Site(latitude, longitude, name=name, alt=altitude)

    if verbose:
        log.info('Created site with name \'{0}\''.format(name))

    return site


def JDdiff(JD0, JD1):
    """Returns the number of seconds between two Julian dates."""

    return (JD1 - JD0) * 86400
