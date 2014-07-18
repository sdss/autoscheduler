#!/usr/bin/python

'''
This file contains all custom Jinja2 filters.
'''

import datetime

#from hooloovookit.astro import convert

def j2split(value, delimiter=None):
	if delimiter == None:
		return value.split()
	else:
		return value.split(delimiter)

def j2join(value, delimiter=","):
    return delimiter.join(value)

def j2hasSurvey(surveyListTuple):
    survey, aList = surveyListTuple
    return survey.lower() in [x.display_string.lower() for x in aList]

def j2hasBossSurvey(surveys):
    return "BOSS" in [x.display_string for x in surveys]

def j2hasZeroLen(aList):
    return len(aList)==0

#def mjd2date(mjd):
#	d = mjd2datetime(mjd)
#	return d.strftime('%Y.%m.%d')

