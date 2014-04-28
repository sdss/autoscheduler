from __future__ import print_function, division
from time import time
import numpy as np
import astropysics.coords as coo
import astropysics.obstools as obs
from moonpos import moonpos

def observability(apg, par, times, lengths):
	apo = obs.Site(32.789278, -105.820278)
	obsarr = np.zeros([len(apg), len(times)])
	
	# Loop over all plates
	for p in range(len(apg)):
		# Initalize obsarr row
		for t in range(len(times)): obsarr[p,t] = apg[p].priority
		
		# Compute observing constants
		apyscoo = coo.ICRSCoordinates(apg[p].ra, apg[p].dec)
		transitmjd = obs.calendar_to_jd(apo.nextRiseSetTransit(apyscoo, dtime=obs.jd_to_calendar(times[0]))[2])
		if transitmjd - int(times[0]) > 1: transitmjd -= 1
		if transitmjd - int(times[0]) < -1: transitmjd += 1
		
		# Gaussian prioritization on time from transit
		for t in range(len(times)): 
			obsarr[p,t] += 50.0 * float(np.exp( -(transitmjd - times[t]+lengths[t]/2/24)**2 / (2 * (15)**2)))
		
		# Moon avoidance
		for t in range(len(times)):
			moonra, moondec = moonpos(times[t])
			mooncoo = coo.ICRSCoordinates(moonra, moondec)
			moondist = mooncoo - apyscoo
			if moondist.d < par['moon_threshold']: obsarr[p,t] = -3
		
		# Determine whether HAs of block are within observational range
		for t in range(len(times)):
			if obsarr[p,t] < 0: continue
		
			if (transitmjd - times[t]) * 15 < apg[p].minha: obsarr[p,t] = -1
			if (times[t]+lengths[t]/24 - transitmjd) * 15 > apg[p].maxha: obsarr[p,t] = -1
		
			# Compute horiztonal coordinates
			horz = apo.apparentCoordinates(apyscoo, datetime=[times[t] + lengths[t] / 5 / 24 * x for x in range(5)])
			secz = [1/np.cos((90.0 - horz[x].alt.d) * np.pi / 180) for x in range(len(horz))]
			# Check whether any of the points contain a bad airmass value
			badsecz = [x for x in secz if x < 1.003 or x > par['maxz']]
			if len(badsecz) > 0: obsarr[p,t] = -2

	return obsarr
