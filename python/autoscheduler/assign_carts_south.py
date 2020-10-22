from __future__ import print_function, division
from time import time
from copy import deepcopy
from operator import itemgetter
import numpy as np
import os
import autoscheduler.apogee as apg


def assign_carts(schedule, errors, loud=True):
    '''
    assign_carts: Assigns all survey plate choices to cartridges.

    INPUT: night schedule (NOTE: this behavior is different from the north)
    OUTPUT: plugplan -- dictionary list containing all plugging choices for tonight
    '''

    cart_start = time()
    # Create database connection
    from autoscheduler.plateDBtools.database.connections.LCODatabaseUserLocalConnection import db
    session = db.Session()
    from autoscheduler.plateDBtools.database.apo.platedb import ModelClasses as plateDB

    # Read in all available cartridges
    # allcarts = session.execute("SET SCHEMA 'platedb'; "+
    #       "SELECT crt.number FROM platedb.cartridge AS crt "+
    #       "ORDER BY crt.number").fetchall()
    allcarts = session.query(plateDB.Cartridge.number).order_by(plateDB.Cartridge.number).all()

    plugplan = list()

    for c in allcarts:
        plugplan.append({'cart': c[0], 'oldplate': 0})

    # Read in all plates that are currently plugged

    # currentplug = session.execute("SET SCHEMA 'platedb'; "+
    #   "SELECT crt.number, plt.plate_id "+
    #   "FROM (((((platedb.active_plugging AS ac "+
    #       "JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
    #       "LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
    #       "LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
    #       "LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
    #       "LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
    #   "ORDER BY crt.number").fetchall()

    currentplug = session.query(plateDB.Cartridge.number, plateDB.Plate.plate_id)\
                                .join(plateDB.Plugging).join(plateDB.Plate).join(plateDB.ActivePlugging)\
                                .order_by(plateDB.Cartridge.number).all()

    # add current plug plate. leave logic alone; it works
    for c, p in currentplug:
        wcart = [x for x in range(len(plugplan)) if plugplan[x]['cart'] == c][0]
        plugplan[wcart]['oldplate'] = p

    # had to get rid of hardcoded carts
    par = {'exposure': 67, 'overhead': 20, 'maxz': 3, 'moon_threshold': 15, 'sn_target': 3136}
    nightLength = (schedule['bright_end'] - schedule['bright_start']) * 24
    nslots = int(round(nightLength / ((par['exposure'] + par['overhead']) / 60)))
    par['ncarts'] = nslots
    apogee_choices = apg.schedule_apogee(schedule=schedule, errors=errors, par=par, plan=True, loud=loud, south=True)

    # Save APOGEE-II choices to cartridges
    apgpicks = list()
    # order apogee plates by obs time
    ordered_choices = sorted(apogee_choices, key=itemgetter('obsmjd'))
    # print('there are {} apogee choices tonight.'.format(len(ordered_choices)))
    if len(ordered_choices) == 0:
        print('[PY] No APOGEE plates chosen')
        return list()

    # First loop: assign plates to carts which are already plugged
    # if they are in the first N plates of the night (N=num of carts)
    for i, choice in enumerate(ordered_choices):
        if i < len(allcarts):
            for cart in plugplan:
                if cart['oldplate'] == choice['plate']:
                    choice_index = ordered_choices.index(choice)
                    thispick = ordered_choices.pop(choice_index)
                    thispick['cart'] = cart['cart']
                    apgpicks.append(thispick)
                    cart['cart'] = -1

    # second loop, assign plates to remaining carts in order of observing
    remaining_carts = [x for x in plugplan if x['cart'] != -1]
    if len(remaining_carts) > 0:
        for cart in remaining_carts:
            thispick = ordered_choices.pop(0)  # remove the next plate up to be observed and plug it
            while thispick["plate"] == -1:
                thispick['cart'] = -1
                apgpicks.append(thispick)
                try:
                    thispick = ordered_choices.pop(0)
                except IndexError:
                    # I can see this happening...
                    thispick = None
                    break
            
            if thispick is not None:
                # clumsy? but probably safe
                thispick['cart'] = cart['cart']
                apgpicks.append(thispick)
                cart['cart'] = -1

    # assign dummy carts, -1 showing that they aren't actually plugged
    for choice in ordered_choices:
        thispick = choice
        thispick['cart'] = -1
        apgpicks.append(thispick)

    cart_end = time()
    if loud:
        print("[PY] Assigned cartridges (%.3f sec)" % (cart_end - cart_start))

    return apgpicks
