from __future__ import print_function, division
from time import time
import numpy as np
import os

def assign_carts(apogee_choices, manga_choices, eboss_choices, errors, loud=True):
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
	allcarts = session.execute("SET SCHEMA 'platedb'; "+
			"SELECT crt.number FROM platedb.cartridge AS crt "+
			"ORDER BY crt.number").fetchall()
	plugplan = []
	for c in allcarts:
		plugplan.append({'cart': c[0], 'cartsurveys': 0, 'oldplate': 0})
		if c[0] < 10: plugplan[-1]['cartsurveys'] = 1
		if c[0] >= 10: plugplan[-1]['cartsurveys'] = 2
		if c[0] == 2: plugplan[-1]['cartsurveys'] = 3
	
	# Read in all plates that are currently plugged
	currentplug = session.execute("SET SCHEMA 'platedb'; "+
		"SELECT crt.number, plt.plate_id "+
		"FROM (((((platedb.active_plugging AS ac "+
			"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
			"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
			"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
		"ORDER BY crt.number").fetchall()
	for c,p in currentplug:
		wcart = [x for x in range(len(plugplan)) if plugplan[x]['cart'] == c][0]
		plugplan[wcart]['oldplate'] = p
		
	# Reorder plugplan to priority order
	sort_plugplan, cart_order = [], [17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
	for c in cart_order:
		pidx = [x for x in range(len(plugplan)) if plugplan[x]['cart'] == c]
		if len(pidx) == 0: continue
		sort_plugplan.append(plugplan[pidx[0]])
	plugplan = sort_plugplan
		
	# Save MaNGA choices to cartridges (since they are the most dependent)
	# TO-DO
	manpicks = manga_choices

	# Find currently-plugged MaNGA plates, and adjust the cart order
	from sdss.internal.manga.Totoro.dbclasses.plate import Plates
	pluggedPlates = Plates.getPlugged()
	man_cartnum, man_pctcomplete = [], []
	for plate in pluggedPlates:
		man_cartnum.append(plate.getActiveCartNumber())
		man_pctcomplete.append(plate.getPlateCompletion())
	man_pctsort = np.argsort(man_pctcomplete)
	man_cartnum, man_pctcomplete = [man_cartnum[-x-1] for x in man_pctsort], [man_pctcomplete[-x-1] for x in man_pctsort]

	print(cart_order)
	for c in range(len(man_cartnum)):
		man_entry = [x for x in range(len(cart_order)) if cart_order[x] == man_cartnum[c]]
		if len(man_entry) > 0: cart_order.pop(man_entry[0])
		cart_order.append(man_cartnum[c])
	print(cart_order)

	
	# Save APOGEE-II choices to cartridges
	apgsaved = np.zeros(len(apogee_choices))
	apgpicks = []
	# First loop: assign plates to carts which are already plugged
	for i in range(len(apogee_choices)):
		wplate = [x for x in range(len(plugplan)) if apogee_choices[i]['plate'] == plugplan[x]['oldplate']]
		if len(wplate) == 0: continue
		# Save new values to apgpicks
		thispick = apogee_choices[i]
		thispick['cart'] = plugplan[wplate[0]]['cart']
		thispick['plate'] = apogee_choices[i]['plate']
		plugplan[wplate[0]]['cart'] = -1
		apgsaved[i] = 1
		apgpicks.append(thispick)
	# Second loop: assign plates to carts which are not plugged
	for i in range(len(apogee_choices)):
		if apgsaved[i] == 1: continue
		carts_avail = [x for x in range(len(plugplan)) if plugplan[x]['cart'] >= 0 and (plugplan[x]['cartsurveys'] == 1 or plugplan[x]['cartsurveys'] == 3)]
		if len(carts_avail) == 0: continue
		# Save new values to apgpicks
		thispick = apogee_choices[i]
		thispick['cart'] = plugplan[carts_avail[0]]['cart']
		plugplan[carts_avail[0]]['cart'] = -1
		apgpicks.append(thispick)
		
	# Save eBOSS choices to cartridges
	ebosaved = np.zeros(len(eboss_choices))
	ebopicks = []
	# First loop: assign plates to carts which are already plugged
	for i in range(len(eboss_choices)):
		wplate = [x for x in range(len(plugplan)) if eboss_choices[i]['plate'] == plugplan[x]['oldplate']]
		if len(wplate) == 0: continue
		# Save new values to ebopicks
		thispick = eboss_choices[i]
		thispick['cart'] = plugplan[wplate[0]]['cart']
		plugplan[wplate[0]]['cart'] = -1
		ebosaved[i] = 1
		ebopicks.append(thispick)
	# Second loop: assign plates to carts which are not plugged
	for i in range(len(eboss_choices)):
		if ebosaved[i] == 1: continue
		carts_avail = [x for x in range(len(plugplan)) if plugplan[x]['cart'] >= 0 and plugplan[x]['cartsurveys'] == 2]
		if len(carts_avail) == 0: continue
		# Save new values to ebopicks
		thispick = eboss_choices[i]
		thispick['cart'] = plugplan[carts_avail[0]]['cart']
		plugplan[carts_avail[0]]['cart'] = -1
		ebopicks.append(thispick)
	
	cart_end = time()
	if loud:
		print("[PY] Assigned cartridges (%.3f sec)" % (cart_end - cart_start))
	
	return apgpicks, manpicks, ebopicks
		
