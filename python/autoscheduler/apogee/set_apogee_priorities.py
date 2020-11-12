from __future__ import print_function, division
from time import time
import numpy as np

# SET_PRIORITIES
# DESCRIPTION: Sets priority values for all available APOGEE-II plates
# INPUT: apg -- list of objects with all APOGEE-II plate information
# OUTPUT: none


def set_priorities(apg, par, schedule, plan=False, loud=True, twilight=False, south=False):
    set_pri_start = time()
    # Loop through all plates and set priorities
    for p in range(len(apg)):
        # Manual override
        if apg[p].manual_priority == 10:
            apg[p].priority = 9999.0
            continue
        elif apg[p].manual_priority == 1:
            apg[p].priority = -1.0
            continue

        # Set base priority
        apg[p].priority = 100.0 * apg[p].manual_priority

        # Already Plugged
        if not south:
            if apg[p].plugged > 0:
                apg[p].priority += 100.0

        # Declination
        if south:
            apg[p].priority -= 50.0 * float(np.exp(-(apg[p].dec + 29)**2 / (2 * (20)**2)))
        else:
            apg[p].priority -= 50.0 * float(np.exp(-(apg[p].dec - 33)**2 / (2 * (20)**2)))
        # Ecliptic
        # TO-DO

        # Completion (using algorithm in SDSS python module)
        if plan:
            if apg[p].pct() >= 1:
                apg[p].priority = -2

        # Cadence
        if schedule['jd'] != apg[p].maxhist():
            if schedule['jd'] - apg[p].maxhist() < 3:
                apg[p].priority = -1

        #  # Cadence
        # if schedule['jd'] != apg[p].maxhist():
        #     # 3-visit cadence rules: 3 days between adjacent obs, 26 between first and last
        #     if apg[p].vplan == 3:
        #         if schedule['jd'] - apg[p].maxhist() < 3:
        #             apg[p].priority = -1
        #         if apg[p].vdone == 2 and schedule['jd'] - apg[p].minhist() < 26:
        #             apg[p].priority = -1
        #     # 4+ visit cadence rules: 3 days between adjacent obs
        #     elif apg[p].vplan > 3:
        #         if schedule['jd'] - apg[p].maxhist() < 3:
        #             apg[p].priority = -1
        #     # Alternative cadence rules
        #     # Do a once a bright run cadence for KOI and substellar plates
        #     if apg[p].cadence == 'kep_koi' or apg[p].cadence == 'substellar' or apg[p].cadence == 'koi_btx':
        #             if schedule['jd'] - apg[p].maxhist() < 4:
        #                 apg[p].priority = -1

    # In-Order Completion (needs second loop)
    for p in range(len(apg)):
        wfield = [x for x in range(len(apg)) if apg[x].locationid == apg[p].locationid]
        for f in wfield:
            if apg[p].apgver > apg[f].apgver and apg[f].priority > 1:
                apg[p].priority /= 2

    # For south, de-prioritize plates for programs not scheduled tonight
    if 'programs' in schedule:
        for p in apg:
            if p.cadence not in schedule['programs']:
                p.priority /= 10
    set_pri_end = time()

    if loud:
        print("[PY] Prioritized APOGEE-II plates (%.3f sec)" % (set_pri_end - set_pri_start))
