#!/usr/bin/env python
# encoding: utf-8
"""
set.py

Created by José Sánchez-Gallego on 18 Mar 2014.
Licensed under a 3-clause BSD license.

Revision history:
    18 Mar 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from .baseDBClass import BaseDBClass
from .exposure import Exposure
from .. import mangaDB, Session, plateDB
from .. import log
from .. import config
from ..exceptions import TotoroError
from ..logic import checkSet
from ..utils import createSite, getMinMaxIntervalSequence
import numpy as np
from copy import copy

session = Session()


class Set(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 exposures=True, verbose=True, mock=False, **kwargs):

        self.exposures = []
        self.isMock = mock
        self.verbose = verbose

        self.site = createSite()

        if not self.isMock:

            self.__DBClass__ = mangaDB.Set
            super(Set, self).__init__(inp, format=format,
                                      autocomplete=autocomplete)

            self.ra, self.dec = self.getCoordinates()

            if verbose:
                log.debug('Loaded set with pk={0}'.format(self.pk))

            if exposures:
                self.loadExposuresFromDB()

    def loadExposuresFromDB(self):

        with session.begin(subtransactions=True):
            mangaSet = session.query(mangaDB.Set).get(self.pk)

        for mangaExposure in mangaSet.exposures:
            self.exposures.append(Exposure(mangaExposure.platedbExposure.pk,
                                           autocomplete=True,
                                           format='pk',
                                           extendFromMaNGA=True,
                                           verbose=self.verbose))

    @classmethod
    def createMockSet(cls, ra=None, dec=None, verbose=False, **kwargs):

        newSet = Set.__new__(cls)

        if ra is None or dec is None:
            raise TotoroError('ra and dec must be specified')

        newSet.ra = ra
        newSet.dec = dec

        newSet.isMock = True
        newSet.pk = None if 'pk' not in kwargs else kwargs['pk']

        newSet.exposures = []

        if verbose:
            log.debug('Created mock with pk={0}'.format(newSet.pk))

        return newSet

    def addMockExposure(self, **kwargs):

        if self.complete is True:
            raise TotoroError('set is complete; not exposures can be added.')

        if 'ditherPosition' not in kwargs or kwargs['ditherPosition'] is None:
            kwargs['ditherPosition'] = self.getMissingDitherPositions()[0]

        newExposure = Exposure.createMockExposure(**kwargs)
        self.exposures.append(newExposure)

    def getCoordinates(self):

        if hasattr(self, 'ra') and hasattr(self, 'dec'):
            return np.array([self.ra, self.dec])

        with session.begin(subtransactions=True):
            pointing = session.query(plateDB.Pointing).join(
                plateDB.PlatePointing).join(plateDB.Observation).join(
                    plateDB.Exposure).join(mangaDB.Exposure).join(
                        mangaDB.Set).filter(
                            mangaDB.Set.pk == self.pk).one()

        return np.array([pointing.center_ra, pointing.center_dec], np.float)

    def getHARange(self):
        """Returns the HA range of the exposures in the set."""

        expHARanges = np.array([exposure.getHARange()
                                for exposure in self.exposures
                                if exposure.valid])
        return getMinMaxIntervalSequence(expHARanges)

    def getHALimits(self):
        """Returns the HA limits to add more exposures to the set."""

        haRange = self.getHARange()
        return np.array([np.max(haRange) - 15., np.min(haRange) + 15.]) % 360.

    def getDitherPositions(self):
        """Returns a list of dither positions in the set."""

        return [exp.ditherPosition for exp in self.exposures]

    def getMissingDitherPositions(self):
        """Returns a list of missing dither positions."""

        setDitherPositions = copy(config['set']['ditherPositions'])
        for dPos in self.getDitherPositions():
            if dPos.upper() in setDitherPositions:
                setDitherPositions.remove(dPos.upper())

        return setDitherPositions

    def getSN2Array(self):
        """Returns an array with the cumulated SN2 of the valid exposures in
        the set. The return format is [b1SN2, b2SN2, r1SN2, r2SN2]."""

        validExposures = []
        for exposure in self.exposures:
            if exposure.valid:
                validExposures.append(exposure)

        if len(validExposures) == 0:
            return np.array([0.0, 0.0, 0.0, 0.0])
        else:
            return np.sum([exp.getSN2Array() for exp in validExposures],
                          axis=0)

    def getSN2Range(self):
        """Returns the SN2 range in which new exposures may be taken."""

        maxSN2Factor = config['set']['maxSN2Factor']

        sn2 = np.array([exp.getSN2Array() for exp in self.exposures])
        sn2Average = np.array(
            [(np.mean(ss[0:2]), np.mean(ss[2:4])) for ss in sn2])

        minSN2Blue = np.max(sn2Average[:, 0]) / maxSN2Factor
        maxSN2Blue = np.min(sn2Average[:, 0]) * maxSN2Factor
        minSN2Red = np.max(sn2Average[:, 1]) / maxSN2Factor
        maxSN2Red = np.min(sn2Average[:, 1]) * maxSN2Factor

        if minSN2Red < config['SN2thresholds']['exposureRed']:
            minSN2Red = config['SN2thresholds']['exposureRed']
        if minSN2Blue < config['SN2thresholds']['exposureBlue']:
            minSN2Blue = config['SN2thresholds']['exposureBlue']

        return np.array([[minSN2Blue, maxSN2Blue], [minSN2Red, maxSN2Red]])

    def getSeeingRange(self):
        """Returns the seeing range in which new exposures may be taken."""

        maxSeeingRange = config['set']['maxSeeingRange']
        maxSeeing = config['exposure']['maxSeeing']
        seeings = np.array([exp.seeing for exp in self.exposures])

        seeingRangeMin = np.max(seeings) - maxSeeingRange
        seeingRangeMax = np.min(seeings) + maxSeeingRange
        if seeingRangeMax > maxSeeing:
            seeingRangeMax = maxSeeing

        return np.array([seeingRangeMin, seeingRangeMax])

    def getQuality(self):
        """Returns the quality of the set (Excellent, Good, Poor)."""

        return checkSet(self, verbose=False)

    def getValidExposures(self):

        validExposures = []
        for exp in self.exposures:
            if exp.valid is True:
                validExposures.append(exp)

        return validExposures

    def getAverageSeeing(self):

        seeings = []
        for exp in self.exposures:
            if exp.valid:
                seeings.append(exp.manga_seeing)

        return np.mean(seeings)

    def getLSTRange(self):

        ha0, ha1 = self.getHALimits()

        lst0 = (ha0 + self.ra) % 360. / 15
        lst1 = (ha1 + self.ra) % 360. / 15

        return np.array([lst0, lst1])

    def getUTVisibilityWindow(self, date=None, format='str'):

        lst0, lst1 = self.getLSTRange()

        ut0 = self.site.localTime(lst0, date=date, utc=True,
                                  returntype='datetime')
        ut1 = self.site.localTime(lst1, date=date, utc=True,
                                  returntype='datetime')

        if format == 'str':
            return ('{0:%H:%M}'.format(ut0), '{0:%H:%M}'.format(ut1))
        else:
            return (ut0, ut1)

    @property
    def complete(self):
        if self.getQuality() != 'Incomplete':
            return True
        else:
            return False
