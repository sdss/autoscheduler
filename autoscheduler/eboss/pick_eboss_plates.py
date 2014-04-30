from __future__ import print_function, division
from time import time
import numpy as np


def pick_plates(ebo, par, times, obs):
	# Setup
	chosen = [-1 for x in times]

	# First loop through already-plugged plates and place them
	pickplug_start = time()
	for p in range(len(ebo)):
		if ebo[p].plugged == 0: continue
		nleft = ebo[p].visleft(par)
		# Plate is complete or no longer observable, we can't keep it plugged
		if nleft == 0 or max(obs[p,:]) < 0:
			for t in range(len(times)): obs[p,t] = -10
			continue
		# Find optimal slots to choose
		optslot = [x for x in range(len(times)) if obs[p,x] == max(obs[p,:])][0]
		centerslot = int(round(nleft / 2)-1)
		# Optimal slot is too close to beginning of night, start from beginning
		if optslot < centerslot: startslot = 0
		# Optimal slot is too close to end of night, start from end
		elif optslot > len(times)-nleft+centerslot: startslot = len(times) - nleft - 1
		# Optimal range is wholly within the night, place it
		else: startslot = optslot-centerslot
		
		# Determine whether any adjustments are necessary due to alread-plugged plates
		if chosen[startslot] >= 0: startslot += 1
		if chosen[startslot+nleft] >= 0: startslot -1
		
		# Mark slots as chosen
		for i in range(nleft):
			if startslot+i >= len(chosen): continue
			chosen[startslot+i] = ebo[p].plateid
		# Remove plate from further picking
		for t in range(len(times)): obs[p,t] = -10
	pickplug_end = time()
	print("[PY] Placed eBOSS already-plugged plates (%.3f sec)" % (pickplug_end - pickplug_start))
			
	# Loop through all un-scheduled blocks and place plates
	# TO-DO

	print(chosen)
	
	# Return all chosen plates
	chosenplates = np.unique(chosen)
	eboss_choices = []
	for p in chosenplates:
		eboss_choices.append({'plate': p})
	return eboss_choices
