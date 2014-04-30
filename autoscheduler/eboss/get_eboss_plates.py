from __future__ import print_function, division
from time import time
import os

# EBOPLATE OBJECT DENITION
# DESCRIPTION: eBOSS Plate Object
class eboplate(object):
	# Identifying plate information
	plateid = 0
	platepk = -1
	
	# Plate pointing information
	ra = 0.0
	dec = 0.0
	ha = 0.0
	maxha = 0.0
	minha = 0.0
	
	# Scheduling info
	snr = 0.0
	snb = 0.0
	manual_priority = 0.0
	priority = 0.0
	plugged = 0

# GET_PLATES
# DESCRIPTION: Reads in eBOSS plate information from platedb
# INPUT: none
# OUTPUT: ebo -- list of dicts with all eBOSS plate information
def get_plates(plan=False):
	# Create database connection
	if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0: from sdss.internal.database.connections.UtahLocalConnection import db
	else: from sdss.internal.database.connections.APODatabaseUserLocalConnection import db
	session = db.Session()
	
	# Pull all relevant plate information for eBOSS plates
	stage1_start = time()
	if plan:
		stage1 = session.execute("SET SCHEMA 'platedb'; "+
			"SELECT ptg.center_ra, ptg.center_dec, plt.plate_id, pltg.hour_angle, pltg.priority, pltg.ha_observable_max, pltg.ha_observable_min, plt.pk "+
			"FROM ((((((platedb.plate AS plt "+
				"INNER JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk = plt.pk)) "+
				"INNER JOIN platedb.plate_pointing AS pltg ON (pltg.plate_pk=plt.pk)) "+
				"INNER JOIN platedb.pointing AS ptg ON (pltg.pointing_pk=ptg.pk)) "+
				"INNER JOIN platedb.plate_location AS ploc ON (ploc.pk=plt.plate_location_pk)) "+
				"INNER JOIN platedb.plate_to_plate_status AS p2ps ON (p2ps.plate_pk=plt.pk))"+
				"INNER JOIN platedb.plate_status AS plts ON (plts.pk=p2ps.plate_status_pk))"+
			"WHERE p2s.survey_pk=2 AND plt.plate_id >= 4800 AND plts.label = 'Accepted' AND ploc.label = 'APO' "+
			"ORDER BY plt.plate_id").fetchall()
	else:
		stage1 = session.execute("SET SCHEMA 'platedb'; "+
			"SELECT ptg.center_ra, ptg.center_dec, plt.plate_id, pltg.hour_angle, pltg.priority, pltg.ha_observable_max, pltg.ha_observable_min, plt.pk "+
			"FROM ((((((platedb.active_plugging AS ac "+
				"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
				"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
				"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
				"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
				"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
				"LEFT JOIN platedb.pointing AS ptg ON (pltg.pointing_pk=ptg.pk)) "+
			"WHERE p2s.survey_pk=2 ORDER BY crt.number").fetchall()	
	# Setup eBOSS data structure
	ebo = []
	for i in range(len(stage1)):
		ebo.append(eboplate())
		ebo[i].ra = stage1[i][0]
		ebo[i].dec = stage1[i][1]
		ebo[i].plateid = stage1[i][2]
		ebo[i].ha = stage1[i][3]
		ebo[i].manual_priority = stage1[i][4]
		ebo[i].maxha = stage1[i][5]
		ebo[i].minha = stage1[i][6]
		ebo[i].platepk = stage1[i][7]
		ebo[i].plugged = 0
	stage1_end = time()
	print("[SQL] Read in eBOSS plates (%d sec)" % ((stage1_end - stage1_start)))
	
	# Read in previous eBOSS observations
	# TO-DO
	
	# Determine what is currently plugged
	stage3_start = time()
	stage3 = session.execute("SET SCHEMA 'platedb'; "+
		"SELECT crt.number, plt.plate_id "+
		"FROM (((((platedb.active_plugging AS ac "+
			"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
			"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
			"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
		"WHERE p2s.survey_pk=2 ORDER BY crt.number").fetchall()
	# Save currently plugged plates to data
	for c,p in stage3:
		wplate = [x for x in range(len(ebo)) if ebo[x].plateid == p][0]
		ebo[wplate].plugged = c
	stage3_end = time()
	print("[SQL] Read in currently plugged eBOSS plates (%.3f sec)" % ((stage3_end - stage3_start)))
		
	return ebo
	