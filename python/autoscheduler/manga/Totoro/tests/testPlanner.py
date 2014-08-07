#!/usr/bin/env python
# encoding: utf-8
"""
testPlanner.py

Created by José Sánchez-Gallego on 11 Dec 2013.
Copyright (c) 2013. All rights reserved.
Licensed under a 3-clause BSD license.

"""

from __future__ import division
from __future__ import print_function
from Totoro.scheduler import Planner


def testPlanner():

    pp = Planner(startDate=2456918.0, endDate=2456930.0)
    pp.scheduleTimelines()

    return pp


if __name__ == '__main__':
    testPlanner()
