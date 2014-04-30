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
		print(nleft, max(obs[p,:]))
		# Plate is complete or no longer observable, we can't keep it plugged
		if nleft == 0 or max(obs[p,:]) < 0:
			for t in range(len(times)): obs[p,t] = -10
			continue
		# Find optimal slots to choose
		optslot = [x for x in range(len(times)) if obs[p,x] == max(obs[p,:])][0]
		centerslot = int(round(nleft / 2)-1)
		# Optimal slot is too close to beginning of night, start from beginning
		if optslot < centerslot:
			for i in range(nleft): chosen[i] = ebo[p].plateid
		# Optimal slot is too close to end of night, start from end
		elif optslot > len(times)-nleft+centerslot:
			for i in range(nleft): chosen[-i-1] = ebo[p].plateid
		# Optimal range is wholly within the night, place it
		else:
			for i in range(nleft): chosen[optslot-centerslot+i] = ebo[p].plateid
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
