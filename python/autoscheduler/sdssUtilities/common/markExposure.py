#!/usr/bin/env python

from __future__ import print_function
from __future__ import division

import os, glob, shutil
import numpy as np
from autoscheduler.


 autoscheduler.
 autoscheduler.sdssUtilies import yanny as yanny
from svntools import SVN
from astropy.io import fits
from astropy.table import Table
from autoscheduler.


 autoscheduler.
 autoscheduler.sdssUtilies.reformatAstropyColumn import reformatAstropyColumn

from bs4 import BeautifulSoup

__author__ = 'Brian Cherinka'

'''

Name:
    markExposure

Purpose:
	Marks the status of exposures.
	Writes a header fix file into mangacore, and updates the html logfile and current html.
  
Revision History:
    May-2015 - written by B. Cherinka (Toronto)

'''

# Update the status of exposure
def updateExposureHtml(filename, mjd, exp, status):
    ''' Update the exposure status in the log file. '''
    
    if os.path.isfile(filename):
        f = open(filename,'r+')
        out = f.read()
        f.seek(0,0) # this is needed to overwrite html log contents, otherwise cart sections repeat
        try:
            soup = BeautifulSoup(out)
        except:
            f.close()
            raise RuntimeError('Beautiful Soup 4 not installed for python.  Cannot update logfile.')
            return
             
        # check MJD in title
        if str(mjd) in soup.title.string:
            print('Found MJD {0} in file {1}. Updating.'.format(mjd,filename))
            # get quality header index
            alltr = soup.find_all('tr')
            thstrings = [th.string.strip() for th in alltr[2].find_all('th')]
            qualind = thstrings.index(u'QUALITY')
            
            # find matching row to exposure
            good=[(i,tr) for i,tr in enumerate(alltr) if tr.th and '-00{0}'.format(exp) in tr.th.string]
            if any(good):
                for row in good:
                    # select quality td
                    qualtd = row[1].find_all('td')[qualind-1]
                    # build new tag
                    newtag=soup.new_tag('b')
                    newtag.insert(1,soup.new_tag('font'))
                    newtag.font['color']='#FF0000'
                    newtag.font.string=' {0} '.format(status)
                    # replace string text
                    try:
                        qualtd.string.replace_with(newtag)
                    except:
                        print('Could not replace string {0} with new tag value {1}'.format(qualtd,newtag))
            else:
                f.close()
                raise RuntimeError('No exposure found. {0} should not be modified.'.format(filename))
            
            # Write out the html file
            psoup = soup.prettify(formatter='html')
            f.write(str(psoup))
            f.truncate()
            f.close()
        else:
            f.close()
            raise RuntimeError('MJD {0} not found in html logfile {1}! Exiting.'.format(mjd,filename))
    else:
        raise IOError('Logfile {0} does not exist yet. Please wait?'.format(filename))

    
# Update the HTML log file
def updateLogHtml(mjd, exp, status, quickdir, test=None):
    ''' Updates quality of the exposure in the logfile html for the given MJD '''
            
    single = os.path.join(quickdir,mjd,'web')
    singlefile = os.path.join(single,'logfile-{0}.html'.format(mjd))
    logdir = os.path.join(quickdir,'combined')
    logfile = os.path.join(logdir,'logfile-{0}.html'.format(mjd))
    currentfile = os.path.join(logdir,'logfile-current.html')

    updateExposureHtml(singlefile, mjd, exp, status)
    #updateExposureHtml(logfile, mjd, exp, status) #commenting out due to new symbolic links, temp for now
    #updateExposureHtml(currentfile, mjd, exp, status)

# Update the FITS
def updateFits(data, exp, mjd, status):
    ''' Update the actual fits file '''
    
    # reformat quality column to larger string
    data = np.array(reformatAstropyColumn(Table(data),'QUALITY', 'S20'))
    
    # set new status
    qualind=np.where(exp == data['EXPNUM'])[0]
    data['QUALITY'][qualind] = status
    
    return data
    
# Update the FITS log file
def updateLog(mjd, exp, status, quickdir, test=None):
    ''' Updates the quality of the exposure in the logfile FITS for the given MJD '''
    
    single = os.path.join(quickdir,str(mjd))
    singlefile = os.path.join(single,'logfile-{0}.fits'.format(mjd))
        
    if os.path.isfile(singlefile):
        print('Updating FITS log file for exposure {0}'.format(exp))
            
        # get the log data
        hdulist = fits.open(singlefile,mode='update')
        bias = hdulist[1].data
        flats = hdulist[2].data
        arcs = hdulist[3].data
        sci = hdulist[4].data

        # find the exposure
        try: inbias = exp in bias['expnum']
        except: inbias = None
        try: inflat = exp in flats['expnum']
        except: inflat = None
        try: inarc = exp in arcs['expnum']
        except: inarc = None
        try: insci = exp in sci['expnum']
        except: insci = None
        
        # No exposure found in any extension
        if not any([inbias,inflat,inarc,insci]):
            raise RuntimeError('Exposure {0} does not exist in {1}'.format(exp,singlefile))

        # update the fits
        if inbias: data = updateFits(bias, exp, mjd, status)
        elif inflat: data = updateFits(flats, exp, mjd, status)
        elif inarc: data = updateFits(arcs, exp, mjd, status)
        elif insci: data = updateFits(sci, exp, mjd, status)

        # write and close the fits
        if inbias: hdulist[1].data = data
        elif inflat: hdulist[2].data = data
        elif inarc: hdulist[3].data = data
        elif insci: hdulist[4].data = data
        hdulist.close(output_verify='ignore')
            
        # copy it to /combined
        outdir = os.path.join(quickdir,'combined')
        outfile = os.path.join(outdir,'logfile-{0}.fits'.format(mjd))
        #shutil.copy2(singlefile, outfile)
    else:
        raise IOError('FITS logfile {0} does not exist. Please wait?'.format(singlefile))

# Update the redux files
def updateRedux(mjd, exp, status, quickdir, test=None):
    ''' Update the reductions if they exist already '''
    
    mjd = str(mjd)
        
    print('Updating calibration reductions for exposure {0}'.format(exp))
    indir = os.path.join(quickdir,mjd)
    files = glob.glob(os.path.join(indir,'mg*{0}*.fits'.format(exp)))
    if files:
        for file in files:
            hdu = fits.open(file,mode='update')
            hdr = hdu[0].header
            try: val = hdr['QUALITY']
            except: val = None
            if val:
                print('Updating header for file {0}, exposure status {1} to {2}'.format(file,val,status))
                hdr['QUALITY'] = status.lower()
                hdu.close(output_verify='ignore')
    else:
        raise IOError('No reductions found for exposure {0}, MJD {1}. Please wait?'.format(exp,mjd))

# Copy test files for given explist
def copyTestFiles(mjd, exposure, status, quickdir):
    ''' Copy test files for the given exposure, mjd into test directory '''
    
    exp = str(exposure)
    mjd = str(mjd)
    realquickdir = os.getenv('MANGA_QUICK')
    
    files = {'fits': 'logfile-{0}.fits'.format(mjd),
                'web':'logfile-{0}.html'.format(mjd),
                'redux':[]}
    reduxfiles = glob.glob(os.path.join(realquickdir,mjd,'mg*{0}*.fits'.format(exp)))
    outreduxfiles = [os.path.join(quickdir,os.path.dirname(f).rsplit('/',1)[1],os.path.basename(f)) for f in reduxfiles]
    files['redux'] =  reduxfiles
    
    for key,val in files.iteritems():
        if key == 'fits':
            infile = os.path.join(realquickdir,mjd,val)
            outfile = os.path.join(quickdir, mjd, val)
            outcombfile = os.path.join(quickdir,'combined',val)
            shutil.copy2(infile, outfile)
            os.symlink(outfile,outcombfile)
        elif key == 'web':
            infile = os.path.join(realquickdir,mjd,'web',val)
            outfile = os.path.join(quickdir,mjd,'web',val)
            outcombfile = os.path.join(quickdir,'combined',val)
            outcombcurrfile = os.path.join(quickdir,'combined','logfile-current.html')
            shutil.copy2(infile, outfile)
            os.symlink(outfile,outcombfile)
            os.symlink(outfile,outcombcurrfile)
        elif key == 'redux':
            for i,file in enumerate(val):
                shutil.copy2(file, outreduxfiles[i])
    
# Make test directories
def makeTestDirs(quickdir, mjd):
    ''' Make the test directories for updating log files '''
    
    # make paths
    mjddir = os.path.join(quickdir, str(mjd))
    webdir = os.path.join(mjddir,'web')
    combdir = os.path.join(quickdir,'combined')
    
    # make dirs
    dirs = [mjddir, webdir, combdir]
    for dir in dirs:
        if not os.path.isdir(dir): os.makedirs(dir)
    
# Commit to repo
def commitFile(hdrfile, dir_existed, file_existed):
    '''
    Commit the header fix file to the repo.
    newdir/newfile: True if the directory or file need to be svn added.
    '''
    
    svn = SVN()

    # add directory
    hdrdir = os.path.dirname(hdrfile)
    if not dir_existed:
        try:
            svn.add(hdrdir)
        except RuntimeError as e:
            raise RuntimeError('svn add of {0} failed: {1}'.format(hdrdir,e))
    
    # SVN add or commit if not in test mode
    if not file_existed:
        try:
            svn.add(hdrfile)
        except RuntimeError as e:
            raise RuntimeError('svn add of {0} failed: {1}'.format(hdrfile,e))

    try:
        svn.commit(hdrfile)
    except RuntimeError as e:
        raise RuntimeError('svn commit of {0} failed: {1}'.format(hdrfile,e))


# Build header fix file path
def buildPath(mjd, test=None):
    ''' Builds the file path to the header fix file'''
    
    # Set header fix file path in mangacore or use a test directory
    if test: hdrpath = os.path.join(os.path.expanduser('~'),'hdrfix')
    else:
        mcdir = os.getenv('MANGACORE_DIR')
        hdrpath = os.path.join(mcdir,'hdrfix')
        
    hdrdir = os.path.join(hdrpath, mjd)
    
    # Set manga dos directory
    if test:
        quickdir = os.path.join(os.path.expanduser('~'),'dostest')
        makeTestDirs(quickdir,mjd)
    else: quickdir = os.getenv('MANGA_QUICK')
        
    return hdrdir, quickdir

# Write the header fix files
def makeHeaderFixFile(mjd, exp, status, hdrdir):
    ''' Write or add to a header fix file in mangacore'''

    # Make full file path name
    hdrfile = os.path.join(hdrdir, 'sdHdrFix-{0}.par'.format(mjd))
        
    # Create header directory if it doesn't exist
    dir_exists = os.path.isdir(hdrdir)
    if dir_exists:
        print('Header fix directory exists.')
    else:
        print('Header fix does not directory exist. Creating it.')
        os.makedirs(hdrdir)
                    
    # Make new data
    newdata = {'fileroot':[],'keyword':[],'value':[]}
    newdata['fileroot'].append('sdR-??-00{0}'.format(exp))
    newdata['keyword'].append('QUALITY')
    newdata['value'].append('{0}'.format(status.upper()))
    order=['fileroot','keyword','value']
    newtable = Table(newdata,dtype=['S15','S15','S15'])
    newtable = newtable[order]
        
    # Append or write to file
    file_exists = os.path.isfile(hdrfile)
    if file_exists:
        print('Header fix file exists.  Updating file and overwriting.')

        # Read header fix file
        hdrfix = yanny.yanny(filename=hdrfile, np=True)
        oldtable = Table(hdrfix['OPHDRFIX'],dtype=['S15','S15','S15'])
        oldtable = oldtable[order]
            
        # Check if new entry inside old
        newinold = newtable['fileroot'] == oldtable['fileroot']
            
        # Update rows
        if not any(newinold):
            # add new row if it doesn't exist
            [oldtable.add_row(row) for row in newtable]
        else:
            # update the row
            fileindex = np.where(newinold)[0]
            for row in newtable:
                if row['value'] in ['GOOD','OVERRIDE GOOD']:
                    oldtable.remove_row(fileindex[0])
                else:
                    oldtable[fileindex] = row
         
        yanny.write_ndarray_to_yanny(hdrfile,np.array(oldtable),structname='OPHDRFIX',overwrite=True)
                           
    else:
        print('No header fix file found.  Creating it')
        yanny.write_ndarray_to_yanny(hdrfile,np.array(newtable),structname='OPHDRFIX')

    return hdrfile, dir_exists, file_exists
   
   
# Mark exposure status
def markStatus(expobj, status, test=None):
    ''' Mark the status of the exposures.
        expobj - single platedb exposure database entry
        status - string of new exposure status, allowed statuses are Good, Bad, Override Good, Override Bad, or Test
        test - boolean to turn write files in a test mode, i.e. to home directory
    '''
    
    # Make strings
    try:
        exposure = str(expobj.exposure_no)
        mjd = str(expobj.mjd())
    except:
        raise RuntimeError('Input exposure object is not of right type.  Needs to be ModelClasses object.')
    
    # Reject Status if not in allowed
    allowedstats = ['Good', 'Bad', 'Override Good', 'Override Bad', 'Test']
    if status not in allowedstats:
        raise RuntimeError('Input status is not one of allowed statuses.  Please use one of {0}'.format(allowedstats))
    
    # Write header fix files
    hdrpath,quickdir = buildPath(mjd, test=test)
    hdrfile, dir_existed, file_existed = makeHeaderFixFile(mjd, exposure, status, hdrpath)
    if not test: commitFile(hdrfile, dir_existed, file_existed)
    
    # Update the log file
    if test: copyTestFiles(mjd, exposure, status, quickdir)
    updateLog(mjd, exposure, status, quickdir, test=test)
    updateLogHtml(mjd, exposure, status, quickdir, test=test)
    
    # Update the redux files
    updateRedux(mjd, exposure, status, quickdir, test=test)

