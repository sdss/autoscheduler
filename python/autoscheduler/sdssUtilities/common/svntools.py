#!usr/bin/env python

from __future__ import print_function
from __future__ import division
import subprocess

__author__ = 'Brian Cherinka'


###
class SVN():
    ''' A svn class for controlling svn commands '''
    
    def __init__(self):
        pass
        
    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return ('SVN Class')
        
    def accessCheck(self, path):
        ''' Check the SVN access '''
        
        svnCMD = 'svn ls {0} > /dev/null'.format(path)
        try:
            subprocess.call(svnCMD, shell=True)
            return True
        except:
            return False
	
    def add(self, path):
        ''' Adds a file to the repository.'''
	    
        try:
            subprocess.check_output('svn add {0}'.format(path), shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Could not add to svn: {0} \n {1}'.format(path,e))

    def commit(self, path, message=None):
        ''' Commits changes to the SVN repo '''
        
        if not message: message = 'committed files'
        
        try:
            subprocess.check_output('svn commit {0} -m "{1}"'.format(path,message), shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Commit failed on {0} \n {1}'.format(path,e))
            self.cleanUp(path)
	        
    def update(self, path):
        ''' Updates the SVN repository '''
        
        try:
            subprocess.check_output('svn update {0}'.format(path), shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Update failed on {0} \n {1}'.format(path,e))
	        
    def check(self, path):
        ''' Checks the ensure access to log file.  Returns false if unable.'''
        
        try:
            subprocess.check_output('svn ls {0}'.format(path), shell=True, stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Check failed on {0} \n {1}'.format(path,e))
            
    def cleanUp(self, path):
        ''' Clean up an SVN directory on failure.'''
        
        try:
            subprocess.check_output('svn cleanup {0}'.format(path), shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Cleanup failed on {0} \n {1}'.format(path,e))

