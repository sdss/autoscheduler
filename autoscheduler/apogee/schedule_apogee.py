from __future__ import print_function, division
from time import time

from get_apogee_plates import get_plates
from set_apogee_priorities import set_priorities
from observability import observability
from pick_apogee_plates import pick_plates

# SCHEDULE_APOGEE
# DESCRIPTION: Main APOGEE-II scheduling routine.
# INPUT: schedule -- dictionary defining important schedule times throughout the night
# OUTPUT: apogee_choices -- dictionary list containing plate choices + observing times for tonight 
def schedule_apogee(schedule, plan=False):
	# Define APOGEE-II observing parameters
	par = {'exposure': 67, 'overhead': 20, 'ncarts': 9, 'maxz': 3, 'moon_threshold': 15, 'sn_target': 3136}

	# Define APOGEE-II blocks for tonight
	nightlength = (schedule['bright_end'] - schedule['bright_start']) * 24
	nslots = min([int(nightlength / ((par['exposure'] + par['overhead']) / 60)), par['ncarts']])
	if nslots == 0: return []
	times = [schedule['bright_start'] + (par['exposure'] + par['overhead']) / 60 / 24 * x for x in range(nslots)]
	lengths = [(par['exposure'] + par['overhead']) / 60 for x in range(nslots)]
	
	# If APOGEE-II starts the split night
	if schedule['bright_start'] < schedule['dark_start']:
		# Determine whether we should add another exposure (leftover time > 30min)
		if len(times) < par['ncarts'] and nightlength - sum(lengths) > 0.5:
			times.append(schedule['bright_start'] + len(times) * (par['exposure'] + par['overhead']) / 60 / 24)
			lengths.append(par['exposure'] / 60)
		# Because APOGEE-II is first, the last exposure will not have overhead
		lengths[-1] = par['exposure'] / 60
	
	# APOGEE-II ends the night
	else:
		# Determine whether we can add an exposure (leftover time > 15min)
		if len(times) < par['ncarts'] and nightlength - sum(lengths) > (15/60 + par['overhead'] / 60):
			times.append(schedule['bright_start'] + len(times) * (par['exposure'] + par['overhead']) / 60 / 24)
			lengths.append(nightlength - sum(lengths))

	# Get all plate information from the database
	apg = get_plates(plan=plan)
	
	# Prioritize all plates
	set_priorities(apg, par, schedule)
	
	# Determine observability range of all plates
	obs = observability(apg, par, times, lengths)
	
	# Pick plates for tonight
	picks = pick_plates(apg, obs, par, times, lengths, schedule)
	
	return picks

		
		
	