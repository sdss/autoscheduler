from __future__ import print_function, division
from time import time

from autoscheduler.plateDBtools.apogee.get_apogee_plates import get_plates
from set_apogee_priorities import set_priorities
from observability import observability
from pick_apogee_plates import pick_plates

# SCHEDULE_APOGEE
# DESCRIPTION: Main APOGEE-II scheduling routine.
# INPUT: schedule -- dictionary defining important schedule times throughout the night
# OUTPUT: apogee_choices -- dictionary list containing plate choices + observing times for tonight


def schedule_apogee(schedule, errors, par=None, plan=False, loud=True, twilight=False, south=False):

    # Default params for north, south can have different params so keep them if passed in
    if par is None:
        par = {'exposure': 67, 'overhead': 20, 'ncarts': 9, 'maxz': 3, 'moon_threshold': 15, 'sn_target': 3136}

    # Define APOGEE-II blocks for tonight
    nightlength = (schedule['bright_end'] - schedule['bright_start']) * 24
    nslots = min([int(round(nightlength / ((par['exposure'] + par['overhead']) / 60))), par['ncarts']])
    if nslots != 0:
        times = [schedule['bright_start'] + (par['exposure'] + par['overhead']) / 60 / 24 * x for x in range(nslots)]
        lengths = [(par['exposure'] + par['overhead']) / 60 for x in range(nslots)]
        if south:
            # no overhead on last exposure
            lengths[-1] = par['exposure'] / 60
        else:
            # If APOGEE-II starts the split night
            if schedule['bright_start'] < schedule['dark_start'] or schedule['dark_start'] == 0:
                # Determine whether we should add another exposure (leftover time > 15min)
                if len(times) < par['ncarts'] and nightlength - sum(lengths) > 0:
                        times.append(schedule['bright_start'] + len(times) * (par['exposure'] + par['overhead']) / 60 / 24)
                        lengths.append(nightlength - sum(lengths))
                # Because APOGEE-II is first, the last exposure will not have overhead
                else:
                    lengths[-1] = par['exposure'] / 60

            # APOGEE-II ends the night
            else:
                # Determine whether we can add an exposure (leftover time > 15min)
                if len(times) < par['ncarts'] and nightlength - sum(lengths) > par['overhead'] / 60:
                        times.append(schedule['bright_start'] + len(times) * (par['exposure'] + par['overhead']) / 60 / 24)
                        lengths.append(nightlength - sum(lengths))

    else:
            times = []
            lengths = []
    # define twilight parameters
    if twilight:
        # Define APOGEE-II blocks for tonight
        # if schedule['manga_end'] > schedule['eboss_end']:
        #   twtimes= [schedule['manga_end']+(par['exposure'] + par['overhead']) / 60 / 24]
        # else:
        #   twtimes= [schedule['eboss_end']+(par['exposure'] + par['overhead']) / 60 / 24]
        # twlengths = [(par['exposure'] + par['overhead']) / 60]

                # 28 minutes from 15 deg twilight to 8 deg twilight

                # We don't want to schedule plates during summer shutdown or any night that doesn't have a dark survey
        if (schedule['dark_end'] != 0.0):
            twtime = schedule['dark_end'] + par['overhead']/60/24
            twlength = (28+par['overhead'])/60

            times.append(twtime)
            lengths.append(twlength)
            nslots = nslots + 1

    # Return nothing if no APOGEE slots needed.
    if nslots == 0:
        return []

    # Get all plate information from the database
    if south:
        passed_mjd = schedule['jd'] - 2400000
    else:
        passed_mjd = None
    apg = get_plates(errors, plan=plan, loud=loud, south=south, mjd=passed_mjd)
    if len(apg) == 0:
        errors.append('APOGEE-II PLATE ERROR: No APOGEE-II plates found. Aborting.')
        return []

    # decision to include ALL plates, but de-prioritize other programs, moved to set_priorities
    # if 'programs' in schedule:
    #     apg = [p for p in apg if p.cadence in schedule['programs']]
    
    # Prioritize all plates
    set_priorities(apg, par, schedule, plan, loud=loud, twilight=twilight, south=south)

    # Determine observability range of all plates
    obs = observability(apg, par, times, lengths, loud=loud, south=south)

    # Pick plates for tonight
    picks = pick_plates(apg, obs, par, times, lengths, schedule, loud=loud, south=south)

    # Print out all plate information (just for testing purposes)
    if loud:
        df = open('apogee.txt', 'w')
        for p in range(len(apg)):
            print("%20s %5d %3d %3d %5.2f %5.2f  %5.1f %8.2f %8.2f  %s" % (apg[p].name, apg[p].plateid, apg[p].vplan, apg[p].vdone, apg[p].minha, apg[p].maxha, apg[p].sn, apg[p].priority, max(obs[p, :]), apg[p].hist), file=df)
        df.close()

    return picks


def schedule_external(schedule, errors, par=None, plan=False, loud=True, twilight=False, ):

    # Default params for north, south can have different params so keep them if passed in
    if par is None:
        par = {'exposure': 60, 'overhead': 20, 'ncarts': 9, 'maxz': 3, 'moon_threshold': 15, 'sn_target': 3136}

    # Define APOGEE-II blocks for tonight
    nightlength = (schedule['bright_end'] - schedule['bright_start']) * 24
    nslots = min([int(round(nightlength / ((par['exposure'] + par['overhead']) / 60))), par['ncarts']])
    if nslots != 0:
        times = [schedule['bright_start'] + (par['exposure'] + par['overhead']) / 60 / 24 * x for x in range(nslots)]
        lengths = [(par['exposure'] + par['overhead']) / 60 for x in range(nslots)]
        # no overhead on last exposure
        lengths[-1] = par['exposure'] / 60
    else:
            times = []
            lengths = []

    # Return nothing if no APOGEE slots needed.
    if nslots == 0:
        return []

    # Get all plate information from the database
    passed_mjd = schedule['jd'] - 2400000
    # ##########################
    # change
    # ##########################
    apg = get_plates(errors, plan=plan, loud=loud, south=south, mjd=passed_mjd)
    if len(apg) == 0:
        errors.append('APOGEE-II PLATE ERROR: No APOGEE-II plates found. Aborting.')
        return []

    # Prioritize all plates
    # ##########################
    # change
    # ##########################
    set_priorities(apg, par, schedule, plan, loud=loud, twilight=twilight, south=south)

    # Determine observability range of all plates
    obs = observability(apg, par, times, lengths, loud=loud, south=south)

    # Pick plates for tonight
    picks = pick_plates(apg, obs, par, times, lengths, schedule, loud=loud, south=south)

    # Print out all plate information (just for testing purposes)
    if loud:
        df = open('apogee.txt', 'w')
        for p in range(len(apg)):
            print("%20s %5d %3d %3d %5.2f %5.2f  %5.1f %8.2f %8.2f  %s" % (apg[p].name, apg[p].plateid, apg[p].vplan, apg[p].vdone, apg[p].minha, apg[p].maxha, apg[p].sn, apg[p].priority, max(obs[p, :]), apg[p].hist), file=df)
        df.close()

    return picks
