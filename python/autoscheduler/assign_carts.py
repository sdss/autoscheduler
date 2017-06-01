from __future__ import print_function, division
from time import time
from operator import itemgetter
from sdss.internal.database.connections import APODatabaseUserLocalConnection
from sdss.internal.database.apo.platedb import ModelClasses as plateDB
from sdss.internal.database.apo.mangadb import ModelClasses as mangaDB
from Totoro.utils.utils import avoid_cart_2
import numpy as np
import os


def mangaBrightPriority(plateIDs):
    """Sorts APOGEE plates in order of increasing MaNGA data.

    Gets a list of APOGEE plateIDs and returns them in order of increasing
    MaNGA data. It uses the sum of the transparencies of all the MaNGA
    exposures associted with a plate as a proxy for amount of data.
    """

    plateIDs = np.sort(plateIDs)

    Session = APODatabaseUserLocalConnection.Session
    session = Session()

    # Retrieves the plates from the DB
    with session.begin():
        plates = session.query(plateDB.Plate).filter(
            plateDB.Plate.plate_id.in_(plateIDs)).order_by(
                plateDB.Plate.plate_id).all()

    # For each plate, gets a list with the transparency of each exposure.
    mangaTransparencies = []
    for plate in plates:
        plateTransparencies = []
        for plugging in plate.pluggings:
            scienceExposures = plugging.scienceExposures()
            for exp in scienceExposures:
                if exp.survey.label != 'MaNGA':
                    continue
                if len(exp.mangadbExposure) == 0:
                    continue
                plateTransparencies.append(exp.mangadbExposure[0].transparency)
        mangaTransparencies.append(plateTransparencies)

    # Calculates the sum of the transparencies for each plate
    sumOfTransparencies = np.array([np.sum(exps)
                                    for exps in mangaTransparencies])

    plates_to_avoid_cart_2 = np.array([avoid_cart_2(plateid)
                                       for plateid in plateIDs])
    print(plates_to_avoid_cart_2)
    tier1 = plateIDs[plates_to_avoid_cart_2][
        np.argsort(sumOfTransparencies[plates_to_avoid_cart_2])]

    tier2 = plateIDs[~plates_to_avoid_cart_2][
        np.argsort(sumOfTransparencies[~plates_to_avoid_cart_2])]

    # Returns plate ids sorted by the sum of the transparencies.
    return tier1.tolist() + tier2.tolist()


def assign_carts(apogee_choices, manga_choices, eboss_choices, errors, manga_cart_order, loud=True):
    '''
    assign_carts: Assigns all survey plate choices to cartridges.

    INPUT: apogee_choices -- dictionary list containing all APOGEE-II plate choices for tonight
           manga_choices -- dictionary list containing all MaNGA plate choices for tonight
           eboss_choices -- dictionary list containing all eBOSS plate choices for tonight
    OUTPUT: plugplan -- dictionary list containing all plugging choices for tonight
    '''

    cart_start = time()
    # Create database connection
    if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0:
        from sdss.internal.database.connections.UtahLocalConnection import db
    else:
        from sdss.internal.database.connections.APODatabaseUserLocalConnection import db
    session = db.Session()

    # Read in all available cartridges
    # allcarts = session.execute("SET SCHEMA 'platedb'; "+
    #       "SELECT crt.number FROM platedb.cartridge AS crt "+
    #       "ORDER BY crt.number").fetchall()
    allcarts = session.query(plateDB.Cartridge.number).order_by(plateDB.Cartridge.number).all()

    plugplan = []
    for c in allcarts:
        plugplan.append({'cart': c[0], 'cartsurveys': 0, 'oldplate': 0, 'm_picked': 0})
        if c[0] < 10:
            plugplan[-1]['cartsurveys'] = 1
        if c[0] >= 10:
            plugplan[-1]['cartsurveys'] = 2

    # Read in all plates that are currently plugged
    # Co-observing plates are returned twice
    # currentplug = session.execute("SET SCHEMA 'platedb'; "+
    #   "SELECT crt.number, plt.plate_id "+
    #   "FROM (((((platedb.active_plugging AS ac "+
    #       "JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
    #       "LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
    #       "LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
    #       "LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
    #       "LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
    #   "ORDER BY crt.number").fetchall()
    # coobserved plates no longer returned twice
    currentplug = session.query(plateDB.Cartridge.number, plateDB.Plate.plate_id)\
                                .join(plateDB.Plugging).join(plateDB.Plate).join(plateDB.ActivePlugging)\
                                .order_by(plateDB.Cartridge.number).all()
    for c, p in currentplug:
        wcart = [x for x in range(len(plugplan)) if plugplan[x]['cart'] == c][0]
        plugplan[wcart]['oldplate'] = p

    # Save MaNGA choices to cartridges (since they are the most dependent)
    manpicks = manga_choices

    # Reorder plugplan to priority order
    sort_plugplan = []
    # eBOSS is just in order by cart number
    cart_order = [17, 16, 15, 14, 13, 12, 11, 10]
    # APOGEE and MaNGA carts are in an order determined by Totoro
    # cart_order.extend([9, 8, 7, 6, 5, 4, 3, 2, 1])
    cart_order.extend(manga_cart_order)

    for c in cart_order:
        pidx = [x for x in range(len(plugplan)) if plugplan[x]['cart'] == c]
        if len(pidx) == 0:
            continue
        sort_plugplan.append(plugplan[pidx[0]])
    plugplan = sort_plugplan

    # Mark any cartridges already chosen by manga
    if len(manpicks) > 0:
        for c in manpicks:
            wcart = [x for x in range(len(plugplan)) if plugplan[x]['cart'] == c['cart']]
            if len(wcart) == 0:
                continue
            plugplan[wcart[0]]['m_picked'] = 1

    # Sort apogee_choices, so that non-co-observing plates are plugged first
    apogee_choices = sorted(apogee_choices, key=itemgetter('coobs'))

    # Sort the co-observing plates in order of least manga signal to most manga signal
    aponlyplt = [apogee_choices[x]['plate'] for x in range(len(apogee_choices)) if not apogee_choices[x]['coobs'] and apogee_choices[x]['plate'] != -1]
    coobsplt = [apogee_choices[x]['plate'] for x in range(len(apogee_choices)) if apogee_choices[x]['coobs']]
    # Only do this if we have coobs plates
    if len(coobsplt) > 0:
        # Sort coobs plates in order of manga signal
        coobsplt = mangaBrightPriority(coobsplt)
        # Combine both plate lists together
        allplate = aponlyplt+coobsplt
        sort_choices = []
        # Sort apogee_choices by allplate list
        for i in range(len(allplate)):
            hold = [apogee_choices[x] for x in range(len(apogee_choices)) if apogee_choices[x]['plate'] == allplate[i]]
            sort_choices = sort_choices+hold

        # Add back in the -1 plates
        for i in range(len(apogee_choices)):
            if(apogee_choices[i]['plate'] == -1):
                sort_choices.append(apogee_choices[i])

        # Save the results
        apogee_choices = sort_choices

    # Save APOGEE-II choices to cartridges
    apgsaved = np.zeros(len(apogee_choices))
    apgpicks = []
    # First loop: assign plates to carts which are already plugged
    for i in range(len(apogee_choices)):
        wplate = [x for x in range(len(plugplan)) if apogee_choices[i]['plate'] == plugplan[x]['oldplate']]
        if len(wplate) == 0:
            continue
        if plugplan[wplate[0]]['m_picked'] == 1:
            continue
        # Save new values to apgpicks

        thispick = apogee_choices[i]
        thispick['cart'] = plugplan[wplate[0]]['cart']
        thispick['plate'] = apogee_choices[i]['plate']
        plugplan[wplate[0]]['cart'] = -1
        apgsaved[i] = 1
        thispick.pop('coobs', None)
        apgpicks.append(thispick)

    manga_removed_plates = []
    # Second loop: assign plates to carts which are not plugged
    for i in range(len(apogee_choices)):
        if apgsaved[i] == 1:
            continue
        if apogee_choices[i]['coobs']:
            # Co-observing plates prefer being on carts 1 - 6
            carts_avail = [x for x in range(len(plugplan)) if plugplan[x]['cart'] >= 0 and plugplan[x]['cart'] <= 6 and plugplan[x]['m_picked'] == 0]
            if len(carts_avail) == 0:
                carts_avail = [x for x in range(len(plugplan)) if plugplan[x]['cart'] >= 0 and plugplan[x]['cartsurveys'] == 1]
        else:
            carts_avail = [x for x in range(len(plugplan)) if plugplan[x]['cart'] >= 0 and plugplan[x]['cartsurveys'] == 1]
        if len(carts_avail) == 0:
            continue

        # Remove cart from MaNGA list
        if plugplan[carts_avail[0]]['m_picked'] == 1:
            wcart = [x for x in range(len(manpicks)) if plugplan[carts_avail[0]]['cart'] == manpicks[x]['cart']]
            manga_removed_plates.append(manpicks[wcart[0]]['plateid'])
            manpicks.pop(wcart[0])

        # Save new values to apgpicks
        thispick = apogee_choices[i]
        thispick.pop('coobs', None)
        plate_id = thispick['plate']

        if plate_id == -1 or not avoid_cart_2(plate_id):
            # If the plate holes are separated enough for cart 2.
            selected_cart = carts_avail[0]
        else:
            # If the plate cannot be plugged in cart 2 loops until it gets
            # a different cart or gets to the last cart available.
            for cart in carts_avail:
                if cart != 2 or cart == carts_avail[-1]:
                    selected_cart = cart

        thispick['cart'] = plugplan[selected_cart]['cart']
        plugplan[selected_cart]['cart'] = -1
        apgpicks.append(thispick)

        # Report removed MaNGA plates
    if len(manga_removed_plates) > 0:
        errors.append('Removed {} MaNGA Plates'.format(len(manga_removed_plates)))

        # Save eBOSS choices to cartridges
    ebosaved = np.zeros(len(eboss_choices))
    ebopicks = []
    # First loop: assign plates to carts which are already plugged
    for i in range(len(eboss_choices)):
        wplate = [x for x in range(len(plugplan)) if eboss_choices[i]['plate'] == plugplan[x]['oldplate']]
        if len(wplate) == 0:
            continue
        # Save new values to ebopicks
        thispick = eboss_choices[i]
        thispick['cart'] = plugplan[wplate[0]]['cart']
        plugplan[wplate[0]]['cart'] = -1
        ebosaved[i] = 1
        ebopicks.append(thispick)
    # Second loop: assign plates to carts which are not plugged
    for i in range(len(eboss_choices)):
        if ebosaved[i] == 1:
            continue
        carts_avail = [x for x in range(len(plugplan)) if plugplan[x]['cart'] >= 0 and plugplan[x]['cartsurveys'] == 2]
        if len(carts_avail) == 0:
            continue
        # Save new values to ebopicks
        thispick = eboss_choices[i]
        thispick['cart'] = plugplan[carts_avail[0]]['cart']
        plugplan[carts_avail[0]]['cart'] = -1
        ebopicks.append(thispick)

    cart_end = time()
    if loud:
        print("[PY] Assigned cartridges (%.3f sec)" % (cart_end - cart_start))

    return apgpicks, manpicks, ebopicks
