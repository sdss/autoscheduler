from __future__ import print_function, division
from time import time
import numpy as np
import astropysics.coords as coo
import astropysics.obstools as obs
from sdss.utilities.idlasl import moonpos

def observability(apg, par, times, lengths, loud=True):
	obs_start = time()
	apo = obs.Site(32.789278, -105.820278)
	obsarr = np.zeros([len(apg), len(times)])
	beglst = [apo.localSiderialTime(x) for x in times]
	endlst = [apo.localSiderialTime(times[x] + lengths[x]/24) for x in range(len(times))]

	# Determine moon coordinates
	mpos = []
	for t in range(len(times)):
		mooncoords = moonpos(times[t])
		mpos.append(coo.ICRSCoordinates(mooncoords[0], mooncoords[1]))
	
	if loud: df = open('apogeeobs.txt', 'w')
	# Loop over all plates
	for p in range(len(apg)):
		# Initalize obsarr row
		if apg[p].priority <= 0: continue
		for t in range(len(times)): obsarr[p,t] = apg[p].priority
		
		# Compute observing constants
		platecoo = coo.ICRSCoordinates(apg[p].ra, apg[p].dec)
		platelst = float(apg[p].ra + apg[p].ha) / 15
		minlst = float(apg[p].ra + apg[p].minha) / 15
		maxlst = float(apg[p].ra + apg[p].maxha) / 15
		
		for t in range(len(times)):
			# Adjust LSTs for 24 hour wrapping
			usedminlst, usedmaxlst = minlst, maxlst
			if minlst < 0 and beglst[t] > 12 and endlst[t] > 12:
				usedminlst += 24
				usedmaxlst += 24
			if maxlst > 24 and beglst[t] < 12 and endlst[t] < 12:
				usedminlst -= 24
				usedmaxlst -= 24
			if beglst[t] > endlst[t]:
				if minlst < 12: usedminlst += 24
				if maxlst > 12: usedmaxlst -= 24
				
			# Adjust LSTs for Gaussian with 24 hour wrapping
			if beglst[t] > endlst[t]:
				lstsum = beglst[t]+endlst[t]-24
				if platelst > 12: usedplatelst = platelst - 24
				else: usedplatelst = platelst
			else:
				lstsum = beglst[t]+endlst[t]
				if beglst[t] > 18 and platelst < 4: usedplatelst = platelst + 24
				elif beglst[t] < 4 and platelst > 18: usedplatelst = platelst - 24
				else: usedplatelst = platelst
		
			# Gaussian prioritization on time from transit
			obsarr[p,t] += 50.0 * float(np.exp( -(usedplatelst - lstsum/2 + lengths[t]/2)**2 / 2))

			# Moon avoidance
			moondist = mpos[t] - platecoo
			if moondist.d < par['moon_threshold']:
				obsarr[p,t] = -3
				continue
		
			# Determine whether HAs of block are within observational range
			if beglst[t] < usedminlst or endlst[t] > usedmaxlst: 
				obsarr[p,t] = -1
				continue
		
			# Compute horiztonal coordinates
			horz = apo.apparentCoordinates(platecoo, datetime=[times[t] + lengths[t] / 2 / 24 * x for x in range(3)])
			secz = [1/np.cos((90.0 - horz[x].alt.d) * np.pi / 180) for x in range(len(horz))]
			# Check whether any of the points contain a bad airmass value
			badsecz = [x for x in secz if x < 1.003 or x > par['maxz']]
			if len(badsecz) > 0: obsarr[p,t] = -2

                        #Lower the priority of long exposure plates in the last slot
                        if t == len(times) -1:
                                if apg[p].exp_time == 1000.0:
                                        obsarr[p,t] = obsarr[p,t] / 5.0
                                        
			
		if loud: print(apg[p].plateid, minlst, maxlst, apo.localTime(minlst, utc=True), apo.localTime(maxlst, utc=True), obsarr[p,:], file=df)
			
	obs_end = time()
	if loud: print("[PY] Determined APOGEE-II observability (%.3f sec)" % (obs_end - obs_start))

	if loud: df.close()
	
	return obsarr
