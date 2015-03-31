from __future__ import print_function, division
from time import time
import os
from sdss.apogee.plate_completion import completion

# APGPLATE OBJECT DENITION
# DESCRIPTION: APOGEE Plate Object
class apgplate(object):
	# Identifying plate information
	name = ''
	locationid = 0
	plateid = 0
	apgver = 0
	platepk = -1
	
	# Plate pointing information
	ra = 0.0
	dec = 0.0
	ha = 0.0
	maxha = 0.0
	minha = 0.0
	
	# Scheduling info
	vplan = 0
	vdone = 0
	manual_priority = 0
	priority = 0.0
	plugged = 0
	snql, snred, sn = 0.0, 0.0, 0.0
	hist = ''
	reduction = ''
	cadence = ''
	plate_loc = ''
	stack = 0
	lead_survey = 'apg'
	coobs = False
		
	# Determine most recent observation time
	def maxhist(self):
		obsstr = self.hist.split(',')
		if len(obsstr) == 0 or obsstr[0] == '': return float(0.0)
		obshist = [float(x) for x in obsstr if x != '']
		return max(obshist)
		
	# Determine first observation time
	def minhist(self):
		obsstr = self.hist.split(',')
		if len(obsstr) == 0 or obsstr[0] == '': return float(0.0)
		obshist = [float(x) for x in obsstr if x != '']
		return min(obshist)
		
	# Determine plate completion percentage (from algorithm in the SDSS python module)
	def pct(self):
		return completion(self.vplan, self.vdone, self.sn, self.cadence)

# GET_PLATES
# DESCRIPTION: Reads in APOGEE-II plate information from platedb
# INPUT: none
# OUTPUT: apg -- list of objects with all APOGEE-II plate information
def get_plates(errors, plan=False, loud=True, session=None, atapo=True):
	if session is None:
		# Create database connection
		if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0: 
			from sdss.internal.database.connections.UtahLocalConnection import db
		else: 
			from sdss.internal.database.connections.APOSDSSIIIUserLocalConnection import db
		session = db.Session()
	
	# Pull all relevant plate information for APOGEE plates
	stage1_start = time()
	if plan:
		qstr = "SET SCHEMA 'platedb'; "
		qstr += "SELECT plt.location_id, ptg.center_ra, ptg.center_dec, plt.plate_id, pltg.hour_angle, pltg.priority, plt.design_pk, plt.name, pltg.ha_observable_max, pltg.ha_observable_min, plt.pk, plt.current_survey_mode_pk, ploc.label "
		qstr += "FROM (((((((platedb.plate AS plt "
		qstr += "INNER JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk = plt.pk)) "
		qstr += "INNER JOIN platedb.survey AS surv ON (p2s.survey_pk = surv.pk)) "
		qstr += "INNER JOIN platedb.plate_pointing AS pltg ON (pltg.plate_pk=plt.pk)) "
		qstr += "INNER JOIN platedb.pointing AS ptg ON (pltg.pointing_pk=ptg.pk)) "
		qstr += "INNER JOIN platedb.plate_location AS ploc ON (ploc.pk=plt.plate_location_pk)) "
		qstr += "INNER JOIN platedb.plate_to_plate_status AS p2ps ON (p2ps.plate_pk=plt.pk)) "
		qstr += "INNER JOIN platedb.plate_status AS plts ON (plts.pk=p2ps.plate_status_pk)) "
		qstr += "WHERE surv.label='APOGEE-2' AND plts.label = 'Accepted'"
		if atapo: qstr += "AND ploc.label = 'APO' "
		qstr += "ORDER BY plt.plate_id"
		stage1 = session.execute(qstr).fetchall()

		stage1man = session.execute("SET SCHEMA 'platedb'; "+
			"SELECT plt.location_id, ptg.center_ra, ptg.center_dec, plt.plate_id, pltg.hour_angle, pltg.priority, plt.design_pk, plt.name, pltg.ha_observable_max, pltg.ha_observable_min, plt.pk, plt.current_survey_mode_pk "+
			"FROM (((((((platedb.plate AS plt "+
				"INNER JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk = plt.pk)) "+
				"INNER JOIN platedb.survey AS surv ON (p2s.survey_pk = surv.pk)) "+
				"INNER JOIN platedb.plate_pointing AS pltg ON (pltg.plate_pk=plt.pk)) "+
				"INNER JOIN platedb.pointing AS ptg ON (pltg.pointing_pk=ptg.pk)) "+
				"INNER JOIN platedb.plate_location AS ploc ON (ploc.pk=plt.plate_location_pk)) "+
				"INNER JOIN platedb.plate_to_plate_status AS p2ps ON (p2ps.plate_pk=plt.pk)) "+
				"INNER JOIN platedb.plate_status AS plts ON (plts.pk=p2ps.plate_status_pk)) "+
			"WHERE surv.label='MaNGA' AND plts.label = 'Accepted' AND ploc.label = 'APO' "+
			"ORDER BY plt.plate_id").fetchall()
	else:
		stage1 = session.execute("SET SCHEMA 'platedb'; "+
			"SELECT plt.location_id, ptg.center_ra, ptg.center_dec, plt.plate_id, pltg.hour_angle, pltg.priority, plt.design_pk, plt.name, pltg.ha_observable_max, pltg.ha_observable_min, plt.pk, plt.current_survey_mode_pk, ploc.label "+
			"FROM ((((((((platedb.active_plugging AS ac "+
				"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
				"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
				"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
				"LEFT JOIN platedb.plate_location AS ploc ON (ploc.pk=plt.plate_location_pk)) "
				"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
				"LEFT JOIN platedb.survey AS surv ON (p2s.survey_pk = surv.pk)) "+
				"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
				"LEFT JOIN platedb.pointing AS ptg ON (pltg.pointing_pk=ptg.pk)) "+
			"WHERE surv.label='APOGEE-2' ORDER BY crt.number").fetchall()
		stage1man = None
	
	# Setup APOGEE-II data structure
	apg = []
	
	# Save data to structure
	missing = []
	for i in range(len(stage1)):
		try:
			# Check to see whether this is a MaNGA-led plate
			if stage1[i][11] is not None: 
				if stage1[i][11] == 2 or stage1[i][11] == 3: continue
			apg.append(apgplate())
			apg[-1].locationid = stage1[i][0]
			apg[-1].ra = float(stage1[i][1])
			apg[-1].dec = float(stage1[i][2])
			apg[-1].plateid = stage1[i][3]
			apg[-1].ha = float(stage1[i][4])
			apg[-1].manual_priority = stage1[i][5]
			designid = int(stage1[i][6])
			apg[-1].name = stage1[i][7]
			apg[-1].maxha = float(stage1[i][8]) + 7.5
			apg[-1].minha = float(stage1[i][9]) - 7.5
			apg[-1].platepk = stage1[i][10]
			apg[-1].plugged = 0
			if stage1[i][11] is not None:
				if stage1[i][11] == 2 or stage1[i][11] == 3: apg[-1].lead_survey = 'man'
			apg[-1].plate_loc = stage1[i][12]
		except Exception as e:
			print(e)
			missing.append("%d (%s)" % (stage1[i][3], e))
			#continue
		
		# Get APOGEE version number and vplan for this plate
		dvdata = session.execute("SELECT array_to_string(array_agg(dv.value),',') FROM platedb.design_value as dv WHERE (dv.design_field_pk=342 OR dv.design_field_pk=343 OR dv.design_field_pk=344 OR dv.design_field_pk=351 OR dv.design_field_pk=423 OR dv.design_field_pk=424) AND dv.design_pk=%d" % (designid)).fetchall()
		if dvdata[0][0]:
			tmp = dvdata[0][0].split(',')
			apg[-1].apgver = 100*int(tmp[0]) + 10*int(tmp[1]) + int(tmp[2])
			if len(tmp) > 3: apg[-1].vplan = int(tmp[3])
			if len(tmp) > 4: apg[-1].cadence = tmp[4]
		else:
			apg[-1].vplan = 3
			apg[-1].apgver = 999
	stage1_end = time()
	if loud: print("[SQL] Read in APOGEE-II plates (%.3f sec)" % ((stage1_end - stage1_start)))

	# Determine co-observed plates
	if stage1man:
		for m in stage1man:
			# Find this MaNGA plate in the APOGEE-II list
			match_idx = [x for x in range(len(apg)) if apg[x].plateid == m[3]]
			if len(match_idx) > 0:
				apg[match_idx[0]].coobs = True
	
	# Let everyone know there are bad database entries, if necessary
	if len(missing) > 0:
		errors.append("APOGEE-II DB ERROR: missing information in DB on plates: %s" % (', '.join([str(x) for x in missing])))
	
	# Read in previous APOGEE observations
	stage2_start = time()
	stage2 = []
	try:
		stage2 = session.execute("SET SCHEMA 'platedb'; "+
			"SELECT plt.plate_id, CAST (exp.start_time/86400 AS int), sum(qr.snr_standard^2.0), count(qr.snr_standard), sum(apr.snr^2.0), count(apr.snr) "+
			"FROM (((((((platedb.exposure AS exp "+
				"INNER JOIN platedb.survey as surv ON (exp.survey_pk = surv.pk))"+
				"LEFT JOIN apogeeqldb.quickred AS qr ON (exp.pk=qr.exposure_pk)) "+
				"LEFT JOIN apogeeqldb.reduction AS apr ON (exp.pk=apr.exposure_pk)) "+
				"LEFT JOIN platedb.exposure_flavor AS expf ON (expf.pk=exp.exposure_flavor_pk)) "+
				"LEFT JOIN platedb.observation AS obs ON (exp.observation_pk=obs.pk)) "+
				"LEFT JOIN platedb.plate_pointing AS pltg ON (obs.plate_pointing_pk=pltg.pk)) "+
				"RIGHT JOIN platedb.plate AS plt ON (pltg.plate_pk=plt.pk)) "+
			"WHERE expf.label='Object' AND (qr.snr_standard >= 10.0 OR apr.snr >= 10.0) "+
			"GROUP BY plt.plate_id, CAST (exp.start_time/86400 AS int) ORDER BY plt.plate_id").fetchall()
	except: pass
	stage2_end = time()
	if loud: print("[SQL] Read in past APOGEE observations (%.3f sec)" % ((stage2_end - stage2_start)))
	
	# Parse previous APOGEE observations
	for i in range(len(stage2)):
		if stage2[i][0] == 0: continue
		# Find this plate in the data structure
		wplate = [x for x in range(len(apg)) if stage2[i][0] == apg[x].plateid]
		if len(wplate) == 0: continue
		wver = [x for x in range(len(apg)) if apg[wplate[0]].locationid == apg[x].locationid and apg[wplate[0]].apgver == apg[x].apgver]
		
		# Determine which S/N to use, QL or reduction
		if stage2[i][4] != None:
			sn = float(stage2[i][4])
			sncnt = float(stage2[i][5])
			for v in range(len(wver)): apg[wver[v]].snred += float(stage2[i][4])
		elif stage2[i][2] != None:
			sn = float(stage2[i][2])
			sncnt = float(stage2[i][3])
		else:
			sn, sncnt = 0, 0
		if stage2[i][2] != None:
			for v in range(len(wver)): apg[wver[v]].snql += float(stage2[i][2])
			
		# Determine whether we can add this MJD to observation history
		if sncnt >= 2:
			for v in range(len(wver)): 
				apg[wver[v]].hist += "%7d," % (stage2[i][1] + 2400000)
				if stage2[i][4] != None: apg[wver[v]].reduction += '1,'
				else: apg[wver[v]].reduction += '0,'
				apg[wver[v]].vdone += 1
		# Add all good S/N to this plate
		for v in range(len(wver)): apg[wver[v]].sn += sn
		
	# Determine what is currently plugged
	stage3_start = time()
	stage3 = session.execute("SET SCHEMA 'platedb'; "+
		"SELECT crt.number, plt.plate_id "+
		"FROM ((((((platedb.active_plugging AS ac "+
			"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
			"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
			"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
			"LEFT JOIN platedb.survey as surv ON (p2s.survey_pk = surv.pk)) "+
			"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
		"WHERE surv.label = 'APOGEE-2' ORDER BY crt.number").fetchall()
	stage3_end = time()
	if loud: print("[SQL] Read in currently plugged APOGEE plates (%.3f sec)" % ((stage3_end - stage3_start)))
	
	# Save currently plugged plates to data
	for c,p in stage3:
		wplate = [x for x in range(len(apg)) if apg[x].plateid == p]
		if len(wplate) == 0: continue
		apg[wplate[0]].plugged = c
		
	return apg