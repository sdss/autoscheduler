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
from ..utils import mlhalimit, isIntervalInsideOther


session = Session()


def rearrageExposures(plate, force=False, checkExposures=True):
    """Assigns a set to each exposure for a given plate."""

    from ..dbclasses.set import Set, Exposure
    from ..dbclasses import Plate

    if isinstance(plate, Plate):
        pass
    else:
        plate = Plate.fromPlateID(
            plate, reorganiseExposures=False, sets=False)

    log.debug('Reorganising exposures for plate_id=%d' % plate.plate_id)

    with session.begin():
        exposures = session.query(plateDB.Exposure).join(
            plateDB.ExposureFlavor, plateDB.ExposureStatus,
            plateDB.Observation, plateDB.PlatePointing, plateDB.Plate).filter(
                plateDB.Plate.plate_id == plate.plate_id,
                plateDB.ExposureFlavor.label == 'Science',
                plateDB.ExposureStatus.label == 'Good').order_by(
                    plateDB.Exposure.pk)

    expsToSet = []
    for exposure in exposures:

        if len(exposure.mangadbExposure) == 0:
            warn('plateDB exposure pk=%d does not have a mangaDB counterpart' %
                 exposure.pk, TotoroUserWarning)
            continue

        if force:
            # This should remove the set_pk of all the exposures in the set
            # we are deleting.
            removeSet(exposure.mangadbExposure[0].set_pk)
            with session.begin():
                exposure.mangadbExposure[0].set_pk = None
            expsToSet.append(exposure)
        else:
            if exposure.mangadbExposure[0].set_pk is None:
                expsToSet.append(exposure)

    if force:
        sets = []
    else:
        with session.begin():
            setsDB = session.query(mangaDB.Set).join(
                mangaDB.Exposure, plateDB.Exposure, plateDB.Observation,
                plateDB.PlatePointing, plateDB.Plate).filter(
                    plateDB.Plate.plate_id == plate.plate_id,
                    mangaDB.Set.status.label.in_(['Good', 'Excellent']))

        sets = [Set(setDB.pk, verbose=False) for setDB in setsDB]

    exps = [Exposure(expDB.pk, verbose=False) for expDB in expsToSet]

    for exp in exps:

        if not exp.valid:
            log.debug(
                'not assigning mangaDB exposure pk={0} because is invalid'
                .format(exp.manga_pk))
            continue

        createNewSet = True

        for set in sets:

            if set.complete:
                continue

            set.exposures.append(exp)

            if set.getQuality() != 'Bad':
                with session.begin():
                    expDB = session.query(
                        mangaDB.Exposure).get(exp.manga_pk)
                    expDB.set_pk = set.pk
                log.debug('added manga exposure pk={0} to set pk={1}'
                          .format(exp.manga_pk, set.pk))
                createNewSet = False
                break

        # If the exposure has not been assigned to a set,
        # creates a new one.
        if createNewSet:
            with session.begin():
                newSet = mangaDB.Set()
                session.add(newSet)
                session.flush()
                expDB = session.query(mangaDB.Exposure).get(exp.manga_pk)
                expDB.set_pk = newSet.pk
            sets.append(Set(newSet.pk, verbose=False))
            log.debug('added manga exposure pk=%d to new set pk=%d' %
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


def checkExposure(inp, flag=False, format='pk'):
    """Checks if a given exposures meets MaNGA's quality criteria.
    If flag=True, the exposure will be assigned an exposure_status."""

    from ..dbclasses import Exposure, Plate

    status = True

    if isinstance(inp, Exposure):
        exposure = inp
    else:
        with session.begin():
            if format == 'pk':
                exposureDB = session.query(plateDB.Exposure).get(inp)
            elif format == 'manga_pk':
                exposureDB = session.query(plateDB.Exposure).join(
                    mangaDB.Exposure).filter(mangaDB.Exposure == inp).one()
            else:
                raise ValueError('format must be pk or manga_pk.')

        if exposureDB is None:
            raise TotoroError('the exposure could not be found.')
        else:
            exposure = Exposure(exposureDB.pk, verbose=False)

    if exposure.status == 'Override Bad':
        return False
    elif exposure.status == 'Override Good':
        return True

    if exposure.ditherPosition not in ['C', 'E', 'N', 'S']:
        log.info('mangaDB exposure pk={0} has a wrong dither position {1}'
                 .format(exposure.manga_pk, exposure.ditherPosition))
        status = False

    plate = Plate(exposure.getPlatePK(), verbose=False,
                  sets=False, pluggings=False)
    visibilityWindow = np.array([-plate.mlhalimit, plate.mlhalimit])
    HArange = exposure.getHARange()
    if not isIntervalInsideOther(HArange, visibilityWindow, onlyOne=True):
        log.debug('mangaDB exposure pk={0} HA range [{1}, {2}] is outside '
                  'the visibility window of the plate [{3}, {4}]'
                  .format(exposure.manga_pk, HArange[0], HArange[1],
                          visibilityWindow[0], visibilityWindow[1]))
        status = False

    minExpTime = config['exposure']['minExpTime']
    expTime = exposure.expTime
    if expTime < minExpTime:
        log.debug('mangaDB exposure pk={0} has an exposure time shorter than '
                  'the minimum acceptable.'.format(exposure.manga_pk))
        status = False

    maxSeeing = config['exposure']['maxSeeing']
    seeing = exposure.seeing
    if seeing > maxSeeing:
        log.debug('mangaDB exposure pk={0} has a seeing larger than '
                  'the maximum acceptable.'.format(exposure.manga_pk))
        status = False

    minSNred = config['SNthresholds']['exposureRed']
    minSNblue = config['SNthresholds']['exposureBlue']
    snArray = exposure.getSN2Array()

    if np.any(snArray[0:2] < minSNblue) or np.any(snArray[2:] < minSNred):
        log.debug('mangaDB exposure pk={0} has a SN2(s) lower than '
                  'the minimum acceptable.'.format(exposure.manga_pk))
        status = False

    if flag and status is False:
        setExposureStatus(exposure.pk, 'Override Bad')

    return status


def setExposureStatus(inp, status, format='pk'):
    """Sets the status of an exposure."""

    with session.begin():
        if format == 'pk':
            exposure = session.query(mangaDB.Exposure).join(
                plateDB.Exposure).filter(plateDB.Exposure.pk == inp.pk).one()
        elif format == 'manga_pk':
            exposure = session.query(mangaDB.Exposure).get(inp)
        else:
            raise ValueError('format must be pk or manga_pk.')

    with session.begin():
        statusPK = session.query(mangaDB.ExposureStatus.pk).filter(
            mangaDB.ExposureStatus.label == status).scalar()

        exposure.exposure_status_pk = statusPK

    log.debug('mangaDB exposure pk={0} set to {1}'.format(exposure.pk, status))

    return True


def checkSet(input, verbose=True):
    """Checks if a set meets MaNGA's quality criteria. Returns one of the
    following values: 'Good', 'Excellent', 'Poor', 'Bad'."""

    from ..dbclasses.set import Set

    if isinstance(input, Set):
        set = input
    else:
        set = Set(input, verbose=False)

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
