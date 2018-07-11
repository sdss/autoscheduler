#!/usr/bin/env python
# encoding: utf-8
"""
markPlugging.py

Created by José Sánchez-Gallego on 2 Jun 2015.
Licensed under a 3-clause BSD license.

Revision history:
    2 Jun 2015 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from Totoro.utils import getAPOcomplete
from Totoro.exceptions import NoMangaPlate
from Totoro.dbclasses import Plate
from autoscheduler.


 autoscheduler.
 autoscheduler.sdssUtilies.common.svntools import SVN
import warnings
import os


def getAPOcompletePath(plateid):
    """Returns the path for an APOcomplete file in mangacore."""

    if 'MANGACORE_DIR' not in os.environ:
        raise ValueError('MANGACORE_DIR not defined.')

    dir100Name = '{0:06d}'.format(plateid)[0:4] + 'XX'
    dirPath = os.path.join(os.environ['MANGACORE_DIR'], 'apocomplete',
                           dir100Name)
    if os.path.exists(dirPath):
        dirExisted = True
    else:
        dirExisted = False

    return (os.path.join(dirPath,
                         'apocomp-{0:04d}.par'.format(plateid)), dirExisted)


def commitFile(file, dirExisted=False):
    """Commits a file in a repo."""

    assert os.path.exists(file), 'file does not exist'

    dirname = os.path.dirname(file)

    svn = SVN()

    # Adds the directory or file
    try:
        if not dirExisted:
            svn.add(dirname)
        else:
            svn.add(file)
    except RuntimeError as error:
        raise RuntimeError('svn add of {0} failed: {1}'.format(file, error))

    # Commits
    try:
        if not dirExisted:
            fileToCommit = dirname
        else:
            fileToCommit = file
        svn.commit(fileToCommit, message=('auto-committing {0}'
                                          .format(os.path.basename(file))))
    except RuntimeError as error:
        raise RuntimeError('svn commit of {0} failed: {1}'.format(file, error))


def markPlugging(plate, newStatus, dryrun=False, **kwargs):
    """Checks the status of a plugging. If needed, writes the APOcomplete file.

    This function is called every time a user overrides the status of a
    plugging from Petunia's plate detail page. If the new status is override
    complete and the APOcomplete file for that plate does not exist in
    mangacore, writes the new APOcomplete based on the current set arrangement.

    Parameters
    ----------
    plate : int or ModelClasses object
        The plate_id of the plate whose status is being changed, a
        plateDB.Plate object, or a Totoro.Plate object.
    newStatus : string
        The value of the new status set for the plugging.
    dryrun : bool, optional
        If True, does not write the APOcomplete file to mangacore.

    Returns
    -------
    result : None or APOcomplete-like dict
        None if nothing is changed in the SVN repo. If a new APOcomplete file
        is written, the function returns the APOcomplete dictionary in the
        format returned by `Totoro.Plate.getAPOcomplete()`.

    """

    if isinstance(plate, Plate):
        pass
    else:
        try:
            plate = Plate(plate, format='plate_id', updateSets=False)
        except NoMangaPlate:
            return None
        except Exception as ee:
            warnings.warn('creating plate failed with error: {0}'.format(ee),
                          UserWarning)
            return None

    # If plate is not MaNGA-led, does nothing
    if (not plate.isMaNGA or plate.currentSurveyMode is None or
            plate.currentSurveyMode.label != 'MaNGA dither'):
        return None

    # If status is not Overridden Good, we don't do anything
    if newStatus != 'Overridden Good':
        return None

    # We check if an APOcomplete file aready exists. If so, we do nothing.
    APOcompletePath, dirExisted = getAPOcompletePath(plate.plate_id)
    if os.path.exists(APOcompletePath):
        return None

    # We create the apocomplete file
    APOcompleteDir = os.path.dirname(APOcompletePath)
    if not os.path.exists(APOcompleteDir):
        os.makedirs(APOcompleteDir)

    APOcompleteDict = getAPOcomplete(plate,
                                     createFile=True, path=APOcompleteDir)

    if not dryrun:
        commitFile(APOcompletePath, dirExisted=dirExisted)

    return APOcompleteDict
