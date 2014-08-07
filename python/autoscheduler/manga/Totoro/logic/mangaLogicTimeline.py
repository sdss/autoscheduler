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
from ..utils import createSite, JDdiff
from ..utils import getIntervalIntersection, isPointInInterval
from .. import config
from astropy import table


site = createSite()


def getOptimalPlate(plates, JD0, JD1, **kwargs):

    LST0 = site.localSiderialTime(JD0)
    LST1 = site.localSiderialTime(JD1)

    if len(plates) == 0:
        return None

    plateCompletion = [
        simulateCompletionStatus(
            plate, JD0, JD1, LST0=LST0, LST1=LST1, **kwargs)
        for plate in plates
    ]

    completionTable = table.Table(rows=plateCompletion,
                                  names=['plate', 'completion', 'nSets',
                                         'blueSN2', 'redSN2', 'nNewExp'])

    completionTable = completionTable[completionTable['nNewExp'] > 0]

    if len(completionTable) == 0:
        return None
    completionTable.sort('completion')
    return completionTable['plate'][-1]
    # if len(completionTable[completionTable['completion'] >= 1.]) > 0:

    #     idx = np.where(completionTable['completion'] >= 1.)
    #     selectedStatus = completionTable[idx]
    #     selectedStatus.sort('nSets')

    #     if len(selectedStatus[selectedStatus['nSets'] ==
    #            selectedStatus['nSets'][0]]) > 0:

    #         idx = np.where(selectedStatus[selectedStatus['nSets'] ==
    #                        selectedStatus['nSets'][0]])

    #         selectedStatus = selectedStatus[idx]

    #         selectedStatus.sort('completion')
    #         selectedStatus.reverse()

    #         return selectedStatus['plate'][0]

    #     else:

    #         return selectedStatus['plate'][0]

    # else:

    #     completionTable.sort('completion')
    #     return completionTable['plate'][-1]


def getVisiblePlates(plates, LST0, LST1, **kwargs):

    from ..dbclasses import Plates

    return Plates.fromList(
        [plate for plate in plates
         if isPointInInterval(LST0, plate.getLSTRange())])


def getIncompletePlates(plates):

    from ..dbclasses import Plates

    return Plates.fromList(
        [plate for plate in plates
         if not plate.getPlateCompletion(includeIncompleteSets=True)[0]])


def getPlatesWithEnoughTime(plates, JD0, JD1):

    from ..dbclasses import Plates

    pp = []

    LST0 = site.localSiderialTime(JD0)
    LST1 = site.localSiderialTime(JD1)

    for plate in plates:

        plateLST0, plateLST1 = getIntervalIntersection((LST0, LST1),
                                                       plate.getLSTRange(),
                                                       wrapAt=24)

        plateJD0 = JD0 + (plateLST0 - LST0) % 24 / 24.
        plateJD1 = JD0 + (plateLST1 - LST0) % 24 / 24.

        expTime = config['exposure']['exposureTime'] / \
            config['simulation']['efficiency']

        currentJD = plateJD0
        remainingTime = JDdiff(currentJD, plateJD1)

        if remainingTime > expTime:
            pp.append(plate)

    return Plates.fromList(pp)


def simulateCompletionStatus(plate, JD0, JD1, **kwargs):

    simulatedPlate, nNewExp = simulateExposures(plate, JD0, JD1, **kwargs)

    sn2Array = simulatedPlate.getCumulatedSN2(includeIncomplete=True)
    blueSN2 = np.mean(sn2Array[0:])
    redSN2 = np.mean(sn2Array[2:])

    nSets = len(simulatedPlate.sets)

    completion = np.array([blueSN2 / config['SN2thresholds']['plateBlue'],
                           redSN2 / config['SN2thresholds']['plateRed']])

    return (simulatedPlate, np.min(completion),
            nSets, blueSN2, redSN2, nNewExp)


def simulateExposures(plate, JD0, JD1, LST0=None, LST1=None, expTime=None,
                      maxLeftoverTime=None, **kwargs):

    LST0 = site.localSiderialTime(JD0) if LST0 is None else LST0
    LST1 = site.localSiderialTime(JD1) if LST1 is None else LST1

    plateLSTRange = plate.getLSTRange()
    if not isPointInInterval(LST0, plateLSTRange):
        return (plate, 0)

    plateLST0, plateLST1 = getIntervalIntersection((LST0, LST1),
                                                   plate.getLSTRange(),
                                                   wrapAt=24)

    plateJD0 = JD0
    plateJD1 = JD0 + (plateLST1 - LST0) % 24 / 24.

    cPlate = plate.copy()

    currentJD = plateJD0
    remainingTime = JDdiff(currentJD, plateJD1)

    if expTime is None:
        expTime = config['exposure']['exposureTime']

    if maxLeftoverTime is None:
        maxLeftoverTime = expTime

    nNewExposures = 0

    while remainingTime >= 0:

        if cPlate.getPlateCompletion(includeIncompleteSets=True)[0]:
            break

        cPlate.addMockExposure(set=None, startTime=currentJD, expTime=expTime)
        nNewExposures += 1
        currentJD += expTime / 86400.
        remainingTime = JDdiff(currentJD, plateJD1)

    return (cPlate, nNewExposures)
