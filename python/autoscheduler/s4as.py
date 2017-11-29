# ---- SDSS-IV AUTOSCHEDULER ----
# DESCRIPTION: Wrapping layer to all 3 surveys' scheduling modules
# __author__ = 'Ben Thompson <b.a.thompson1@tcu.edu>'

# Import necessary modules
from __future__ import print_function, division
from autoscheduler import night_schedule
import autoscheduler.apogee as apg
from time import time
from astropy import time as atime
import os


def run_scheduler(plan=False, mjd=-1, surveys=['apogee', 'eboss', 'manga'], loud=True):
    as_start_time = time()
    errors = []

    if surveys == ['south'] or surveys == ['override']:
        south = True
        plan = True
        from autoscheduler import assign_carts_south
    else:
        south = False
        from autoscheduler import assign_carts
        import autoscheduler.eboss as ebo
        import autoscheduler.manga as man

    # Read in schedule file
    pwd = os.path.dirname(os.path.realpath(__file__))
    schedule_start_time = time()
    schedule = night_schedule.read_schedule(pwd, errors, mjd=mjd, surveys=surveys, loud=loud, plan=plan, south=south)
    schedule_end_time = time()
    if loud:
        print("[PY] Schedule read in complete (%.3f sec)" % (schedule_end_time - schedule_start_time))

    # if we're scheduling the south, its quick and easy, so ignore the rest of the logic
    if south:
        plan = dict()
        plan['schedule'] = dict()
        plan['schedule']['mjd'] = schedule['jd'] - 2400000
        # April '17: request for default behavior to return an APOGEE schedule, thus block below isn't needed
        # if schedule['survey'] == 0 or schedule['survey'] == 2:  # not observing or engineering
        #     plan['schedule']['apg_start'] = 0.0
        #     plan['schedule']['apg_end'] = 0.0
        #     plan['errors'] = errors
        #     as_end_time = time()
        #     if loud:
        #         print("[PY] run_scheduler complete in (%.3f sec)" % ((as_end_time - as_start_time)))
        #     return plan
        # uncomment between to return to previous default
        apgcart = assign_carts_south.assign_carts(schedule, errors, loud=loud)
        # next 2 lines are artifacts of old code; may be unnecessary
        plan['schedule']['apg_start'] = schedule['bright_start'] - 2400000
        plan['schedule']['apg_end'] = schedule['bright_end'] - 2400000
        # Return cart assignments for chosen plates
        plan['apogee'] = apgcart
        plan['errors'] = errors
        as_end_time = time()
        if loud:
            print("[PY] run_scheduler complete in (%.3f sec)" % ((as_end_time - as_start_time)))
        return plan

    # otherwise, schedule surveys for tonight
    apogee_choices, manga_choices, eboss_choices = [], [], []
    # Schedule APOGEE-II

    # check date range
    check_date = atime.Time(schedule['jd'], format='jd')
    check_year = int(check_date.byear)  # get year of time in question, casting int floors in python 2.7
    check_start = atime.Time('%d-3-16' % (check_year), format='iso')
    check_end = atime.Time('%d-9-15' % (check_year), format='iso')
    twilight_check = (check_start < check_date and check_end > check_date)

    # if apogee observes tonight and in twilight time
    if schedule['bright_start'] > 0 and twilight_check:
                if schedule['manga_end'] > schedule['bright_end'] or schedule['eboss_end'] > schedule['bright_end']:
                        apogee_choices = apg.schedule_apogee(schedule, errors, plan=plan, loud=loud, twilight=True)
                else:
                        apogee_choices = apg.schedule_apogee(schedule, errors, plan=plan, loud=loud, twilight=False)

    # if apogee doesn't observe but its twilight time
    elif twilight_check:
                apogee_choices = apg.schedule_apogee(schedule, errors, plan=plan, loud=loud, twilight=True)

    # if apogee observes and not twilight time
    elif schedule['bright_start'] > 0:
            apogee_choices = apg.schedule_apogee(schedule, errors, plan=plan, loud=loud, twilight=False)

    # Schedule MaNGA
    (manga_choices, manga_cart_order) = man.schedule_manga(schedule, errors, plan=plan, loud=loud)
    # Schedule eBOSS
    if schedule['eboss'] > 0:
        eboss_choices = ebo.schedule_eboss(schedule, errors, plan=plan, loud=loud)

    # Take results and assign to carts
    apgcart, mancart, ebocart = assign_carts.assign_carts(apogee_choices, manga_choices, eboss_choices, errors, manga_cart_order, loud=loud)

    as_end_time = time()
    if loud:
        print("[PY] run_scheduler complete in (%.3f sec)" % ((as_end_time - as_start_time)))

    plan = dict()
    # Reformat schedule dict for output
    plan['schedule'] = dict()
    plan['schedule']['mjd'] = schedule['jd'] - 2400000
    if schedule['bright_start'] > 0:
        plan['schedule']['apg_start'] = schedule['bright_start'] - 2400000
        plan['schedule']['apg_end'] = schedule['bright_end'] - 2400000
    if schedule['manga_start'] > 0:
        plan['schedule']['man_start'] = schedule['manga_start'] - 2400000
        plan['schedule']['man_end'] = schedule['manga_end'] - 2400000
    if schedule['eboss_start'] > 0:
        plan['schedule']['ebo_start'] = schedule['eboss_start'] - 2400000
        plan['schedule']['ebo_end'] = schedule['eboss_end'] - 2400000
    # Return cart assignments for chosen plates
    plan['apogee'] = apgcart
    plan['manga'] = mancart
    plan['eboss'] = ebocart
    plan['errors'] = errors
    return plan
