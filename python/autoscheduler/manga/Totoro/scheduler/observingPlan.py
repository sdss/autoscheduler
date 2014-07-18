#!/usr/bin/env python
# encoding: utf-8
"""
observingPlan.py

Created by José Sánchez-Gallego on 11 Dec 2013.
Copyright (c) 2013. All rights reserved.
Licensed under a 3-clause BSD license.

"""

from __future__ import division
from __future__ import print_function
from astropy import table
from ..exceptions import TotoroError
from .. import config, log
import numpy as np
import os


class ObservingPlan(object):
    """The survey-wide observing plan object.

    Parameters
    ----------
    plan : str or `astropy.tableTable`
        A file pth containing the observing plan or an astropy table
        with the data.
    format : str
        The input format of the plan. The options are 'autoscheduler',
        'autoscheduler.utc', 'autoscheduler.jd', 'sidereal', 'utc' or 'jd'.
    useOptimisedPlan : bool
        It True, tries to read the optimised file (in JD format) for the
        input plan. This notably improves performance.
    saveOptimisedPlan : bool
        If True, once the input observing plan has been converted to JD,
        saves it to the configuration directory. This optimised file will
        later be read if useOptimisedPlan is True.
    survey : str
        If None, the observing plan for all plans will be kept, but survey
        will need to be defined for some methods.

    """

    def __init__(self, schedule=None, **kwargs):

        if schedule is None:
            schedule = config['observingPlan']['schedule']

        if schedule[0] == '+':
            schedule = os.path.join(os.path.dirname(__file__),
                                    '../' + schedule[1:])

        if not os.path.exists(schedule):
            raise TotoroError('schedule {0} not found'.format(schedule))

        self.plan = table.Table.read(schedule, format='ascii.no_header')
        self.plan.keep_columns(['col1', 'col11', 'col12'])
        self.plan.rename_column('col1', 'JD')
        self.plan.rename_column('col11', 'JD0')
        self.plan.rename_column('col12', 'JD1')

        log.info('Observing plan {0} loaded.'.format(schedule))

        self.addRunDayCol()
        self.plan = self.plan[(self.plan['JD0'] > 0) & (self.plan['JD1'] > 0)]

    def addRunDayCol(self):
        """Adds a column with the night within the run."""

        nDay = 1
        nRun = 1
        ll = []
        run = []

        for row in self.plan:
            if row['JD0'] != 0.:
                ll.append(nDay)
                run.append(nRun)
                nDay += 1
            else:
                ll.append(-1)
                run.append(-1)
                nDay = 1
                nRun += 1

        self.plan.add_column(table.Column(data=run, name='RUN', dtype=int))
        self.plan.add_column(table.Column(data=ll, name='RUN_DAY', dtype=int))

    def getSurveyStart(self):
        """Gets the start of survey."""

        validDates = self.plan[self.plan['JD0'] > 0.0]
        startTime = validDates[0]['JD0']
        return startTime

    def getSurveyEnd(self):
        """Gets the end of survey."""

        validDates = self.plan[self.plan['JD1'] > 0.0]
        endTime = validDates[-1]['JD1']
        return endTime

    # def getClosest(self, dd, survey=SURVEY()):

    #     tt = self.data[self.data[self.survey + '_1'] >= dd.jd]

    #     idxStart = (np.abs(tt[self.survey + '_0'] - dd.jd)).argmin()
    #     idxEnd = (np.abs(tt[self.survey + '_1'] - dd.jd)).argmin()

    #     return (tt[idxStart][self.survey + '_0'],
    #             tt[idxEnd][self.survey + '_1'])

    def getMaNGAStart(self, startDate):
        """Returns the JD of the start of the MaNGA observation for a given
        start date."""

        day = self[self['JD'] == int(startDate)]
        return day['JD0'][0]

    def getMaNGAEnd(self, startDate):
        """Returns the JD of the end of the MaNGA observation for a given
        start date."""

        day = self[self['JD'] == int(startDate)]
        return day['JD1'][0]

    def getObservingBlocks(self, startDate, endDate):
        """Returns an astropy table with the observation dates
        for each night between startDate and endDate."""

        log.info('Getting observing block.')

        validDates = self.plan[(self.plan['JD1'] >= int(startDate)) &
                               (self.plan['JD0'] <= int(endDate)) &
                               (self.plan['JD0'] > 0.0) &
                               (self.plan['JD1'] > 0.0)]

        if startDate > validDates['JD0'][0]:
            validDates['JD0'][0] = startDate

        if endDate < validDates['JD1'][-1]:
            validDates['JD1'][-1] = endDate

        totalTime = np.sum([row['JD1'] - row['JD0'] for row in validDates])
        log.info(('{0} blocks (days) selected, '
                  'making a total of {1:.1f} days').format(len(validDates),
                                                           totalTime))

        return validDates

    def __repr__(self):
        return self.plan.__repr__()

    def __str__(self):
        return self.plan.__str__()

    def __getitem__(self, slice):
        return self.plan[slice]
