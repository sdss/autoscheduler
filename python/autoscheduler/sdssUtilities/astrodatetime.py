################################################################################
#
# astrodatetime.py - A subclass of the Python class 'datetime.datetime' to 
#                    include support for Modified Julian Date's and Julian Dates
#
# Copyright (C) 2011 Adrian Price-Whelan
#
# Notes:
#
################################################################################

# Standard Library
from datetime import datetime, tzinfo, timedelta
import pytz

import convert

class GMT0(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=0)
    def tzname(self,dt): 
        return "GMT +0" 
    def dst(self,dt): 
        return timedelta(0)

gmt = GMT0()

class datetime(datetime):
    
    @property
    def mjd(self):
        """ Calculate the Modified Julian Date (MJD) using the datetime object """
        return convert.datetime2mjd(self)
    
    @property
    def jd(self):
        """ Calculate the Julian Date (JD) using the datetime object """
        return convert.datetime2jd(self)
    
    @property
    def sdssjd(self):
        """ Calculate the SDSS Julian Date (SJD or SDSSJD) using the datetime object """
        return convert.mjd2sdssjd(convert.datetime2mjd(self))

    def lst(self, longitude):
        """ Compute the Local Sidereal Time for the datetime object 
            given the a longitude in degrees West
        """
        try:
            utcSelf = self.astimezone(gmt)
        except ValueError:
            raise ValueError("In order to calculate the Local Sidereal Time, you must specify the timezone of the datetime object.\nYou must create a tzinfo() object, and do datetimeObject = datetimeObject.replace(tzinfo=someTimeZone)")
        print "utc", utcSelf.hour, utcSelf.minute, utcSelf.second
        gmst = convert.utcDatetime2gmst(utcSelf)
        return convert.gmst2lst(longitude, gmst.hour, gmst.minute, gmst.second)
    
    @staticmethod
    def fromMJD(mjd):
        """ Create a datetime object from a Modified Julian Date (MJD) """
        dt = convert.mjd2datetime(mjd)
        return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
        
    @staticmethod
    def fromJD(jd, tz=None):
        """ Create a datetime object from a Julian Date (JD) """
        dt = convert.jd2datetime(jd)
        return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
    
    @property
    def decimalTime(self):
        """ Return the decimal time in hours """
        return float(self.hour) + self.minute/60.0 + (self.second+self.microsecond*1e-5)/3600. 
    
    @staticmethod
    def anow(tz=None):
        """ Because datetime's built-in now() method returns a regular datetime object, so this is 
            a special function to return an astrodatetime.datetime object instead"""
        now = datetime.now(tz)
        return datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond, tzinfo=tz)
    
    @staticmethod
    def fromDatetime(datetimeObj):
        return datetime(datetimeObj.year, datetimeObj.month, datetimeObj.day, datetimeObj.hour, datetimeObj.minute, datetimeObj.second, datetimeObj.microsecond, tzinfo=datetimeObj.tzinfo)

if __name__ == "__main__":
    # Functional and unit tests
    
    # Create a datetime object from a JD
    jd = 2455555.3228258542
    dt = datetime.fromJD(jd)
    print "Entered jd: %.10f" % jd
    print "Calculated jd: %.10f" % dt.jd
    print "Difference: %.5f seconds" % abs((dt.jd - jd) * 24 * 60 * 60)
    
    # Create a datetime object from an MJD
    mjd = 55555.922842219874
    dt = datetime.fromMJD(mjd)
    print "Entered mjd: %.10f" % mjd
    print "Calculated mjd: %.10f" % dt.mjd
    print "Difference: %.5f seconds" % abs((dt.mjd - mjd) * 24 * 60 * 60)
    
    # Calculate an LST at APO, which is at GMT-7 hours
    class GMTm7(tzinfo):
        def utcoffset(self, dt):
            return timedelta(hours=-7)
        def tzname(self,dt): 
            return "GMT -7" 
        def dst(self,dt): 
            return timedelta(0)
        
    g = GMTm7()
    dt = datetime.anow(g)
    print dt.lst(105.006)
