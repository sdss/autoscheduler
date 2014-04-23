# -*- coding: utf-8 -*-

"""The application's Globals object"""

__all__ = ['Globals']

from numpy import arange
import logging

class Globals(object):
	"""Container for objects available throughout the life of the application.

	One instance of Globals is created during application initialization and
	is available during requests via the 'app_globals' variable.

	"""
	
	default_dictionary = dict(true=True, false=False)
	default_num_plates = 20
	
	# We only want BOSS and MARVELS plates..
	survey_colors = {"BOSS" : "#5679FF", 
					 "MARVELS" : "#42BE4B",
					 "APOGEE" : "#A423C1"}
#					 "APOGEE" : "#9EDECA"}
	
	page_colors = {}
	page_colors["current_time"] = "#C1FFF6"
	page_colors["twilight"] = "#D6C9E6"
	page_colors["zenith_watch"] = "#FD9C2A"
	page_colors["zenith_warning"] = "#FF3333"
	page_colors["plugged"] = "#CCCCCC"
	page_colors["completed_plugged_bg"] = "#C9FFC3"
	page_colors["special"] = "#FFF800"
	default_dictionary["page_colors"] = page_colors
	
	# Set various APO specific objects
	apo_lat = 32.7802778 # APO's Latitude in degrees
	apo_lon = 105.820278 # APO's Longitude WEST in degrees
	
	# Bin size for graphical visibility window tables
	bin_size = 0.25
	hours = arange(0.0,14.0,bin_size)
	logger = logging.getLogger('platewebapp')
	
	def __init__(self):
		"""Do nothing, by default."""
		pass
