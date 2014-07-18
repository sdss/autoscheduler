# -*- coding: utf-8 -*-

"""Helpers used in platewebapp2."""
from flask import current_app
import datetime
from petunia.lib import app_globals
import numpy as np
from sdss.utilities import convert
#from webhelpers import date, feedgenerator, html, number, misc, text

def filterPlates(plateList, evening_twilight, morning_twilight, nowDatetime, maxNumber=30, plugged=False):
    """ sdfjsakdf
    """
    # Empty list to fill with PlatePointing objects
    platePointings = list()
    
    for plate in plateList:
        for platePointing in plate.plate_pointings:
            if len(platePointings) >= maxNumber: return platePointings
            
            # PlatePointing.times returns a dictionary of times for the object:
            #      key   |   value
            #   ---------------------
            #   nominal  |  nominal observing time for the plate, UTC
            #   min      |  minimum acceptable observing time for the plate, UTC
            #   max      |  maximum acceptable observing time for the plate, UTC
            # see platedb ModelClasses for more info on this function
            platePointing_times = platePointing.times(nowDatetime)
            platePointing_times['begintime'] = convert.datetime2decHour(platePointing_times['min'])
            
            try:
                plateTileStatus = plate.tile.calculatedTileStatus()
            except: # Plate has no associated tile, or MARVELS / APOGEE
                plateTileStatus = "???"
                
            # Display window is from 0 to 13 UTC
            # If both min and max times are outside this window, continue
            # Later code will handle min>max, e.g. when plate starts before APOJD rollover
            mintime = convert.datetime2decHour(platePointing_times['min'])
            maxtime = convert.datetime2decHour(platePointing_times['max'])
            current_app.logger.debug("ID, min, max | %d | %.3f | %.3f | %.3f | %.3f" % (plate.plate_id, mintime, maxtime, evening_twilight, morning_twilight))
            
            # If outside window, go to next plate pointing for the plate
            if mintime > 13 and maxtime > 13: 
                continue
            # If tile is complete, this plate is done
            elif "Complete" in plateTileStatus: 
                break
            
            if not plugged:
                # Don't display plates which aren't visible for very long
                if maxtime - evening_twilight < 1.0:  #- units: hours
                    current_app.logger.debug("WARNING: Drop plate %d with short evening visibility: %.f min" % (plate.plate_id, 60*(maxtime-evening_twilight)))
                    if maxtime - evening_twilight > 0.5:  #- units: hours
                        current_app.logger.debug("plate %d observable for %.f minutes" % (plate.plate_id, 60*(maxtime-evening_twilight)))
                    break
                elif maxtime > morning_twilight and morning_twilight - mintime < 1.0:
                    current_app.logger.debug("WARNING: Drop plate %d with short morning visibility: %.f min" % (plate.plate_id, 60*(morning_twilight-mintime)))
                    break
                
            platePointings.append(platePointing)
            
    return platePointings
    
def platePointingObservabilityColors(platePointing, evening_twilight, morning_twilight, nowDatetime, hourTicker=False):
    plate = platePointing.plate
    platePointing_times = platePointing.times(nowDatetime)
    
    # For each hour on the visibility plot, the following routine figures out what color 
    #	to display in the square as follows for any given half-hour:
    #	- If the pointing is within 3 degrees of Zenith, color red
    #	- If the pointing is between 5 degrees and 3 degrees of Zenith, color yellow
    #	- If the plate isn't visible, color white
    #	- If none of those conditions are met, color it based on what survey it is				
    bgcolors = dict()
    for dec_hr in np.arange(0.0,14.0,app_globals.app_globals.bin_size):
        hour = np.floor(dec_hr)
        mins = (dec_hr - hour) * 60.0
        
        #- Fill in default background colors
        if "Complete" in plate.calculatedCompletionStatus():
            bgcolors[dec_hr] = app_globals.app_globals.page_colors["completed_plugged_bg"]
        else:
            bgcolors[dec_hr] = "#FFFFFF"
        
        hrDatetime = datetime.datetime.combine(nowDatetime.date(),datetime.time(int(hour),int(mins),0))
        
        # Calculate the altitude of the pointing at the hour
        pntg_alt, pntg_az = convert.raDec2AltAz(float(platePointing.pointing.center_ra), float(platePointing.pointing.center_dec), app_globals.app_globals.apo_lat, app_globals.app_globals.apo_lon, hrDatetime)
        
        # If the minimum time is greater than the maximum time, i.e. the observing time wraps around a day,
        #	do something special to determine what cells to color in
        if convert.datetime2decHour(platePointing_times['min']) > convert.datetime2decHour(platePointing_times['max']):
            if ((24.0 - convert.datetime2decHour(platePointing_times['nominal'])) < convert.datetime2decHour(platePointing_times['nominal']) and \
                dec_hr > convert.datetime2decHour(platePointing_times['min'])) or\
                dec_hr <= convert.datetime2decHour(platePointing_times['max']):

                bgcolors[dec_hr] = app_globals.app_globals.survey_colors[plate.surveys[0].label]
                
                if pntg_alt > 85.0 and pntg_alt < 87.0:
                    bgcolors[dec_hr] = app_globals.app_globals.page_colors["zenith_watch"]
                elif pntg_alt > 87.0:
                    bgcolors[dec_hr] = app_globals.app_globals.page_colors["zenith_warning"]
            
        # If the min, or the max lie within this half hour and the next half hour, or if this half hour
        #	is between the two, color the cell the survey color
        elif convert.datetime2decHour(platePointing_times['min']) >= dec_hr and convert.datetime2decHour(platePointing_times['min']) < dec_hr+app_globals.app_globals.bin_size or \
            dec_hr > convert.datetime2decHour(platePointing_times['min']) and dec_hr < convert.datetime2decHour(platePointing_times['max']) or \
            convert.datetime2decHour(platePointing_times['max']) >= dec_hr and convert.datetime2decHour(platePointing_times['max']) < dec_hr+app_globals.app_globals.bin_size :
        
            bgcolors[dec_hr] = app_globals.app_globals.survey_colors[plate.surveys[0].label]
            
            # If the plate is near Zenith, color it yellow or red depending on
            #	how close it is
            if pntg_alt > 85.0 and pntg_alt < 87.0:
                bgcolors[dec_hr] = app_globals.app_globals.page_colors["zenith_watch"]
            elif pntg_alt > 87.0:
                bgcolors[dec_hr] = app_globals.app_globals.page_colors["zenith_warning"]
                            
        if evening_twilight > dec_hr+app_globals.app_globals.bin_size and (bgcolors[dec_hr] == "#FFFFFF" or bgcolors[dec_hr] == app_globals.app_globals.page_colors["plugged"]):
            bgcolors[dec_hr] = app_globals.app_globals.page_colors["twilight"]
        if morning_twilight < dec_hr+app_globals.app_globals.bin_size and (bgcolors[dec_hr] == "#FFFFFF" or bgcolors[dec_hr] == app_globals.app_globals.page_colors["plugged"]):
            bgcolors[dec_hr] = app_globals.app_globals.page_colors["twilight"]
        
        if hourTicker:
            current_dec_hr = nowDatetime.hour + nowDatetime.minute/60.0
            if current_dec_hr >= dec_hr and current_dec_hr < dec_hr+app_globals.app_globals.bin_size and bgcolors[dec_hr] not in app_globals.app_globals.survey_colors.values():
                bgcolors[dec_hr] = app_globals.app_globals.page_colors["current_time"]
        
    return bgcolors
