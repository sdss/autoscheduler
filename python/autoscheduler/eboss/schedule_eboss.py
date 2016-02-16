from __future__ import print_function, division
from time import time
import numpy as np

from get_eboss_plates import get_plates
from observability import observability
from pick_eboss_plates import pick_plates

# SCHEDULE_EBOSS
# DESCRIPTION: Main eBOSS scheduling routine.
# INPUT: schedule -- dictionary defining important schedule times throughout the night
# OUTPUT: eboss_choices -- dictionary list containing plate choices + observing times for tonight 
def schedule_eboss(schedule, errors, plan=False, loud=True):
    # Define eBOSS observing parameters
    par = {'exposure': 16.5, 'ncarts': 8, 'maxz': 2.0, 'moon_threshold': 30, 'snr_avg':4.9, 'snb_avg': 2.2, 'snr': 22, 'snb': 10}
    
    # Divide eBOSS time into blocks
    times = np.arange(schedule['eboss_start'], schedule['eboss_end'], par['exposure']/60/24)
    # Somehow this procedure gets run even when there is no eBOSS time
    if len(times) == 0: return []

    # Get all plate information from the database
    ebo = get_plates(plan=plan, loud=loud)
    if len(ebo) == 0:
        errors.append('eBOSS PLATE ERROR: No eBOSS plates found. Aborting.')
        return []
    
    # If we are not planning, just return the plates read in along with cart numbers
    if not plan:
        eboss_choices = []
        for p in range(len(ebo)):
            eboss_choices.append({'plate': ebo[p].plateid})
        return eboss_choices
    
    # Determine observability
    obs = observability(ebo, par, times, loud=loud)
    
    if loud:
        of = open("eboss.txt", 'w')
        for p in range(len(ebo)):
            obsstr = ''
            for i in obs[p,:]: obsstr += "%3d " % (i)
            print("%5d %9.5f %9.5f %3d %6.2f %6.2f    %s " % (ebo[p].plateid, ebo[p].ra, ebo[p].dec, ebo[p].manual_priority, (ebo[p].ra+ebo[p].minha)/15, (ebo[p].ra+ebo[p].maxha)/15, obsstr), file=of)
        of.close()
    
    # Pick plates for tonight
    eboss_choices = pick_plates(ebo, par, times, obs, loud=loud)

    return eboss_choices


        
        
    
