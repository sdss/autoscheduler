#!/usr/bin/env python
# encoding: utf-8
"""
output.py

Created by José Sánchez-Gallego on 22 Jul 2014.
Licensed under a 3-clause BSD license.

Revision history:
    22 Jul 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from collections import OrderedDict
from ..exceptions import TotoroError
from ..scheduler import scheduler
from .. import dbclasses as dbC
import numpy as np
import yaml


__ALL__ = ['getNightlyOutput']


def getNightlyOutput(input=None, format='dict', **kwargs):

    if input is None:
        nightly = scheduler.Nightly(**kwargs)
    elif isinstance(input, scheduler.Nightly):
        nightly = input
    else:
        raise TotoroError('input format not supported.')

    output = OrderedDict()

    output['mangaStart'] = float(nightly.startDate)
    output['mangaEnd'] = float(nightly.endDate)
    output['currentTime'] = float(nightly.currentDate)

    # output['mangaPlugged'] = dbC.Plates.getPlates(onlyPlugged=True)

    # For future implementation
    output['schedule'] = None

    output['plates'] = OrderedDict()

    for plate in nightly.plates:

        output['plates'][plate.plate_id] = OrderedDict()
        thisPlate = output['plates'][plate.plate_id]

        thisPlate['complete'] = plate.isComplete
        thisPlate['HARange'] = np.array([-1., 1.]) * plate.mlhalimit
        thisPlate['UTVisibilityWindow'] = plate.getUTVisibilityWindow(
            format='datetime')
        thisPlate['SN2'] = plate.getCumulatedSN2()

        thisPlate['sets'] = OrderedDict()

        for set in plate.sets:

            thisPlate['sets'][set.pk] = OrderedDict()
            thisSet = thisPlate['sets'][set.pk]

            thisSet['complete'] = set.complete

            thisSet['averageSeeing'] = set.getAverageSeeing()
            thisSet['SN2'] = set.getSN2Array()

            thisSet['SN2Range'] = set.getSN2Range()
            thisSet['seeingRange'] = set.getSeeingRange()
            thisSet['UTRange'] = set.getUTVisibilityWindow(format='datetime')
            thisSet['HARange'] = set.getHALimits()
            thisSet['missingDithers'] = set.getMissingDitherPositions()

            thisSet['exposures'] = OrderedDict()

            for exposure in set.exposures:

                thisSet['exposures'][exposure.pk] = OrderedDict()
                thisExposure = thisSet['exposures'][exposure.pk]

                thisExposure['valid'] = exposure.valid
                thisExposure['ditherPosition'] = exposure.ditherPosition
                thisExposure['obsHARange'] = exposure.getHARange()
                thisExposure['obsJDRange'] = exposure.getJDObserved()

                thisExposure['seeing'] = exposure.seeing
                thisExposure['SN2'] = exposure.getSN2Array()

        if thisPlate['complete']:
            thisPlate['incompleteSets'] = []
        else:
            thisPlate['incompleteSets'] = OrderedDict(
                [(set, thisPlate['sets'][set])
                 for set in thisPlate['sets']
                 if thisPlate['sets'][set]['complete'] is False])

    if format == 'yaml':
        return yaml.dump(output, default_flow_style=False)

    return output
