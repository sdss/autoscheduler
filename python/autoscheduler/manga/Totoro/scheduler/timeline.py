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


class Timelines(list):

    def __init__(self, observingBlocks, plates=None, **kwargs):

        initList = []
        for row in observingBlocks:
            initList.append(Timeline(row['JD0'], row['JD1'], plates=plates))

        list.__init__(self, initList)

    def schedule(self, **kwargs):

        plates = self[0]._plates
        for timeline in self:
            timeline._plates = plates
            timeline.schedule(**kwargs)
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

    def schedule(self, **kwargs):

        log.info('Scheduling timeline with JD0={0:.4f}'.format(self.startTime))

        currentTime = self.startTime
        remainingTime = JDdiff(currentTime, self.endTime)

        while remainingTime > config['exposure']['exposureTime']:

            optimalPlate = getOptimalPlate(
                self._plates, currentTime, self.endTime, **kwargs)

            nNewExposures = self._getNNewExposures(optimalPlate)

            if optimalPlate is None or nNewExposures == 0:
                warnings.warn('no valid plates found at JD={0:.4f} '
                              '(timeline ends at JD={1:.4f})'.format(
                                  currentTime, self.endTime),
                              TotoroUserWarning)
                currentTime += config['exposure']['exposureTime'] / 86400.

            else:

                self._replaceWithOptimal(optimalPlate)
                currentTime = optimalPlate.getExposureRange()[1]

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
                self._plates[ii] = optimalPlate

    def _observePlate(self, plate, startTime=None, endTime=None,
                      calibrations=True, **kwargs):

        startTime = self.startTime if startTime is None else startTime
        endTime = self.endTime if endTime is None else endTime

        return
