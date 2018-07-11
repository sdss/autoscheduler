#!/usr/bin/python

# -------------------------------------------------------------------
# Import statements
# -------------------------------------------------------------------
import os
import sys
from decimal import *

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relationship, exc, column_property, deferred
from sqlalchemy import orm
from sqlalchemy.schema import Column
from sqlalchemy.dialects.postgresql import *
from sqlalchemy.types import Float
from sqlalchemy.orm.session import Session
from sqlalchemy import String # column types, only used for custom type definition
from sqlalchemy import func # for aggregate, other functions

from plateDBtools.database.DatabaseConnection import DatabaseConnection
import plateDBtools.database.apo.platedb.ModelClasses as platedb
import plateDBtools.database.apo.mangadb.ModelClasses as mangadb

db = DatabaseConnection()

metadata_pickle_filename = "ModelClasses_apo_mangaDOSModel.pickle"

# ------------------------------------------
# Load the cached metadata if it's available
# ------------------------------------------
# NOTE: delete this cache is the database schema changes!!
# TODO: determine this programmatically (may not be possible)
# Only attempt to read/write the cache if the environment
# variable "MODEL_CLASSES_CACHE" is set to "YES".
use_cache = "MODEL_CLASSES_CACHE" in os.environ and os.environ["MODEL_CLASSES_CACHE"] == "YES"
if use_cache:
    cache_path = os.path.join(os.path.expanduser("~"), ".sqlalchemy_cache")
    cached_metadata = None
    if os.path.exists(cache_path):
        try:
            cached_metadata = pickle.load(open(os.path.join(cache_path, metadata_pickle_filename)))
        except IOError:
            # cache file not found
            pass
else:
    cached_metadata = False
# ------------------------------------------

# ========================
# Define database classes
# ========================
Base = db.Base

class ExposureFile(Base):
	if cached_metadata:
		__table__ = cached_metadata.tables['mangadosdb.exposure_file']
	else:
		__tablename__ = 'exposure_file'
		__table_args__ = {'autoload': True, 'schema' : 'mangadosdb'}
		
	def __repr__(self):
		return '<ExposureFile (pk={0}, filename={1})'.format(self.pk, self.filename)
		
	def getHeaderValue(self, key):
	    ''' Return the header value for a specified header keyword '''
	    keylist = 	[val.keyword.label for val in self.header]
	    
	    if key.upper() in keylist:
	        return str(self.header[keylist.index(key.upper())].value)
	    else:
	        return None
	
	def getHeader(self):
	    ''' Return the header as a dict'''
	    return {str(val.keyword.label):str(val.value) for val in self.header}

class Fiber(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.fiber']
    else:
        __tablename__ = 'fiber'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb', 'extend_existing':True}
	
	flux = deferred(Column(ARRAY(Float)))
	ivar = deferred(Column(ARRAY(Float)))
	wavelength = deferred(Column(ARRAY(Float)))
	dispersion = deferred(Column(ARRAY(Float)))
		
	def __repr__(self):
		return '<Fiber (pk={0})>'.format(self.pk)

class Flat(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.flat']
    else:
        __tablename__ = 'flat'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Flat (pk={0})'.format(self.pk)
	
 	@property
 	def wavelength(self):
 		return self.fiber.wavelength
 	
 	@property
 	def dispersion(self):
 		return self.fiber.dispersion
			
class Arc(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.arc']
    else:
        __tablename__ = 'arc'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Arc (pk={0})>'.format(self.pk)
		
 	@property
 	def wavelength(self):
 		return self.fiber.wavelength
 	
 	@property
 	def dispersion(self):
 		return self.fiber.dispersion	

class PipelineInfo(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.pipeline_info']
    else:
        __tablename__ = 'pipeline_info'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Pipeline_Info (pk={0})>'.format(self.pk)

class PipelineVersion(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.pipeline_version']
    else:
	__tablename__ = 'pipeline_version'
	__table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Pipeline_Version (pk={0}, version={1})>'.format(self.pk, self.version)

class PipelineStage(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.pipeline_stage']
    else:
        __tablename__ = 'pipeline_stage'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Pipeline_Stage (pk={0}, label={1})>'.format(self.pk, self.label)
	
class PipelineCompletionStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.pipeline_completetion_status']
    else:
        __tablename__ = 'pipeline_completion_status'
        __table_args__ = {'autoload': True, 'schema': 'mangadosdb'}

	def __repr__(self):
		return '<Pipeline_Completion_Status (pk={0}, label={1})>'.format(self.pk, self.label)
		
class PipelineName(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.pipeline_name']
    else:
        __tablename__ = 'pipeline_name'
        __table_args__ = {'autoload': True, 'schema': 'mangadosdb'}

	def __repr__(self):
		return '<Pipeline_Name (pk={0}, label={1})>'.format(self.pk, self.label)
		      
class FitsHeaderValue(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.fits_header_value']
    else:
        __tablename__ = 'fits_header_value'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Fits_Header_Value (pk={0})'.format(self.pk)

class FitsHeaderKeyword(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.fits_header_keyword']
    else:
        __tablename__ = 'fits_header_keyword'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Fits_Header_Keyword (pk={0}, label={1})'.format(self.pk,self.label)

class FiberType(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.fiber_type']
    else:
        __tablename__ = 'fiber_type'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Fiber_Type (pk={0},label={1})'.format(self.pk,self.label)

class IFUBundle(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.ifu_type']
    else:
        __tablename__ = 'ifu_bundle'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<IFU_Bundle (pk={0})'.format(self.pk)

class IFUToBlock(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.ifu_to_block']
    else:
        __tablename__ = 'ifu_to_block'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<IFU_to_Block (pk={0})'.format(self.pk)

class SlitBlock(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.slit_block']
    else:
        __tablename__ = 'slit_block'
        __table_args__ = {'autoload' : True, 'schema' : 'mangadosdb'}

	def __repr__(self):
		return '<Slit_Block (pk={0})'.format(self.pk)

class IFUPluggingStatus(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.ifu_plugging_status']
    else:
        __tablename__ = 'ifu_plugging_status'
        __table_args__ = {'autoload': True, 'schema': 'mangadosdb'}
	
	def __repr__(self):
		return '<IfuPluggingStatus (pk={0},label={1})>'.format(self.pk, self.label)

class HarnessName(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.harness_name']
    else:
        __tablename__ = 'harness_name'
        __table_args__ = {'autoload': True, 'schema': 'mangadosdb'}
	
	def __repr__(self):
		return '<HarnessName (pk={0}, name={1})>'.format(self.pk, self.label)

class IFUToHarname(Base):
    if cached_metadata:
        __table__ = cached_metadata.tables['mangadosdb.ifu_to_harname']
    else:
        __tablename__ = 'ifu_to_harname'
        __table_args__ = {'autoload': True, 'schema': 'mangadosdb'}
	
	def __repr__(self):
		return '<IFU_to_Harname (pk={0})>'.format(self.pk)		
				
# ========================
# Define relationships
# ========================

ExposureFile.pipelineInfo = relationship(PipelineInfo, backref="exposurefile")
ExposureFile.exposure = relationship(mangadb.Exposure, backref="exposurefile")

Fiber.flat = relationship(Flat, backref="fiber")
Fiber.arc = relationship(Arc, backref="fiber")
Fiber.fibertype = relationship(FiberType, backref='fiber')
Fiber.exposureFile = relationship(ExposureFile, backref='fiber')
Fiber.harname = relationship(HarnessName, backref='fiber')

FitsHeaderValue.exposure = relationship(ExposureFile, backref="header")
FitsHeaderValue.keyword = relationship(FitsHeaderKeyword, backref="value")

IFUBundle.harname = relationship(HarnessName, secondary=IFUToHarname.__table__, backref='ifubundle')
IFUBundle.block = relationship(SlitBlock, secondary=IFUToBlock.__table__, backref='ifubundle')
IFUBundle.status = relationship(IFUPluggingStatus, backref='ifubundle')

PipelineInfo.name = relationship(PipelineName, backref="pipeinfo")
PipelineInfo.stage = relationship(PipelineStage, backref="pipeinfo")
PipelineInfo.version = relationship(PipelineVersion, backref="pipeinfo")
PipelineInfo.completionStatus = relationship(PipelineCompletionStatus, backref="pipeinfo")

mangadb.SN2Values.pipelineInfo = relationship(PipelineInfo, backref='sn2values')
					   
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
