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
from ..utils import checkExposure, checkSet, createSite
import numpy as np

session = Session()


class Set(BaseDBClass):

    def __init__(self, inp, format='pk', autocomplete=True,
                 exposures=True, verbose=True, **kwargs):

        self.exposures = []
        self.verbose = verbose

        self.site = createSite()

        self.__DBClass__ = mangaDB.Set
        super(Set, self).__init__(inp, format=format,
                                  autocomplete=autocomplete)

        self.ra, self.dec = self.getCoordinates()

        if verbose:
            log.debug('Loaded set with pk={0}'.format(self.pk))

        if exposures:
            self.loadExposuresFromDB()

    def loadExposuresFromDB(self):

        with session.begin():
            mangaSet = session.query(mangaDB.Set).get(self.pk)

        for mangaExposure in mangaSet.exposures:
            self.exposures.append(Exposure(mangaExposure.platedbExposure.pk,
                                           autocomplete=True,
                                           format='pk',
                                           extendFromMaNGA=True,
                                           verbose=self.verbose))

    def getCoordinates(self):

        with session.begin():
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

        return np.array([np.min(expHARanges), np.max(expHARanges)])

    def getHALimits(self):
        """Returns the HA limits to add more exposures to the set."""

        haRange = self.getHARange()
        return np.array([np.max(haRange) - 15., np.min(haRange) + 15.])

    def getDitherPositions(self):
        """Returns a list of dither positions in the set."""

        return [exp.ditherPosition for exp in self.exposures]

    def getSN2Array(self):
        """Returns an array with the cumulated SN2 of the valid exposures in
        the set. The return format is [b1SN2, b2SN2, r1SN2, r2SN2]."""

        validExposures = []
        for exposure in self.exposures:
            if checkExposure(exposure.manga_pk):
                validExposures.append(exposure)

        if len(validExposures) == 0:
            return np.array([0.0, 0.0, 0.0, 0.0])
        else:
            return np.sum([exp.getSN2Array() for exp in validExposures],
                          axis=0)

    def getQuality(self):
        """Returns the quality of the set (Excellent, Good, Poor)."""

        return checkSet(self.pk, verbose=False)

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

    def getUTVisibilityWindow(self):

        ha0, ha1 = self.getHALimits()

        lst0 = (ha0 + self.ra) % 360. / 15
        lst1 = (ha1 + self.ra) % 360. / 15


        # Needs to add date
        ut0 = '{0:%H:%M}'.format(self.site.localTime(
            lst0, utc=True, returntype='datetime'))
        ut1 = '{0:%H:%M}'.format(self.site.localTime(
            lst1, utc=True, returntype='datetime'))

        return (ut0, ut1)


    # def _getCompletionStatus(self):

    #     snOK = False
    #     ditherPosOK = False
    #     HAlimitsOK = False
    #     seeingOK = False

    #     validExp = self.getValidExposures()

    #     ditherPos = [exp.ditherPos for exp in validExp]
    #     if (all([dd in DITHER_POSITIONS_NEEDED() for dd in ditherPos]) and
    #             all([dd in ditherPos for dd in DITHER_POSITIONS_NEEDED()])):
    #         ditherPosOK = True

    #     if (self.get_HA_minmax() is not None and
    #             Longitude(self.get_HA_minmax()[1] - self.get_HA_minmax()[0],
    #                       unit=uu.hour)
    #             <= Longitude('1h')):
    #         HAlimitsOK = True

    #     if validExp.nExposures >= 1:
    #         minMaxSN = self._getMaxMinSN()
    #         if (all(minMaxSN[1, :]/minMaxSN[0, :] <= SN2_FACTOR_SET()) and
    #                 all(minMaxSN[3, :]/minMaxSN[2, :] <= SN2_FACTOR_SET())):
    #             snOK = True

    #     avgSeeings = [exp.avgSeeing for exp in validExp]
    #     if np.max(avgSeeings) - np.min(avgSeeings) <= MAX_DIFF_SEEING_SET:
    #         seeingOK = True

    #     return (bool(snOK * ditherPosOK * HAlimitsOK),
    #             (snOK, ditherPosOK, HAlimitsOK, seeingOK))

    # def getFailedTests(self):

    #     tests = self._getCompletionStatus()[1]
    #     labels = ['SN2', 'ditherPositions', 'HAlimits', 'avgSeeing']
    #     return [labels[ii] for ii in range(len(labels)) if tests[ii] is False]

    # def _getMaxMinSN(self):
    #     """Returns an array with the max and min SN in the valid exposures.

    #     The array returned is of the form
    #         [[minSN_Blue_1, minSN_Blue_2],
    #          [maxSN_Blue_1, maxSN_Blue_2],
    #          [minSN_Red_1, minSN_Red_2],
    #          [maxSN_Red_1, maxSN_Red_2]]

    #     """

    #     validExp = self.getValidExposures()

    #     if validExp.nExposures == 0:
    #         return np.array([[0., 0.], [0., 0.], [0., 0.], [0., 0.]])

    #     SN_red = np.array([exp.SN_red for exp in validExp])
    #     SN_blue = np.array([exp.SN_blue for exp in validExp])
    #     maxSNred = np.max(SN_red, axis=0)
    #     minSNred = np.min(SN_red, axis=0)
    #     maxSNblue = np.max(SN_blue, axis=0)
    #     minSNblue = np.min(SN_blue, axis=0)

    #     return np.array([minSNblue, maxSNblue, minSNred, maxSNred])

    # @property
    # def missingDither(self):
    #     if 'ditherPositions' in self.getFailedTests():
    #         return True
    #     return False

    # def get_HA_minmax(self, exposures=None):

    #     if exposures is None:
    #         exposures = self.getValidExposures()

    #     if len(exposures) == 0:
    #         return None

    #     HAs = []
    #     for exp in exposures:
    #         HAs += [exp.HAstart.hour, exp.HAend.hour]
    #     return Longitude([np.min(HAs), np.max(HAs)], unit=uu.hour)

    # @property
    # def nExposures(self):
    #     return len(self.getValidExposures())

    # @property
    # def complete(self):
    #     if self._complete is not None:
    #         return self._complete
    #     return self._getCompletionStatus()[0]

    # @complete.setter
    # def complete(self, value):
    #     assert isinstance(value, bool) and value is not None
    #     self._complete = value

    # @property
    # def avgSeeing(self):
    #     if self._avgSeeing is not None:
    #         return self._avgSeeing
    #     return np.mean([exp.avgSeeing for exp in self.getValidExposures()])

    # @avgSeeing.setter
    # def avgSeeing(self, value):
    #     assert isinstance(value, Real)
    #     self._avgSeeing = value

    # @property
    # def SN_red(self):
    #     if self._SN_red is not None:
    #         return self._SN_red
    #     if self.nExposures == 0:
    #         return np.array([0.0, 0.0])
    #     return np.sum(np.atleast_2d(
    #         [exp.SN_red for exp in self.getValidExposures()]), axis=0)

    # @SN_red.setter
    # def SN_red(self, value):
    #     assert isinstance(value, (np.ndarray, list, tuple))
    #     self._SN_red = value

    # @property
    # def SN_blue(self):
    #     if self._SN_blue is not None:
    #         return self._SN_blue
    #     if self.nExposures == 0:
    #         return np.array([0.0, 0.0])
    #     return np.sum(np.atleast_2d(
    #         [exp.SN_blue for exp in self.getValidExposures()]), axis=0)

    # @SN_blue.setter
    # def SN_blue(self, value):
    #     assert isinstance(value, (np.ndarray, list, tuple))
    #     self._SN_blue = value

    # @property
    # def HAlimits(self):
    #     if self._HAlimits is not None:
    #         return self._HAlimits

    #     HAmaxmin = self.get_HA_minmax()
    #     if HAmaxmin is None:
    #         return None

    #     oneHour = Longitude('1h')
    #     if Longitude(HAmaxmin[1] - HAmaxmin[0], unit=uu.hour) > oneHour:
    #         return HAmaxmin

    #     return Longitude(
    #         [HAmaxmin[1]-oneHour, HAmaxmin[0]+oneHour], wrap_angle='180d')

    # @HAlimits.setter
    # def HAlimits(self, value):
    #     assert isinstance(value, (np.ndarray, list, tuple))
    #     self._HAlimits = np.array(value)

    # @property
    # def quality(self):
    #     if self._quality is not None:
    #         return self._quality

    #     if self.complete is False:
    #         return 'bad'

    #     if self.avgSeeing > SEEING_POOR():
    #         return 'poor'
    #     elif self.avgSeeing <= SEEING_POOR() and \
    #             self.avgSeeing > SEEING_EXCELLENT():
    #         return 'good'
    #     else:
    #         return 'excellent'

    # @quality.setter
    # def quality(self, value):
    #     assert isinstance(value, basestring)
    #     value = value.lower()
    #     self._quality = value
    #     if value in ['good', 'excellent', 'poor']:
    #         self.complete = True
    #     elif value == 'bad':
    #         self.complete = False
    #     else:
    #         raise ValueError('setQuality cannot have value {0}'.format(value))
