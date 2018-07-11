
from __future__ import print_function

import numpy as np

# NOTE: need this because numpy uint64 bit shifting is broken:
# https://github.com/numpy/numpy/issues/1931
lsh = lambda x,s: np.uint64(x)*np.uint64(2**s)

class PhotoObjID(object):
	''' A class for handling SDSS photoObjID values. '''
	def __init__(self, objid=None, run=None, rerun=None, camcol=None, field=None, id=None, skyversion=2):
		self.objid = None
		if objid:
			self.objid=objid
		else:
		   if isinstance(rerun, str):
		       rerun = int(rerun)
		   self.objid = np.uint64(0) # this line seems unnecessary
		   firstfield = 0
		   self.objid = (lsh(0,63) | lsh(skyversion,59) | lsh(rerun,48) |
		   				 lsh(run,32) | lsh(camcol,29) | lsh(0,28) | lsh(firstfield,28) | lsh(field,16) | lsh(id,0))

	@property
	def id(self):
		return self.objid
	
	def __repr__(self):
		''' TODO: print component fields when the code is ready to break them down from the ID! '''
		return "<SDSS PhotoObjID: {0}>".format(self.objid)
	
class SpecObjID(object):
	''' A class for handling SDSS specObjID values. '''

	def __init__(self, plate=None, mjd=None, fiber=None, run2d=None, dr=None):
		
		if dr:
			dr = dr.lower()
		if run2d:
			run2d = run2d.lower()
		
		if dr == "dr8":
			raise Exception("The run2d value must be specified for DR8. "
							"There are three possible values: 26 (the pipeline version for DR7), "
							"103 (a special version of the pipeline to handle stellar cluster plates), and 104.")
		elif dr == "dr9":
			if run2d is not None and run2d != "v5_4_45":
				raise Exception("The run2d value of '{0}' is not valid for the DR9 data release.".format(run2d))
			else:
				run2d = "v5_4_45"
		elif dr == "dr10":
			if run2d is not None and run2d != "v5_5_12":
				raise Exception("The run2d value of '{0}' is not valid for the DR10 data release.".format(run2d))
			else:
				run2d = "v5_5_12"
		elif dr == "dr11":
			if run2d is not None and run2d != "v5_6_5":
				raise Exception("The run2d value of '{0}' is not valid for the DR11 data release.".format(run2d))
			else:
				run2d = "v5_6_5"
		elif dr == "dr12":
			raise Exception("Can someone look up the run2d value for DR12?")
			run2d = ""
		else:
			raise Exception("An unknown data release value was provided: '{0}'".format(dr))
	
		self.specobjid = np.uint64(0)
		if isinstance(run2d,basestring):
			n,m,p = run2d.split('_')
			n = int(n[1:])
			m = int(m)
			p = int(p)
			run2d = (n-5)*10000 + m*100 + p
		self.specobjid |= lsh(plate,50) | lsh(fiber,38) | lsh(mjd-50000,24) | lsh(run2d,10)

	def id(self):
		return self.objid
	
	def __repr__(self):
		''' TODO: print component fields when the code is ready to break them down from the ID! '''
		return "<SDSS SpecObjID: {0}>".format(self.objid)
	
