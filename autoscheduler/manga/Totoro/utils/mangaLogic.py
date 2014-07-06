#!/usr/bin/env python
# encoding: utf-8
"""
mangaLogic.py

Created by José Sánchez-Gallego on 4 Jul 2014.
Licensed under a 3-clause BSD license.

Contains functions and classes related with the scheduling logic for
MaNGA plates.

Revision history:
    4 Jul 2014 J. Sánchez-Gallego
      Initial version

"""

from __future__ import division
from __future__ import print_function
from .. import Session, plateDB, mangaDB
from .. import config, log
import numpy as np
from ..exceptions import TotoroError
from ..exceptions import TotoroUserWarning
from warnings import warn
from ..utils import mlhalimit


session = Session()


def reorganiseExposures(plate_id, force=False, checkExposures=True):
    """Assigns a set to each exposure for a given plate."""

    from ..dbclasses.set import Set, Exposure

    log.debug('Reorganising exposures for plate_id=%d' % plate_id)

    with session.begin():
        plate = session.query(plateDB.Plate).filter(
            plateDB.Plate.plate_id == plate_id).one()
        exposures = session.query(plateDB.Exposure).join(
            plateDB.ExposureFlavor).join(plateDB.ExposureStatus).join(
                plateDB.Observation).join(plateDB.PlatePointing).join(
                    plateDB.Plate).filter(
                        plateDB.Plate.pk == plate.pk and
                        plateDB.ExposureFlavor.label == 'Science' and
                        plateDB.ExposureStatus.label == 'Good').all()

    expsToSet = []
    for exposure in exposures:

        if len(exposure.mangadbExposure) == 0:
            warn('plateDB exposure pk=%d does not have a mangaDB counterpart' %
                 exposure.pk, TotoroUserWarning)
            continue

        if force:
            removeSet(exposure.mangadbExposure[0].set_pk)
            with session.begin():
                exposure.mangadbExposure[0].set_pk = None
            if checkExposure(exposure.mangadbExposure[0].pk, force=True):
                expsToSet.append(exposure)
        else:
            if (exposure.mangadbExposure[0].set_pk is None and
                    checkExposure(exposure.mangadbExposure[0].pk)):
                expsToSet.append(exposure)

    if force:
        sets = []
    else:

        with session.begin():
            setsDB = session.query(mangaDB.Set).join(mangaDB.Exposure).join(
                plateDB.Exposure).join(plateDB.Observation).join(
                    plateDB.PlatePointing).join(plateDB.Plate).filter(
                        plateDB.Plate.plate_id == plate_id and
                        (mangaDB.Set.status.label == 'Good' or
                         mangaDB.Set.status.label == 'Excellent'))

        sets = [Set(setDB.pk, verbose=False) for setDB in setsDB]

    exps = [Exposure(expDB.pk, verbose=False) for expDB in expsToSet]

    for exp in exps:
        toNewSet = True
        expDitherPosition = exp.ditherPosition
        expHARange = exp.getHARange()

        for set in sets:
            setHALimits = set.getHALimits()
            setDitherPositions = set.getDitherPositions()

            if np.min(expHARange) >= np.min(setHALimits) and \
                    np.max(expHARange) <= np.max(setHALimits):

                if expDitherPosition != 'C' and \
                        expDitherPosition not in setDitherPositions:

                    exp.manga_set_pk = set.pk
                    set.exposures.append(exp)

                    with session.begin():
                        expDB = session.query(mangaDB.Exposure).get(
                            exp.manga_pk)
                        expDB.set_pk = set.pk

                    tmpSet = Set(set.pk, verbose=False)
                    tmpSetQuality = tmpSet.getQuality()
                    del tmpSet

                    if tmpSetQuality in ['Good', 'Excellent', 'Incomplete']:
                        log.debug(
                            'added manga exposure pk=%d to set pk=%d' %
                            (exp.pk, set.pk))
                        toNewSet = False
                        break
                    else:
                        with session.begin():
                            expDB = session.query(mangaDB.Exposure).get(
                                exp.manga_pk)
                            expDB.set_pk = None

        # If the exposure has not been assigned to a set,
        # creates a new one.
        if toNewSet:
            with session.begin():
                newSet = mangaDB.Set()
                session.add(newSet)
                session.flush()
                expDB = session.query(mangaDB.Exposure).get(exp.manga_pk)
                expDB.set_pk = newSet.pk
            sets.append(Set(newSet.pk, verbose=False))
            log.debug('added manga exposure pk=%d to set pk=%d' %
                      (exp.manga_pk, newSet.pk))


def removeSet(set_pk):
    """Removes a set."""

    if set_pk is None:
        return True

    with session.begin():
        set = session.query(mangaDB.Set).get(set_pk)
        if set is None:
            log.debug('removing set pk=%d failed because the set does not' +
                      ' exist.' % set_pk)
            return False
        else:
            session.delete(set)
            log.debug('removed set pk=%d' % set_pk)
            return True


def checkExposure(mangadb_exposure_pk, flag=True, force=False):
    """Checks if a given exposures meets MaNGA's quality criteria.
    If flag=True, the exposure will be assigned an exposure_status."""

    with session.begin():
        mangaExposure = session.query(
            mangaDB.Exposure).get(mangadb_exposure_pk)

    if mangaExposure is None:
        return False

    if not force:
        if mangaExposure.status.label in ['Bad', 'Override Bad']:
            return False
        elif mangaExposure.status.label == 'Override Good':
            return True

    minSNred = config['SNthresholds']['exposureRed']
    minSNblue = config['SNthresholds']['exposureBlue']
    minExpTime = config['exposure']['minExpTime']
    maxSeeing = config['exposure']['maxSeeing']

    seeing = mangaExposure.seeing
    sn2Red = np.array([mangaExposure.sn2values[0].r1_sn2,
                       mangaExposure.sn2values[0].r2_sn2])
    sn2Blue = np.array([mangaExposure.sn2values[0].b1_sn2,
                        mangaExposure.sn2values[0].b2_sn2])
    expTime = mangaExposure.platedbExposure.exposure_time

    if expTime < minExpTime or np.any(sn2Red < minSNred) or \
            np.any(sn2Blue < minSNblue) or seeing > maxSeeing:
        if flag:
            setExposure(mangadb_exposure_pk, 'Override Bad')
        return False
    else:
        if flag:
            setExposure(mangadb_exposure_pk, 'Good', override=False)

        return True


def setExposure(mangadb_exposure, status, format='pk', override=False):
    """Sets the status of a mangaDB.Exposure to Override Bad."""

    if format == 'pk':
        with session.begin():
            mangaExposure = session.query(
                mangaDB.Exposure).get(mangadb_exposure)

        if mangaExposure is None:
            raise TotoroError('no mangaDB.Exposure with pk={0}'.format(
                mangadb_exposure))

    else:
        mangaExposure = mangadb_exposure

    with session.begin():
        if override and 'Override' not in status:
            status = 'Override ' + status

        statusPK = session.query(mangaDB.ExposureStatus).filter(
            mangaDB.ExposureStatus.label == status).one().pk

        if mangaExposure.exposure_status_pk == statusPK:
            return True

        mangaExposure.exposure_status_pk = statusPK

    log.debug('mangaDB exposure pk=%d set to %s' % (mangaExposure.pk, status))

    return True


def checkSet(set_pk, verbose=True):
    """Checks if a set meets MaNGA's quality criteria. Returns one of the
    following values: 'Good', 'Excellent', 'Poor', 'Bad'."""

    from ..dbclasses.set import Set

    set = Set(set_pk, verbose=False)

    dec = set.exposures[0].dec
    haLimit = mlhalimit(dec)
    maxHA = np.max(set.getHARange())
    if np.abs(maxHA) > np.abs(haLimit):
        if verbose:
            log.debug('set pk=%d is invalid because is ' % set.pk +
                      'outside the visibility window')
        return 'Bad'

    haRange = set.getHARange()
    if np.abs(haRange[1] - haRange[0]) > config['set']['maxHARange']:
        if verbose:
            log.debug('set pk%d is invalid because the HA range is ' % set.pk +
                      'larger than %d deg.' % config['set']['maxHARange'])
        return 'Bad'

    seeing = np.array([exp.manga_seeing for exp in set.exposures])
    if np.max(seeing) - np.min(seeing) > config['set']['maxSeeingRange']:
        if verbose:
            log.debug('set pk%d is invalid because it ' % set.pk +
                      'fails the seeing uniformity criteria')
        return 'Bad'

    sn2 = np.array([exp.getSN2Array() for exp in set.exposures])
    for ii in range(len(sn2)):
        for jj in range(ii, len(sn2)):
            sn2Ratio = sn2[ii] / sn2[jj]
            if np.any(sn2Ratio > config['set']['maxSNFactor']) or \
                    np.any(sn2Ratio < (1. / config['set']['maxSNFactor'])):
                if verbose:
                    log.debug('set pk%d is invalid because ' % set.pk +
                              'it fails the SN2 uniformity criteria')
                return 'Bad'

    ditherPositions = ['S', 'N', 'E']
    setDitherPositions = set.getDitherPositions()

    if len(setDitherPositions) < len(ditherPositions):
        if verbose:
            log.debug('set pk=%d is incomplete.' % set.pk)
        return 'Incomplete'

    for pos in ditherPositions:
        if pos not in setDitherPositions:
            if verbose:
                log.debug('set pk=%d is invalid because ' % set.pk +
                          'does not have a dither in position %s' % pos)
            return 'Bad'

    if np.mean(seeing) > config['set']['poorSeeing']:
        return 'Poor'
    elif np.mean(seeing) <= config['set']['excellentSeeing']:
        return 'Excellent'
    else:
        return 'Good'
