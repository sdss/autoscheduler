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
# from ..exceptions import TotoroError
from .observingPlan import ObservingPlan
from ..dbclasses import Fields
from .. import config
from .. import log


class BaseScheduler(object):
    """The base class for the autoscheduler.

    This class provides the common base to plan observations
    and is inherited by Scheduler, Plugger and Planner.

    """

    def __init__(self, startDate=None, endDate=None, **kwargs):

        self.observingPlan = ObservingPlan(**kwargs)
        self.createSite(**kwargs)
        self.setStartEndDate(startDate, endDate, **kwargs)

    def createSite(self, longitude=None, latitude=None, altitude=None,
                   name=None, **kwargs):

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

        self.site = obstools.Site(latitude, longitude, name=name, alt=altitude)

        log.info('Created site with name \'{0}\''.format(name))

    def setStartEndDate(self, startDate, endDate, scope='planner', **kwargs):
        """Sets the start and end date if they haven't been defined."""

        if startDate is None:
            # Uses the current LST
            startDate = obstools.calendar_to_jd(None)

        if startDate < self.observingPlan.getSurveyStart():
            startDate = self.observingPlan.getSurveyStart()

        if endDate is None:
            endDate = self.observingPlan.getSurveyEnd()

        if scope == 'planner':
            startDate = int(startDate)
            endDate = int(endDate) + 1

        self.startDate = startDate
        self.endDate = endDate

        log.info('Adjusted start date: {0}'.format(self.startDate))
        log.info('Adjusted end date: {0}'.format(self.endDate))

    def getObservingBlocks(self):
        """Return a table with the observing blocks."""

        return self.observingPlan.getObservingBlocks(
            self.startDate, self.endDate)


class Planner(BaseScheduler):

    def __init__(self, startDate=None, endDate=None, **kwargs):

        log.info('Running in PLANNER MODE.')

        super(Planner, self).__init__(startDate=startDate,
                                      endDate=endDate, scope='planner',
                                      **kwargs)

        self.getFields()

    def getFields(self, **kwargs):
        """Gets a table with the fields that can be scheduled."""

        log.info('Beginning to load fields from DB.')
        self.fields = Fields(rejectCompleted=True, **kwargs)

    # def simulate(self):
    #     """Applies the scheduling logic and returns the planner schedule."""

    #     for row in self.observingPlan[0:2]:
    #         startJD = time.Time(row[SURVEY() + '_0'], scale='utc', format='jd')
    #         endJD = time.Time(row[SURVEY() + '_1'], scale='utc', format='jd')
    #         self._observeNight(startJD, endJD)

    # def _observeNight(self, startJD, endJD):

    #     def remainingTime(tt):
    #         return (endJD - tt).sec

    #     self.fields.plugFields(startJD, endJD)
    #     currentTime = startJD

    #     while remainingTime(currentTime) > ONE_EXPOSURE:
    #         print(currentTime)
    #         fieldToObserve = self.fields.getOptimumField(currentTime)
    #         currentTime = fieldToObserve.observe(currentTime, until=endJD)
    #         print(currentTime)
    #         if currentTime is None:
    #             print('Help!!!')
