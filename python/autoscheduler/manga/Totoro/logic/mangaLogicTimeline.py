#!/usr/bin/env python
# encoding: utf-8
"""
mangaLogicTimeline.py

Created by José Sánchez-Gallego on 3 Aug 2014.
Licensed under a 3-clause BSD license.

Revision history:
    3 Aug 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
import numpy as np
from ..utils import createSite, JDdiff, getIntervalIntersection
from .. import config
from astropy import table


site = createSite()


def getOptimalPlate(plates, JD0, JD1, **kwargs):

    LST0 = site.localSiderialTime(JD0)
    LST1 = site.localSiderialTime(JD1)

    visiblePlates = getVisiblePlates(plates, LST0, LST1, **kwargs)
    incompletePlates = getIncompletePlates(visiblePlates)

    if len(incompletePlates) == 0:
        return None

    plateCompletion = [simulateCompletionStatus(plate, JD0, JD1, **kwargs)
                       for plate in incompletePlates]

    completionTable = table.Table(rows=plateCompletion,
                                  names=['plate', 'completion', 'nSets',
                                         'blueSN2', 'redSN2'])

    if len(completionTable[completionTable['completion'] >= 1.]) > 0:

        idx = np.where(completionTable['completion'] >= 1.)
        selectedStatus = completionTable[idx]
        selectedStatus.sort('nSets')

        if len(selectedStatus[selectedStatus['nSets'] ==
               selectedStatus['nSets'][0]]) > 0:

            idx = np.where(selectedStatus[selectedStatus['nSets'] ==
                           selectedStatus['nSets'][0]])

            selectedStatus = selectedStatus[idx]

            selectedStatus.sort('blueSN2')
            selectedStatus.reverse()

            return selectedStatus['plate'][0]

        else:

            return selectedStatus['plate'][0]

    else:

        completionTable.sort('completion')
        return completionTable['plate'][-1]


def getVisiblePlates(plates, LST0, LST1, **kwargs):

    from ..dbclasses import Plates

    return Plates.fromList(
        [plate for plate in plates if plate.isVisible(LST0, LST1)])


def getIncompletePlates(plates):

    from ..dbclasses import Plates

    return Plates.fromList(
        [plate for plate in plates if plate.isComplete is False])


def simulateCompletionStatus(plate, JD0, JD1, **kwargs):

    simulatedPlate = simulateExposures(plate, JD0, JD1, **kwargs)

    sn2Array = simulatedPlate.getCumulatedSN2()
    blueSN2 = np.mean(sn2Array[0:])
    redSN2 = np.mean(sn2Array[2:])

    nSets = len(simulatedPlate.sets)

    completion = np.array([blueSN2 / config['SN2thresholds']['plateBlue'],
                           redSN2 / config['SN2thresholds']['plateRed']])

    return (simulatedPlate, np.min(completion), nSets, blueSN2, redSN2)


def simulateExposures(plate, JD0, JD1, **kwargs):

    LST0 = site.localSiderialTime(JD0)
    LST1 = site.localSiderialTime(JD1)

    plateLST0, plateLST1 = getIntervalIntersection((LST0, LST1),
                                                   plate.getLSTRange(),
                                                   wrapAt=24)

    plateJD0 = JD0 + (plateLST0 - LST0) % 24 / 24.
    plateJD1 = JD0 + (plateLST1 - LST0) % 24 / 24.

    expTime = config['exposure']['exposureTime'] / \
        config['simulation']['efficiency']

    cPlate = plate.copy()

    currentJD = plateJD0
    remainingTime = JDdiff(currentJD, plateJD1)

    while not cPlate.isComplete and remainingTime > expTime:
        cPlate.addMockExposure(set=None, startTime=currentJD, expTime=expTime)
        currentJD += expTime / 86400.
        remainingTime = JDdiff(currentJD, plateJD1)

    return cPlate
