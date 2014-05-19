from __future__ import print_function, division
from time import time
import numpy as np
import astropysics.coords as coo
import astropysics.obstools as obs
from ..moonpos import moonpos

def observability(apg, par, times, lengths, loud=True):
	obs_start = time()
	apo = obs.Site(32.789278, -105.820278)
	obsarr = np.zeros([len(apg), len(times)])
	beglst = [apo.localSiderialTime(x) for x in times]
	endlst = [apo.localSiderialTime(times[x] + lengths[x]/24) for x in range(len(times))]

	# Determine moon coordinates
	mpos = []
	for t in range(len(times)):
		moonra, moondec = moonpos(times[t])
		mpos.append(coo.ICRSCoordinates(moonra, moondec))
	
	# Loop over all plates
	for p in range(len(apg)):
		# Initalize obsarr row
		if apg[p].priority <= 0: continue
		for t in range(len(times)): obsarr[p,t] = apg[p].priority
		
		# Compute observing constants
		platecoo = coo.ICRSCoordinates(apg[p].ra, apg[p].dec)
		platelst = float(apg[p].ra + apg[p].ha) / 15
		minlst = platelst + float(apg[p].minha) / 15
		maxlst = platelst + float(apg[p].maxha) / 15
		
		for t in range(len(times)):
			# Gaussian prioritization on time from transit
			obsarr[p,t] += 50.0 * float(np.exp( -(platelst - (beglst[t]+endlst[t])/2 + lengths[t]/2)**2 / 2))

			# Moon avoidance
			moondist = mpos[t] - platecoo
			if moondist.d < par['moon_threshold']:
				obsarr[p,t] = -3
				continue
		
			# Determine whether HAs of block are within observational range
			if beglst[t] < minlst or endlst[t] > maxlst: 
				obsarr[p,t] = -1
				continue
		
			# Compute horiztonal coordinates
			horz = apo.apparentCoordinates(platecoo, datetime=[times[t] + lengths[t] / 2 / 24 * x for x in range(3)])
			secz = [1/np.cos((90.0 - horz[x].alt.d) * np.pi / 180) for x in range(len(horz))]
			# Check whether any of the points contain a bad airmass value
			badsecz = [x for x in secz if x < 1.003 or x > par['maxz']]
			if len(badsecz) > 0: obsarr[p,t] = -2
			
	obs_end = time()
	if loud: print("[PY] Determined APOGEE-II observability (%.3f sec)" % (obs_end - obs_start))

	
	return obsarr
