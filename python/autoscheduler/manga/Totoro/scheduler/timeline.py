#!/usr/bin/env python
# encoding: utf-8
"""
timeline.py

Created by José Sánchez-Gallego on 1 Aug 2014.
Licensed under a 3-clause BSD license.

Revision history:
    1 Aug 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from ..dbclasses.plate import Plates
from .. import config, log
import warnings
from ..exceptions import TotoroUserWarning
from ..utils import JDdiff, createSite
from ..logic import getOptimalPlate
import numpy as np


class Timelines(list):

    def __init__(self, observingBlocks, plates=None, **kwargs):

        initList = []
        for row in observingBlocks:
            initList.append(Timeline(row['JD0'], row['JD1'], plates=plates))

        list.__init__(self, initList)

    def schedule(self, mode='planner', **kwargs):

        plates = self[0]._plates
        for timeline in self:
            timeline._plates = plates
            timeline.schedule(mode=mode, **kwargs)
            plates = timeline._plates


class Timeline(object):

    def __init__(self, startTime, endTime, plates=None, **kwargs):

        self.startTime = startTime
        self.endTime = endTime

        if plates is None:
            self._plates = Plates()
        else:
            self._plates = plates

        self.site = createSite()

    def schedule(self, mode='planner', **kwargs):

        log.info('Scheduling timeline with JD0={0:.4f}, JD1={1:.4f}'
                 .format(self.startTime, self.endTime))
        currentTime = self.startTime
        remainingTime = JDdiff(currentTime, self.endTime)

        expTime = (config['exposure']['exposureTime'] /
                   config[mode]['efficiency'])
        maxLeftoverTime = config[mode]['maxLeftoverTime']

        while remainingTime >= maxLeftoverTime:

            optimalPlate = getOptimalPlate(
                self._plates, currentTime, self.endTime, expTime=expTime,
                **kwargs)

            if optimalPlate is None:
                warnings.warn('no valid plates found at JD={0:.4f} '
                              '(timeline ends at JD={1:.4f})'.format(
                                  currentTime, self.endTime),
                              TotoroUserWarning)
                currentTime += config['exposure']['exposureTime'] / 86400.

            else:
                self._replaceWithOptimal(optimalPlate)
                newTime = optimalPlate.getLastExposure().getJDObserved()[1]
                currentTime = newTime

            remainingTime = JDdiff(currentTime, self.endTime)

        return

    def _getNNewExposures(self, optimalPlate):

        for ii in range(len(self._plates)):
            if self._plates[ii].location_id == optimalPlate.location_id:
                return (len(optimalPlate.getValidExposures()) -
                        len(self._plates[ii].getValidExposures()))

    def _replaceWithOptimal(self, optimalPlate):

        for ii in range(len(self._plates)):
            if self._plates[ii].location_id == optimalPlate.location_id:
                self._plates[ii] = optimalPlate.copy()

    def _observePlate(self, plate, startTime=None, endTime=None,
                      calibrations=True, **kwargs):

        startTime = self.startTime if startTime is None else startTime
        endTime = self.endTime if endTime is None else endTime

        return

    def getExposures(self):

        exposures = []
        for plate in self._plates:
            exposures += plate.getValidExposures()

        timelineExposures = []
        for exp in exposures:
            expJD0, expJD1 = exp.getJDObserved()
            if expJD0 >= self.startTime and expJD1 <= self.endTime:
                timelineExposures.append(exp)

        return timelineExposures

    def printExposures(self):

        exposures = self.getExposures()

        jdArray = np.array([exp.getJDObserved() for exp in exposures],
                           dtype=[('JD0', float), ('JD1', float)])

        jdArray.sort(order='JD0')

        print(jdArray)