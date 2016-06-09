from __future__ import print_function, division
from time import time
import os
import sqlalchemy
import numpy as np
from sdss.apogee.plate_completion import completion

# DESCRIPTION: APOGEE Plate Object
class apgplate(object):
	# Identifying plate information
	def __init__(self,plate=None):
		if plate is None: 
			raise Exception("Somehow tried to make plate object without a plate")
		#properties we get from plate object
		self.plate = plate
		self.name = plate.name
		self.locationid = plate.location_id
		self.plateid = plate.plate_id
		self.platepk = plate.pk
		self.ddict= plate.design.designDictionary
		#plate_loc is physical location, and may never be used
		self.plate_loc = plate.location.label
		
		#NOTE FROM JOHN: ddict contains RA, DEC, and survey info
		#if this runs slowly, use ddict to set these
		self._ra = None
		self._dec = None
		self._ha = None
		self._maxha = None
		self._minha = None
		self._manual_priority = None
		self._plugged = None

		self._exp_time = None
		self._lead_survey = None
		self._coobs = None

		#catch values not set properly
		if 'apogee_design_type' in self.ddict:
			self.cadence = self.ddict['apogee_design_type']
			self.driver = self.ddict['apogee_design_driver']
			self.vplan = int(self.ddict['apogee_n_design_visits'])
			self.apgver = 100*int(self.ddict['apogee_short_version']) + 10*int(self.ddict['apogee_med_version']) + int(self.ddict['apogee_long_version'])
		else:
			self.cadence = 'default'
			self.driver = 'default'
			self.vplan = 3
			self.apgver = 999

		#properties requiring plate_completion method
		self.vdone = 0
		self.sn = 0.0
		self.hist = ''

		#ben sets these but doesn't use them outside of get_plates; not needed?
		self.snql = 0.0
		self.snred = 0.0
		self.reduction = ''

		#properties not set in get_plates
		self.priority = 0.0
		self.stack = 0


#----------------------------
#properties
#----------------------------
	@property 
	def ra(self):
		if self._ra is None:
			self._ra = float(self.plate.firstPointing.center_ra)
		return self._ra

	@property 
	def dec(self):
		if self._dec is None:
			self._dec = float(self.plate.firstPointing.center_dec)
		return self._dec

	@property 
	def ha(self):
		if self._ha is None:
			self._ha = float(self.plate.firstPointing.platePointing(self.plate.plate_id).hour_angle)
		return self._ha

	@property 
	def maxha(self):
		if self._maxha is None:
			self._maxha = float(self.plate.firstPointing.platePointing(self.plate.plate_id).ha_observable_max) + 7.5
		return self._maxha

	@property 
	def minha(self):
		if self._minha is None:
			self._minha = float(self.plate.firstPointing.platePointing(self.plate.plate_id).ha_observable_min) - 7.5
		return self._minha

	@property 
	def manual_priority(self):
		if self._manual_priority is None:
			self._manual_priority = int(self.plate.firstPointing.platePointing(self.plate.plate_id).priority)
		return self._manual_priority

	@property 
	def plugged(self):
		if self._plugged is None:
			self._plugged = 0
			for p in self.plate.pluggings:
				if len(p.activePlugging) >0:
					self._plugged = p.cartridge.number
		return self._plugged

	@property 
	def lead_survey(self):
		if self._lead_survey is None:
			if self.plate.currentSurveyMode is None:
				self._lead_survey = 'apg'
			elif self.plate.currentSurveyMode.label == 'APOGEE lead': 
				self._lead_survey = 'apg'
			else: 
				self._lead_survey = 'man'
		return self._lead_survey	

	@property 
	def exp_time(self):
		if self._exp_time is None:
			if "apogee_exposure_time" in self.ddict: 
				self._exp_time = float(self.ddict['apogee_exposure_time'])
			elif self.lead_survey == 'apg': 
				self._exp_time = 500.0
			else: self._exp_time = 450.0
		return self._exp_time

	@property 
	def coobs(self):
		if self._coobs is None:
			if 'MANGA' in self.ddict['instruments']:
				self._coobs = True
			else: self._coobs = False
		return self._coobs

#----------------------------
#useful methods
#----------------------------
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


def get_plates(errors, plan=False, loud=True, session=None, atapo=True, allPlates=False, plateList = []):
	'''DESCRIPTION: Reads in APOGEE-II plate information from platedb
	INPUT: None
	OUTPUT: apg -- list of objects with all APOGEE-II plate information'''
	start_time = time()

	if session is None:
		# Create database connection
		if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0: 
			from sdss.internal.database.connections.UtahLocalConnection import db
		else: 
			from sdss.internal.database.connections.APODatabaseUserLocalConnection import db
	        session = db.Session()
	from sdss.internal.database.apo.platedb import ModelClasses as pdb
	from sdss.internal.database.apo.apogeeqldb import ModelClasses as qldb

	try:
		acceptedStatus=session.query(pdb.PlateStatus).filter(pdb.PlateStatus.label=="Accepted").one()
	except sqlalchemy.orm.exc.NoResultFound:
		raise Exception("Could not find 'Accepted' status in plate_status table")

	try:
		survey=session.query(pdb.Survey).filter(pdb.Survey.label=="APOGEE-2").one()
	except sqlalchemy.orm.exc.NoResultFound:
		raise Exception("Could not find 'APOGEE-2' survey in survey table")

	try:
		plateLoc=session.query(pdb.PlateLocation).filter(pdb.PlateLocation.label=="APO").one()
	except sqlalchemy.orm.exc.NoResultFound:
		raise Exception("Could not find 'APO' location in plate_location table")

	# Pull all relevant plate information for APOGEE plates
	protoList = list()
	with session.begin():
		if plateList != []:
			#getting plates with same loc id as requested plates to determine hist & completion
			locIDS=session.query(pdb.Plate.location_id)\
			   .filter(pdb.Survey.pk == survey.pk)\
			   .filter(pdb.Plate.plate_id.in_(plateList)).all()

			plates=session.query(pdb.Plate)\
			   .join(pdb.PlateToSurvey, pdb.Survey)\
			   .filter(pdb.Survey.pk == survey.pk)\
			   .filter(pdb.Plate.location_id.in_(locIDS)).all()

		elif plan:
			protoList=session.query(pdb.Plate.plate_id)\
				   .join(pdb.PlateToSurvey, pdb.Survey)\
				   .join(pdb.PlateLocation)\
				   .join(pdb.PlateToPlateStatus,pdb.PlateStatus)\
				   .filter(pdb.Survey.pk == survey.pk)\
				   .filter(pdb.Plate.location==plateLoc)\
				   .filter(pdb.PlateStatus.pk ==acceptedStatus.pk).all()
			locIDS=session.query(pdb.Plate.location_id)\
				    .filter(pdb.Survey.pk == survey.pk)\
					.filter(pdb.Plate.plate_id.in_(protoList)).all()

			plates=session.query(pdb.Plate)\
			   .join(pdb.PlateToSurvey, pdb.Survey)\
			   .filter(pdb.Survey.pk == survey.pk)\
			   .filter(pdb.Plate.location_id.in_(locIDS)).all()

		elif allPlates:
			plates=session.query(pdb.Plate)\
			   .join(pdb.PlateToSurvey, pdb.Survey)\
			   .filter(pdb.Survey.pk == survey.pk).all()
		else:
			protoList=session.query(pdb.Plate.plate_id)\
				   .join(pdb.PlateToSurvey, pdb.Survey)\
				   .join(pdb.Plugging,pdb.Cartridge)\
				   .join(pdb.ActivePlugging)\
				   .filter(pdb.Survey.pk == survey.pk)\
				   .order_by(pdb.Cartridge.number).all()
			#getting plates with same loc id as PLUGGED plates to determine hist & completion
			locIDS=session.query(pdb.Plate.location_id)\
			   .filter(pdb.Survey.pk == survey.pk)\
			   .filter(pdb.Plate.plate_id.in_(protoList)).all()

			plates=session.query(pdb.Plate)\
			   .join(pdb.PlateToSurvey, pdb.Survey)\
			   .filter(pdb.Survey.pk == survey.pk)\
			   .filter(pdb.Plate.location_id.in_(locIDS)).all()

	q1Time = time()
	if loud: print('[SQL]: plate query completed in {} s'.format(q1Time-start_time))

	#create the list of apg plate objects
	apg = list()
	tmpPlateList=list()
	for plate in plates:
		tmpPlate=apgplate(plate)
		if allPlates or plateList != []: apg.append(tmpPlate)	
		else:
			if tmpPlate.lead_survey == 'apg':
				tmpPlateList.append(tmpPlate.plateid)
				apg.append(tmpPlate)

	if protoList != []:
		plateList = set([p[0] for p in protoList]).intersection(tmpPlateList)

	assignmentTime = time()
	if loud: print('[PYTHON]: plate object created in {} s'.format(assignmentTime-q1Time))

	exposedPlates = [p.plateid for p in apg]
	with session.begin():
		#returns list of tuples (mjd,plateid,qrRed,fullRed)
		exposures=session.query(sqlalchemy.func.floor(pdb.Exposure.start_time/86400+.3),pdb.Plate.plate_id,\
			qldb.Quickred.snr_standard,qldb.Reduction.snr)\
		.join(pdb.Survey).join(pdb.ExposureFlavor)\
		.join(pdb.Observation).join(pdb.PlatePointing).join(pdb.Plate)\
		.outerjoin(qldb.Quickred).outerjoin(qldb.Reduction)\
		.filter(pdb.ExposureFlavor.label == 'Object')\
		.filter(pdb.Plate.plate_id.in_(exposedPlates)).all()
		#removed survey label filter to deal with mislabled exposures
		# .filter(pdb.Survey.label == 'APOGEE-2' )
	q2Time = time()
	
	if loud: print('[SQL]: exposures query completed in {} s'.format(q2Time-assignmentTime))	

	exposures_tab = np.array(exposures)
	fullRedCheck = np.copy([exposures_tab[:,0],exposures_tab[:,1],exposures_tab[:,2],exposures_tab[:,3],[x[3] if x[3] is not None else x[2] for x in exposures_tab]]).swapaxes(0,1)

	#convert nones in SNR to zeros
	fullRedCheck = np.array(fullRedCheck,dtype=np.float)
	proto_good_exp = np.nan_to_num(fullRedCheck)
	good_exp=proto_good_exp[proto_good_exp[:,4]>10]

	plateidDict = dict()

	for i,p in enumerate(apg): 
		plateidDict[p.plateid] = i

	for p in apg:
		if p.hist != '' and p.vdone != 0: continue
		repeat = []
		#find plates that share location and cohort
		for pl in apg:
			if p.plateid == pl.plateid: continue
			if p.locationid == pl.locationid:
				if p.apgver == pl.apgver: repeat.append(pl.plateid)
		if repeat != []:
			repeat.append(p.plateid)		
			plateExps = good_exp[np.in1d(good_exp[:,1], repeat)]
			dates = np.unique(plateExps[:,0])
			for d in dates:
				day = plateExps[plateExps[:,0] == d]
				if day.shape[0] >= 2: 
					for r in repeat:
						apg[plateidDict[r]].hist += '{},'.format(int(d)+2400000)
						apg[plateidDict[r]].vdone += 1
						apg[plateidDict[r]].sn += float(np.sum(day[:,4]**2))
						apg[plateidDict[r]].snql += float(np.sum(day[:,2]**2))
						apg[plateidDict[r]].snred += float(np.sum(day[:,3]**2))
						if np.sum(day[:,4]) == np.sum(day[:,3]): apg[plateidDict[r]].reduction += '1,'
						# else: print("fuck you")
						else: apg[plateidDict[r]].reduction += '0,'
		else:
			plateExps = good_exp[good_exp[:,1] == p.plateid]
			dates = np.unique(plateExps[:,0])
			for d in dates:
				day = plateExps[plateExps[:,0] == d]
				if day.shape[0] >= 2: 
					p.hist += '{},'.format(int(d)+2400000)
					p.vdone += 1
					p.sn += float(np.sum(day[:,4]**2))
					p.snql += float(np.sum(day[:,2]**2))
					p.snred += float(np.sum(day[:,3]**2))
					if np.sum(day[:,4]) == np.sum(day[:,3]): p.reduction += '1,'
					else: p.reduction += '0,'

	end_time = time()
	if loud: print('[PYTHON]: get_plates complete in {} s'.format(end_time-start_time))

	if plateList != []:
		return [apg[plateidDict[p]] for p in plateList]

	return apg
