#!/usr/bin/env python
# encoding: utf-8
"""
scheduler.py

Created by José Sánchez-Gallego on 17 Feb 2014.
Licensed under a 3-clause BSD license.

Revision history:
    17 Feb 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from astropysics import obstools
from .observingPlan import ObservingPlan
from ..dbclasses import Fields
from ..dbclasses import Plates
from ..utils import createSite
from .timeline import Timelines
from ..exceptions import TotoroNotImplemented
from .. import log


class BaseScheduler(object):
    """The base class for the autoscheduler.

    This class provides the common base to plan observations
    and is inherited by Scheduler, Plugger and Planner.

    """

    def __init__(self, startDate=None, endDate=None, **kwargs):

        self._observingPlan = ObservingPlan(**kwargs)
        self.site = createSite(**kwargs)
        self._setStartEndDate(startDate, endDate, **kwargs)

        self.observingBlocks = self._observingPlan.getObservingBlocks(
            self.startDate, self.endDate)

    def _setStartEndDate(self, startDate, endDate, scope='planner', **kwargs):
        """Sets the start and end date if they haven't been defined."""

        if scope == 'planner':
            if startDate is None:
                startDate = obstools.calendar_to_jd(None)
            if endDate is None:
                endDate = self._observingPlan.getSurveyEnd()

            startDate = self._observingPlan.getClosest(startDate)['JD0']
            endDate = self._observingPlan.getClosest(endDate)['JD1']

        elif scope == 'nightly':
            # if startDate is None:
            startDate = 2456889
            startDate = self._observingPlan.getJD(startDate)[0]
            # if endDate is None:
            endDate = 2456889
            endDate = self._observingPlan.getJD(endDate)[1]

        elif scope == 'plugger':
            startDate, endDate = self._observingPlan.getJD(startDate)
            # endDate = self._observingPlan.getJD(startDate)[1]

        self.startDate = startDate
        self.endDate = endDate
        self.currentDate = obstools.calendar_to_jd(None)

        log.info('Adjusted start date: {0}'.format(self.startDate))
        log.info('Adjusted end date: {0}'.format(self.endDate))


class Planner(BaseScheduler):

    def __init__(self, startDate=None, endDate=None, **kwargs):

        log.info('Running in PLANNER MODE.')

        super(Planner, self).__init__(startDate=startDate,
                                      endDate=endDate, scope='planner',
                                      **kwargs)

        self.fields = self.getFields()

    def getFields(self, rejectDrilled=True, **kwargs):
        """Gets a table with the fields that can be scheduled."""

        log.info('Finding fields with rejectDrilled={0}'.format(rejectDrilled))
        fields = Fields(rejectDrilled=rejectDrilled, **kwargs)

        log.info('Found {0} fields'.format(len(fields)))

        return fields

    def scheduleTimelines(self):
        """Creates simulated timelines for the observing blocks."""

        self.timelines = Timelines(
            self.observingBlocks, plates=self.fields, mode='planner')
        self.timelines.schedule()


class Plugger(BaseScheduler):

    def __init__(self, date=None, **kwargs):

        super(Plugger, self).__init__(startDate=date, endDate=None,
                                      scope='plugger', **kwargs)

        self.plates = self.getPlatesAtAPO()

    def getPlatesAtAPO(self, rejectComplete=True):

        log.info('Getting plates at APO with rejectComplete={0}'.format(
                 rejectComplete))

        plates = Plates(onlyPlugged=False, onlyAtAPO=True,
                        onlyIncomplete=rejectComplete)

        log.info('Plates found: {0}'.format(len(plates)))

        return plates

    def getOutput(self):

        self.timelines = Timelines(
            self.observingBlocks, plates=self.plates, mode='plugger')

        self.timelines.schedule()


class Nightly(BaseScheduler):

    def __init__(self, startDate=None, endDate=None, plates=None, **kwargs):

        log.info('Running in NIGHTLY MODE.')

        super(Nightly, self).__init__(startDate=startDate,
                                      endDate=endDate, scope='nightly',
                                      **kwargs)

        if plates is None:
            self.plates = self.getPlates()
        else:
            self.plates = plates

    def getPlates(self, **kwargs):
        """Gets the plugged plates."""

        log.info('Finding plugged plates.')
        plates = Plates(onlyPlugged=False, onlyAtAPO=True,
                        onlyIncomplete=False, rearrageExposure=True,
                        **kwargs)

        if len(plates) == 0:
            log.info('no plugged plates found.')

        return plates

    def printTabularOutput(self):
        """Prints a series of tables with information about the schedule."""

        from .. import output

        output.printTabularOutput(self.plates)

    def getTabularOutput(self):

        from .. import output

        return output.getTabularOutput(self.plates)

    def getOutput(self, format='dict'):
        """Returns the nightly output in the selected format."""

        from .. import output

        return output.getNightlyOutput(self, format=format)
