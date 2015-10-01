from __future__ import print_function, division
from time import time
import numpy as np
import astropysics.coords as coo
import astropysics.obstools as obs
from sdss.utilities.idlasl import moonpos

def observability(ebo, par, times, loud=True):
    obs_start = time()
    apo = obs.Site(32.789278, -105.820278)
    obsarr = np.zeros([len(ebo), len(times)])
    beglst = [apo.localSiderialTime(x) for x in times]
    endlst = [apo.localSiderialTime(times[x] + par['exposure']/60/24) for x in range(len(times))]
    
    # Determine moon coordinates
    mpos = []
    for t in range(len(times)):
        mooncoords = moonpos(times[t])
        mpos.append(coo.ICRSCoordinates(mooncoords[0], mooncoords[1]))
    
    # Loop over all plates
    for p in range(len(ebo)):
        # Initalize obsarr row
        for t in range(len(times)): obsarr[p,t] = ebo[p].manual_priority * 100
        
        # Compute observing constants
        platecoo = coo.ICRSCoordinates(ebo[p].ra, ebo[p].dec)
        platelst = float(ebo[p].ra + ebo[p].ha) / 15
        try: 
            minlst = float(ebo[p].ra + ebo[p].minha) / 15
        except:
            print("Plate Missing minha info: {}".format(ebo[p].plateid))
            continue

        maxlst = float(ebo[p].ra + ebo[p].maxha) / 15
        
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
            obsarr[p,t] += 50.0 * float(np.exp( -(usedplatelst - lstsum/2 + par['exposure']/60/2)**2 / 2))
        
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
            horz = apo.apparentCoordinates(platecoo, datetime=times[t] + par['exposure'] / 60 / 2 / 24)
            secz = 1/np.cos((90.0 - horz[0].alt.d) * np.pi / 180)
            # Check whether any of the points contain a bad airmass value
            if secz < 1.003 or secz > par['maxz']: obsarr[p,t] = -2
    obs_end = time()
    if loud: print("[PY] Determined eBOSS observability (%.3f sec)" % (obs_end - obs_start))
    return obsarr
