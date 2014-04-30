from __future__ import print_function, division
from time import time
import numpy as np

def pick_plates(apg, obs, par, times, lengths, schedule):
	pick_start = time()
	# Check how many plates are available in each slot
	nslot = np.zeros(len(times))
	for t in range(len(times)):
		wgood = [x for x in range(len(apg)) if obs[x,t] > 0]
		nslot[t] = len(wgood)
	
	# Loop through slots to choose in availability order
	chosen = np.zeros([len(times), 3], dtype=np.int)
	pickorder = np.argsort(nslot)
	for t in range(len(times)):
		cslot = pickorder[t]
		priorder = np.argsort(obs[:,cslot])
		# Pick main plate
		if obs[priorder[-1],cslot] <= 0:
			print("[WARN] No good APG-II plates for block %1d. Max priority = %4.1f" % (cslot, max(obs[:,cslot])))
			chosen[cslot,0] = -1
		else: chosen[cslot,0] = priorder[-1]
		# Pick backup plates
		if obs[priorder[-2],cslot] <= 0: chosen[cslot,1] = -1
		else: chosen[cslot,1] = priorder[-2]
		if obs[priorder[-3],cslot] <= 0: chosen[cslot,2] = -1
		else: chosen[cslot,2] = priorder[-3]
		
		# Remove chosen plate, if it is not stack-able.
		if apg[chosen[cslot,0]].stack == 0:
			for i in range(len(times)):
				if i != cslot: obs[chosen[cslot,0],i] = -10
		# This plate is stack-able, only remove non-adjacent blocks
		else:
			for i in range(len(times)): 
				if abs(i-cslot) > 1: obs[chosen[cslot,0],i] = -10
		
	# Check for stacked fields
	for t in range(len(times)-1):
		if chosen[t,0] < 0: continue
		if chosen[t,0] != chosen[t+1,0]: continue
		print("[PY] APG-II stack chosen")
		# Create new arrays
		newtimes, newlengths, newchosen = np.zeros(len(times)-1), np.zeros(len(times)-1), np.zeros([len(times)-1,3])
		# Loop through previous blocks
		for i in range(t):
			newtimes[i] = times[i]
			newlengths[i] = lengths[i]
			newchosen[i,:] = chosen[i,:]
		# Combine current block and next block
		newtimes[t] = times[t]
		newlengths[t] = lengths[t] + lengths[t+1]
		newchosen[t,:] = chosen[t,:]
		# Save all blocks after merged ones
		for i in range(t+2,len(times)):
			newtimes[i-1] = times[i]
			newlengths[i-1] = lengths[i]
			newchosen[i-1,:] = chosen[i,:]
		# Overwrite old arrays
		times, lengths, chosen = newtimes, newlengths, newchosen
	pick_end = time()
	print("[PY] Chose APOGEE-II plates (%.3f sec)" % (pick_end - pick_start))
	
	# Create output struct
	picks = []
	for c in range(len(chosen[:,0])):
		# Strip overhead time from exposure length, if this is a full block
		if lengths[c] >= par['exposure']/60: thislength = lengths[c] - par['overhead']/60
		else: thislength = lengths[c]
		# Determine where block actually starts
		if schedule['dark_start'] == 0: thistime = times[c]
		elif schedule['bright_start'] < schedule['dark_start']: thistime = times[c]
		else:
			if lengths[c] >= par['exposure']/60: thistime = times[c]
			else: thistime = times[c] + par['overhead']/60/24
			
		# Determine block choices
		if chosen[c,0] < 0: thisplate = -1
		else: thisplate = apg[chosen[c,0]].plateid
		if chosen[c,1] < 0: thisbak1 = -1
		else: thisbak1 = apg[chosen[c,1]].plateid
		if chosen[c,2] < 0: thisbak2 = -1
		else: thisbak2 = apg[chosen[c,2]].plateid
	
		picks.append({'obstime': thistime, 'explength': thislength, 'plate': thisplate, 'first_backup': thisbak1, 'second_backup': thisbak2})
		
	return picks
	
	
	
