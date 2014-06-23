from __future__ import print_function, division
from time import time
import numpy as np
import astropysics.coords as coo
import astropysics.obstools as obs
from ..moonpos import moonpos

def observability(ebo, par, times, loud=True):
    obs_start = time()
    apo = obs.Site(32.789278, -105.820278)
    obsarr = np.zeros([len(ebo), len(times)])
    beglst = [apo.localSiderialTime(x) for x in times]
    endlst = [apo.localSiderialTime(times[x] + par['exposure']/24) for x in range(len(times))]
    
    # Determine moon coordinates
    mpos = []
    for t in range(len(times)):
        moonra, moondec = moonpos(times[t])
        mpos.append(coo.ICRSCoordinates(moonra, moondec))
    
    # Loop over all plates
    for p in range(len(ebo)):
        # Initalize obsarr row
        for t in range(len(times)): obsarr[p,t] = ebo[p].manual_priority * 100
        
        # Compute observing constants
        platecoo = coo.ICRSCoordinates(ebo[p].ra, ebo[p].dec)
        platelst = float(ebo[p].ra + ebo[p].ha) / 15
        minlst = float(ebo[p].ra + ebo[p].minha) / 15
        maxlst = float(ebo[p].ra + ebo[p].maxha) / 15
        
        for t in range(len(times)): 
            # Gaussian prioritization on time from transit
            obsarr[p,t] += 50.0 * float(np.exp( -(platelst - (beglst[t]+endlst[t])/2 + par['exposure']/2)**2 / 2))
        
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
            horz = apo.apparentCoordinates(platecoo, datetime=times[t] + par['exposure'] / 2 / 24)
            secz = 1/np.cos((90.0 - horz[0].alt.d) * np.pi / 180)
            # Check whether any of the points contain a bad airmass value
            if secz < 1.003 or secz > par['maxz']: obsarr[p,t] = -2
    obs_end = time()
    if loud: print("[PY] Determined eBOSS observability (%.3f sec)" % (obs_end - obs_start))
    return obsarr
