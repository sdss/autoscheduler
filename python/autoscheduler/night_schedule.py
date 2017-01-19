from __future__ import print_function, division
import datetime
import numpy as np


def get_juldate():
    dt = datetime.datetime.utcnow()
    L = int((dt.month-14.0)/12.0)
    julian = dt.day - 32075 + int(1461*(dt.year+4800l+L)/4.0) + int(367*(dt.month - 2-L*12)/12.0) - int(int(3*((dt.year+4900l+L)/100.0))/4.0)
    julian += ((dt.hour/24.0) + (dt.minute/(24.0*60.0)) + (dt.second/86400.) + (dt.microsecond/(86400.*1e6)) - 0.5)
    return julian


def read_schedule(pwd, errors, mjd=-1, surveys=['apogee', 'eboss', 'manga'], loud=True, plan=False, south=False):
    '''
    read_schedule: reads in scheduler formatted nightly schedule

    INPUT: filename -- name of the base schedule file supplied by survey coordinator
    OUTPUT: schedule -- list of dicts that contain the relevant survey times for each night.
    '''
    # Read in SDSS-III schedule
    schdir = '/'.join(pwd.split('/')[0:-2]) + "/schedules/"
    schf = open(schdir+'Sch_base.6yrs.txt.frm.dat', 'r')
    schlines = schf.read().splitlines()
    schf.close()
    # Assign values to schedule dict list
    schedule = []
    for i in range(len(schlines)):
        tmp = schlines[i].split()
        # Assign already-computed values to dict
        schedule.append({'jd': float(tmp[0]), 'eboss': int(tmp[1]), 'manga': int(tmp[2]), 'bright_start': float(tmp[4]),
                         'bright_end': float(tmp[5]), 'dark_start': float(tmp[6]), 'dark_end': float(tmp[7]),
                         'eboss_start': float(tmp[8]), 'eboss_end': float(tmp[9]), 'manga_start': float(tmp[10]), 'manga_end': float(tmp[11])})
    # Read in SDSS-IV schedule
    schf = open(schdir+'Sch_base.6yrs.txt.frm.dat', 'r')
    schlines = schf.read().splitlines()
    schf.close()
    # Assign values to schedule dict list
    for i in range(len(schlines)):
        tmp = schlines[i].split()
        # Assign already-computed values to dict
        schedule.append({'jd': float(tmp[0]), 'eboss': int(tmp[1]), 'manga': int(tmp[2]), 'bright_start': float(tmp[4]),
                         'bright_end': float(tmp[5]), 'dark_start': float(tmp[6]), 'dark_end': float(tmp[7]),
                         'eboss_start': float(tmp[8]), 'eboss_end': float(tmp[9]), 'manga_start': float(tmp[10]), 'manga_end': float(tmp[11])})

    # Determine what line in the schedule to use for tonight
    if mjd < 0:
        jd_now = get_juldate()
        utc_hr = (((jd_now - int(jd_now))+0.5)*24+19) % 24
        # For plugging, we want the next day after 9PM
        if plan:
            if utc_hr > 21 or utc_hr <= 7:
                tonight = int(jd_now)+1
            else:
                tonight = int(jd_now)
        # For observing, we want the current date until 9AM
        else:
            tonight = int(jd_now-0.1)
    else:
        tonight = 2400000 + int(mjd)
    if loud:
        print("[PY] Scheduling MJD %5d" % (tonight - 2400000))

    # Find line to use in the schedule file
    currjd = [x for x in range(len(schedule)) if schedule[x]['jd'] == tonight]
    # If this line doesn't exist, find the closest day
    if not len(currjd) > 0:
        currjd = np.argsort([np.abs(schedule[x]['jd']-tonight) for x in range(len(schedule))])
        errors.append('MJD ERROR: JD %d not present in schedule file. Using JD = %d instead.' % (tonight, schedule[currjd[0]]['jd']))

    # See if schedule needs to be adjusted based on what surveys are being run tonight
    # Is eBOSS offline, but MaNGA isn't? MaNGA gets all of dark time.
    if 'manga' in surveys and not 'eboss' in surveys:
        schedule[currjd[0]]['manga_start'] = schedule[currjd[0]]['dark_start']
        schedule[currjd[0]]['manga_end'] = schedule[currjd[0]]['dark_end']
        schedule[currjd[0]]['eboss_start'] = 0
        schedule[currjd[0]]['eboss_end'] = 0
        schedule[currjd[0]]['eboss'] = 0
    # Is MaNGA offline, but eBOSS isn't? eBOSS gets all of dark time.
    if 'eboss' in surveys and not 'manga' in surveys:
        schedule[currjd[0]]['eboss_start'] = schedule[currjd[0]]['dark_start']
        schedule[currjd[0]]['eboss_end'] = schedule[currjd[0]]['dark_end']
        schedule[currjd[0]]['manga_start'] = 0
        schedule[currjd[0]]['manga_end'] = 0
        schedule[currjd[0]]['manga'] = 0
    # Are both dark-time surveys offline? APOGEE-II gets everything.
    if not 'eboss' in surveys and not 'manga' in surveys:
        schedule[currjd[0]]['bright_start'] = min([x for x in [schedule[currjd[0]]['bright_start'], schedule[currjd[0]]['dark_start']] if x > 0])
        schedule[currjd[0]]['bright_end'] = max([x for x in [schedule[currjd[0]]['bright_end'], schedule[currjd[0]]['dark_end']] if x > 0])
        schedule[currjd[0]]['eboss_start'] = 0
        schedule[currjd[0]]['eboss_end'] = 0
        schedule[currjd[0]]['eboss'] = 0
        schedule[currjd[0]]['manga_start'] = 0
        schedule[currjd[0]]['manga_end'] = 0
        schedule[currjd[0]]['manga'] = 0
    # APOGEE-II is offline. What happens?
    # TO-DO

    return schedule[currjd[0]]
