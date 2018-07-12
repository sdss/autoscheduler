#!/usr/bin/python

# -------------------------------------------------------------------
# Import statements
# -------------------------------------------------------------------
import sys, math, os
from decimal import *
from astropy.time import Time
from autoscheduler.sdssUtilities import dateObs2HA as ha
#from sdss.manga import DustMap
import cPickle as pickle

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relationship, exc, column_property, backref
from sqlalchemy import orm
from sqlalchemy.orm.session import Session
from sqlalchemy import String # column types, only used for custom type definition
from sqlalchemy import func # for aggregate, other functions

from autoscheduler.plateDBtools.database.DatabaseConnection import DatabaseConnection
import autoscheduler.plateDBtools.database.apo.platedb.ModelClasses as platedb

db = DatabaseConnection()

metadata_pickle_filename = "ModelClasses_apo_mangadb.pickle"

# ------------------------------------------
# Load the cached metadata if it's available
# ------------------------------------------
# NOTE: delete this cache if the database schema changes!!
# TODO: determine this programmatically (may not be possible)
use_cache = "MODEL_CLASSES_CACHE" in os.environ and os.environ["MODEL_CLASSES_CACHE"] == 'YES'
if use_cache:
	cache_path = os.path.join(os.path.expanduser("~"), ".sqlalchemy_cache")
	cached_metadata = None
	if os.path.exists(cache_path):
		try:
			cached_metadata = pickle.load(open(os.path.join(cache_path, metadata_pickle_filename)))
		except IOError:
			# cache file not found
			pass
else: cached_metadata = False
# ------------------------------------------

# ========================
# Define database classes
# ========================
Base = db.Base

class Exposure(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.exposure']
	else:
		__tablename__ = 'exposure'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<Exposure (pk={0})>'.format(self.pk)

	def taiToAirmass(self):
		'''Convert airmass from Tai, for midpoint of observation'''

		# compute tai midpoint
		taibeg = self.platedbExposure.start_time
		exptime = self.platedbExposure.exposure_time
		taiend = taibeg + exptime
		taimid = (taibeg + taiend) / Decimal(2.0)

		# APO location
		longitude = 360. - 105.820417
		latitude = 32.780361
		altitude = 2788.

		# convert to radians
		jd = 2400000.5 + float(taimid) / (24.*3600.) #julian day
		lat = math.radians(latitude)
		dec = math.radians(self.platedbExposure.observation.plate_pointing.pointing.center_dec)
		ra = self.platedbExposure.observation.plate_pointing.pointing.center_ra

		# get hour angle
		t = Time(jd, scale='tai', format='jd')
		hourang = ha.dateObs2HA(t.iso.replace(' ','T'), float(ra)) # in hours
		hourang = math.radians(hourang) # to radians

		# compute airmass
		cosz = math.sin(dec)*math.sin(lat) + math.cos(dec)*math.cos(hourang)*math.cos(lat)
		airmass = 1.0 / cosz

		return airmass

	def normalizeSN2(self, camera):
		''' Normalize SN2 '''

		if camera[0] == 'b':
			bosssn2 = 3.6
			scale = 1.0
		elif camera[0] == 'r':
			bosssn2 = 7.5
			scale = 1.25

		# simulated SN2 for a given camera, for a given exposure (via airmass)
		airmass = self.taiToAirmass()
		simSN2 = bosssn2 / math.pow(airmass, scale)

		if camera == 'b1': normSN2 = [sn2.b1_sn2 / simSN2 for sn2 in self.sn2values]
		if camera == 'b2': normSN2 = [sn2.b2_sn2 / simSN2 for sn2 in self.sn2values]
		if camera == 'r1': normSN2 = [sn2.r1_sn2 / simSN2 for sn2 in self.sn2values]
		if camera == 'r2': normSN2 = [sn2.r2_sn2 / simSN2 for sn2 in self.sn2values]

		return normSN2

class ExposureStatus(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.exposure_status']
	else:
		__tablename__ = 'exposure_status'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<Exposure_Status (pk={0}, label={1})>'.format(self.pk, self.label)

class ExposureToData_cube(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.exposure_to_data_cube']
	else:
		__tablename__ = 'exposure_to_data_cube'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<Exposure_to_Data_Cube (pk={0})'.format(self.pk)

class Set(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.set']
	else:
		__tablename__ = 'set'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<Set (pk={0}, name={1})>'.format(self.pk, self.name)

class SetStatus(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.set_status']
	else:
		__tablename__ = 'set_status'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<Set_Status (pk={0}, label={1})>'.format(self.pk, self.label)

class DataCube(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.data_cube']
	else:
		__tablename__ = 'data_cube'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<MangaDB Data_Cube (pk={0})>'.format(self.pk)

class Spectrum(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.spectrum']
	else:
		__tablename__ = 'spectrum'
		__table_args__ = {'autoload' : True, 'schema' : 'mangadb'}

	def __repr__(self):
		return '<Spectrum (pk={0})>'.format(self.pk)

class SN2Values(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.sn2_values']
	else:
		__tablename__ = 'sn2_values'
		__table_args__ = {'autoload': True, 'schema': 'mangadb'}

	def __repr__(self):
		return '<SN2_Values (pk={0})>'.format(self.pk)

	def normalize(self, camera, kappa=1.0):
		''' Normalize the SN2 values to the simulated blue/red SN2 '''

		# Get ra, dec and dust estimate
		#ra = self.exposure.platedbExposure.observation.plate_pointing.pointing.center_ra
		#dec = self.exposure.platedbExposure.observation.plate_pointing.pointing.center_dec
		#dmap = DustMap()
		#dvals = dmap(ra, dec)

		if camera[0] == 'b':
			bosssn2 = 3.6
			scale = 1.0
			#kappa = dvals['gIncrease'].data[0]
		elif camera[0] == 'r':
			bosssn2 = 7.5
			scale = 1.25
			#kappa = dvals['iIncrease'].data[0]

		# simulated SN2 for a given camera, for a given exposure (via airmass)
		airmass = self.exposure.taiToAirmass()
		simSN2 = bosssn2 / (math.pow(airmass, scale) * kappa)

		if camera == 'b1': normSN2 = self.b1_sn2 / simSN2
		if camera == 'b2': normSN2 = self.b2_sn2 / simSN2
		if camera == 'r1': normSN2 = self.r1_sn2 / simSN2
		if camera == 'r2': normSN2 = self.r2_sn2 / simSN2

		return normSN2

class CurrentStatus(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.current_status']
	else:
		__tablename__ = 'current_status'
		__table_args__ = {'autoload': True, 'schema': 'mangadb'}

	def __repr__(self):
		return '<Current_Status (pk={0}, exp={1}, mjd={2}, flavor={3}, unplugIFU={4})>'.format(self.pk,
		self.exposure_no, self.mjd, self.flavor, self.unpluggedifu)

class Filelist(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.filelist']
	else:
		__tablename__ = 'filelist'
		__table_args__ = {'autoload':True, 'schema': 'mangadb'}

	def __repr__(self):
		return '<Filelist (pk={0},name={1},path={2})'.format(self.pk,self.name,self.path)

class Plate(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadb.plate']
	else:
		__tablename__ = 'plate'
		__table_args__ = {'autoload':True, 'schema': 'mangadb'}

	def __repr__(self):
		return '<Plate (pk={0}, plate_id={1})'.format(self.pk,self.platedbPlate.plate_id)


# ========================
# Define relationships
# ========================
Exposure.set = relationship(Set, backref="exposures")
Exposure.status = relationship(ExposureStatus, backref="exposures")
Exposure.platedbExposure = relationship(platedb.Exposure, backref='mangadbExposure')
Exposure.spectra = relationship(Spectrum, backref="exposures")
Exposure.datacubes = relationship(DataCube, backref="exposures")

ExposureToData_cube.exposure = relationship(Exposure, backref="exposuresToDatacubes")
ExposureToData_cube.datacube = relationship(DataCube, backref="exposuresToDatacubes")

DataCube.plate = relationship(platedb.Plate, backref='dataCube')

Spectrum.datacube = relationship(DataCube, backref="spectrum")
Set.status = relationship(SetStatus, backref="sets")

SN2Values.exposure = relationship(Exposure, backref='sn2values')

Plate.platedbPlate = relationship(platedb.Plate, backref=backref("mangadbPlate", uselist=False))


# ---------------------------------------------------------
# Test that all relationships/mappings are self-consistent.
# ---------------------------------------------------------
from sqlalchemy.orm import configure_mappers
try:
	configure_mappers()
except RuntimeError, error:
	print """
mangadb.ModelClasses:
An error occurred when verifying the relationships between the database tables.
Most likely this is an error in the definition of the SQLAlchemy relationships -
see the error message below for details.
"""
	print "Error type: %s" % sys.exc_info()[0]
	print "Error value: %s" % sys.exc_info()[1]
	print "Error trace: %s" % sys.exc_info()[2]
	sys.exit(1)

# ----------------------------------------
# If no cached metadata was found, save it
# ----------------------------------------
if use_cache:
	if not cached_metadata:
		# cache the metadata for future loading
		# - MUST DELETE IF THE DATABASE SCHEMA HAS CHANGED
		try:
			if not os.path.exists(cache_path):
				os.makedirs(cache_path)
			with open(os.path.join(cache_path, metadata_pickle_filename), 'w') as cachefile:
				pickle.dump(obj=Base.metadata, file=cachefile)
		except:
			# couldn't write the file for some reason
			pass

