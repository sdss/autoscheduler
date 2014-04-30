from __future__ import print_function, division
from time import time
import numpy as np

from get_eboss_plates import get_plates
from observability import observability

# SCHEDULE_EBOSS
# DESCRIPTION: Main eBOSS scheduling routine.
# INPUT: schedule -- dictionary defining important schedule times throughout the night
# OUTPUT: eboss_choices -- dictionary list containing plate choices + observing times for tonight 
def schedule_eboss(schedule, plan=False):
	# Define eBOSS observing parameters
	par = {'exposure': 16.5, 'ncarts': 8, 'maxz': 2.0, 'moon_threshold': 30, 'snr_avg': 9.0, 'snb_avg': 4.0, 'snr': 25, 'snb': 10}
	
	# Divide eBOSS time into blocks
	times = np.arange(schedule['eboss_start'], schedule['eboss_end'], par['exposure']/60/24)

	# Get all plate information from the database
	ebo = get_plates(plan=plan)
	
	# Determine observability
	obs = observability(ebo, par, times)

	return []


		
		
	
