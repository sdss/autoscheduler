# ---- SDSS-IV AUTOSCHEDULER ----
# DESCRIPTION: Wrapping layer to all 3 surveys' scheduling modules
#__author__ = 'Ben Thompson <b.a.thompson1@tcu.edu>'

# Import necessary modules
from __future__ import print_function, division
import autoscheduler
import autoscheduler.apogee as apg
from time import time
import os

def run_scheduler(plan=False):
	as_start_time = time()
	
	# Read in schedule file
	pwd = os.path.dirname(os.path.realpath(__file__))
	schedule_start_time = time()
	schedule = autoscheduler.read_schedule(pwd+'/schedules/Sch_base.sdss3.txt')
	# Determine what line in the schedule to use for tonight
	tonight = round(autoscheduler.get_juldate())
	currjd = [x for x in range(len(schedule)) if schedule[x]['jd'] == 2456733]
	if not len(currjd) > 0:
		raise AssertionError, "MJD %5d does not exist in schedule file." % (tonight-2400000)
	currjd = currjd[0]
	schedule_end_time = time()
	print("[PY] Schedule read in complete (%3.1f min)" % ((schedule_end_time - schedule_start_time)/60.0))
	
	print ("[PY] Scheduling MJD %5d" % (tonight-2400000))
	
	# Schedule surveys for tonight
	apogee_choices, manga_choices, eboss_choices = [], [], []
	# Schedule APOGEE-II
	if schedule[currjd]['bright_start'] > 0:
		apogee_choices = apg.schedule_apogee(schedule[currjd], plan=plan)
	# Schedule MaNGA
	#if schedule[currjd]['manga'] > 0:
	#	manga_choices = schedule_manga(schedule[currjd])
	# Schedule eBOSS
	#if schedule[currjd]['eboss'] > 0:
	#	eboss_choices = schedule_eboss(schedule[currjd])
	
	# Take results and assign to carts
	plugplan = autoscheduler.assign_carts(apogee_choices, manga_choices, eboss_choices)
	
	as_end_time = time()
	print("[PY] run_scheduler complete in (%3.1f min)" % ((as_end_time - as_start_time) / 60.0))
	
	return plugplan


