from __future__ import print_function, division
from time import time
import astropysics.coords as coo
import astropysics.obstools as obs

# SCHEDULE_EBOSS
# DESCRIPTION: Main eBOSS scheduling routine.
# INPUT: schedule -- dictionary defining important schedule times throughout the night
# OUTPUT: eboss_choices -- dictionary list containing plate choices + observing times for tonight 
def schedule_eboss(schedule, plan=False):

	# Get all plate information from the database
	ebo = get_eboss_plates(plan=plan)
	
	return ebo


# GET_EBOSS_PLATES
# DESCRIPTION: Reads in eBOSS plate information from platedb
# INPUT: none
# OUTPUT: ebo -- list of dicts with all eBOSS plate information
def get_eboss_plates(plan=False):
	# Create database connection
	if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0: from sdss.internal.database.connections.UtahLocalConnection import db
	else: from sdss.internal.database.connections.APODatabaseUserLocalConnection import db
	session = db.Session()
	apo = obs.Site(32.789278, -105.820278)
	
	ebo = []
	
	# Determine what is currently plugged
	sql_start = time()
	eboplug = session.execute("SET SCHEMA 'platedb'; "+
		"SELECT crt.number, plt.pk, plt.ra, plt.dec "+
		"FROM (((((platedb.active_plugging AS ac "+
			"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
			"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
			"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
		"WHERE p2s.survey_pk = 2 ORDER BY crt.number").fetchall()
	sql_end = time()
	print("[SQL] Read in currently plugged eBOSS plates (%d sec)" % ((sql_end - sql_start)))
	
	for i in eboplug:
		plate = coo.ICRSCoordinates(i[2], i[3])
		transitmjd = obs.calendar_to_jd(apo.nextRiseSetTransit(field)[2])
		ebo.append({'platepk': i[1], 'transittime': transitmjd})
		
	return ebo
		
		
	