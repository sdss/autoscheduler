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
def schedule_eboss(schedule, plan=False, loud=True):
    # Define eBOSS observing parameters
    par = {'exposure': 16.5, 'ncarts': 8, 'maxz': 2.0, 'moon_threshold': 30, 'snr_avg': 9.0, 'snb_avg': 4.0, 'snr': 25, 'snb': 10}
    
    # Divide eBOSS time into blocks
    times = np.arange(schedule['eboss_start'], schedule['eboss_end'], par['exposure']/60/24)

    # Get all plate information from the database
    ebo = get_plates(plan=plan, loud=loud)
    
    # If we are not planning, just return the plates read in along with cart numbers
    if not plan:
        eboss_choices = []
        for p in range(len(ebo)):
            eboss_choices.append({'plate': ebo[p].plateid})
        return eboss_choices
    
    # Determine observability
    obs = observability(ebo, par, times, loud=loud)
    
    # Pick plates for tonight
    eboss_choices = pick_plates(ebo, par, times, obs, loud=loud)

    return eboss_choices


        
        
    
