from __future__ import print_function, division
from time import time
import numpy as np


def pick_plates(ebo, par, times, obs, loud=True):
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
        if startslot+nleft < len(chosen):
            if chosen[startslot+nleft] >= 0: startslot += -1
        
        # Mark slots as chosen
        for i in range(nleft):
            if startslot+i >= len(chosen): continue
            chosen[startslot+i] = ebo[p].plateid
        # Remove plate from further picking
        for t in range(len(times)): obs[p,t] = -10
    pickplug_end = time()
    if loud: print("[PY] Placed eBOSS already-plugged plates (%.3f sec)" % (pickplug_end - pickplug_start))
            
    # Loop through all un-scheduled blocks and place plates
    ebossrest_start = time()
    t = 0
    while t < len(chosen):
        if chosen[t] >= 0 or len(np.unique(chosen)) > par['ncarts']:
            t += 1
            continue
        # Choose the highest-priority plate for this slot
        priorder = np.argsort(obs[:,t])
        p = priorder[-1]
        if obs[p,t] < 0:
            if loud: print("[WARN] No eBOSS plates for slot %2d. Max priority = %4.1f" % (t, max(obs[:,t])))
            t += 1
            continue
        nleft = ebo[p].visleft(par)
        # Check to see whether plate can be observed for the entire necessary block
        endblock = min([t+nleft, len(chosen)-1])
        if obs[p,endblock] < 0:
            # If it cannot be placed in this block, then remove it from the running and try again
            obs[p,t] = -10
            continue
        # Place plate in expected number of slots
        for i in range(nleft):
            if t+i >= len(chosen): continue
            chosen[t+i] = ebo[p].plateid
        for i in range(len(times)): obs[p,i] = -10
    ebossrest_end = time()
    if loud: print("[PY] Placed new eBOSS plates (%.3f sec)" % (pickplug_end - pickplug_start))

    print(chosen)
    
    # Return all chosen plates
    chosenplates = np.unique(chosen)
    eboss_choices = []
    for p in chosenplates:
        if p < 0: continue
        eboss_choices.append({'plate': p})
    return eboss_choices
