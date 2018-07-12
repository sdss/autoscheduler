#!/usr/bin/env python
# encoding: utf-8
"""
plPlugMapM.py

Created by José Sánchez-Gallego on 10 Jul 2015.
Licensed under a 3-clause BSD license.

Revision history:
    10 Jul 2015 J. Sánchez-Gallego
      Initial version, based on the previous incarnation of this file.

"""

from __future__ import division
from __future__ import print_function
from autoscheduler.plateDBtools.database.apo.platedb import ModelClasses as plateDB
from autoscheduler.


 autoscheduler.
 autoscheduler.sdssUtilies import yanny
from sdss_access.path import Path
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import string
import hashlib
import warnings
import os
import re
import numpy as np
from numpy.lib.recfunctions import append_fields

Session = plateDB.db.Session
ActivePluggingException = plateDB.ActivePluggingException
PluggingException = plateDB.PluggingException


class PlPlugMapMFileException(PluggingException):
    """Custom class for PlPlugMapM exceptions. Adds contact information."""
    pass


def getPlPlugMapM_pk(plateID, fscanMJD, fscanID, pointing='A'):
    """Returns the pk of a PlPlugMapM record in the DB."""

    session = Session()
    with session.begin(subtransactions=True):
        plPlugMapM = session.query(plateDB.PlPlugMapM).join(
            plateDB.Plugging, plateDB.Plate).filter(
                plateDB.PlPlugMapM.fscan_mjd == fscanMJD,
                plateDB.PlPlugMapM.fscan_id == fscanID,
                plateDB.PlPlugMapM.pointing_name == pointing,
                plateDB.Plate.plate_id == plateID).all()

    if len(plPlugMapM) == 0:
        raise PlPlugMapMFileException('no PlPlugMapM records found for '
                                      'plateID={0}, fscanMJD={1}, '
                                      'fscanID={2}, pointing={3}'
                                      .format(plateID, fscanMJD, fscanID,
                                              pointing))
    elif len(plPlugMapM) > 1:
        raise PlPlugMapMFileException('multiple records found for '
                                      'plateID={0}, fscanMJD={1}, '
                                      'fscanID={2}, pointing={3}. '
                                      'This should never happen.'
                                      .format(plateID, fscanMJD, fscanID,
                                              pointing))
    else:
        return plPlugMapM[0].pk


def getPlPlugMapM(pk):
    """Returns an SQLalchemy object with the PlPlugMapM entry for `pk`"""

    session = Session()
    with session.begin(subtransactions=True):
        plPlugMapM = session.query(plateDB.PlPlugMapM).get(pk)
        if plPlugMapM is None:
            raise RuntimeError('no plPlugMapM record found with pk={0}'
                               .format(pk))

    return plPlugMapM


def makePluggingActive(pk):
    """Convenience function to make a plugging active. Performs some checks."""

    session = Session()
    with session.begin(subtransactions=True):
        plugging = session.query(plateDB.Plugging).get(pk)
        if plugging is None:
            raise ActivePluggingException(
                'no plugging record found with pk={0}'.format(pk))

    return plugging.makeActive()


class PlPlugMapMFile(object):
    """A class representing a plPlugMapM file.

    This class generates an object from a plPlugMapM scan file and provides
    methods to load it to the database. An instance can also be created from
    the blob in a plPlugMapM DB entry.

    Parameters
    ----------
    fscan : string or ``Yanny`` object
        The path to the plPlugMapM scan to load or a ``Yanny`` object with
        such a scan.

    Keyword arguments
    -----------------
    verbose : boolean, optional
        Sets the verbosity mode.

    """

    def __init__(self, fscan, verbose=False):

        assert isinstance(verbose, bool)
        self.verbose = verbose

        if isinstance(fscan, str):
            self.data = yanny.yanny(fscan, np=True)
            self.filename = os.path.basename(fscan)
            self.dirname = os.path.dirname(fscan)
        elif isinstance(fscan, yanny.yanny):
            self.data = fscan
            self.filename = os.path.basename(fscan.filename)
            self.dirname = os.path.dirname(fscan.filename)
        else:
            raise TypeError('fscan of type {0} must be a string or a '
                            'yanny object'.format(type(fscan)))

        self._initGuideNums()
        self._initGuide()

    @classmethod
    def fromDatabase(cls, pk):
        """Returns a `PlPlugMapMFile` from the DB.

        Returns the fscan corresponging to the plPlugMapM entry with primary
        key `pk`.

        """

        plPlugMapM = getPlPlugMapM(pk)

        try:
            yy = yanny.yanny(string=str(plPlugMapM.file), np=True)
        except:
            raise PlPlugMapMFileException(
                'problem found converting blob to Yanny file '
                'for PlPlugMapM.pk={0}'.format(pk))
        plFile = PlPlugMapMFile.__new__(cls)
        plFile.__init__(yy)
        plFile.filename = plPlugMapM.filename

        return plFile

    def write(self, path):
        """Writes the PlPlugMapM contents to a file."""

        try:
            from lockfile import LockFile
            useLockFile = True
        except:
            useLockFile = False

        if useLockFile:
            # Get locked file
            lock = LockFile(path)
            if not lock.is_locked():
                # Write plugmap file
                lock.acquire()
                ff = open(path, 'w')
                ff.write(self.data._contents)
                ff.close()
                lock.release()
            else:
                raise PlPlugMapMFileException(
                    'path {0} is locked'.format(path))
        else:
            ff = open(path, 'w')
            ff.write(self.data._contents)
            ff.close()

    def updateContents(self):
        """Updates the contents of the Yanny object.

        This code is copied from the `write()` method in sdss.utilities.yanny.
        """

        contents = ''

        for key in self.data.pairs():
            contents += "{0} {1}\n".format(key, self.data[key])

        # Print out enum definitions
        if len(self.data['symbols']['enum']) > 0:
            contents += '\n' + '\n\n'.join(self.data['symbols']['enum']) + '\n'

        # Print out structure definitions
        if len(self.data['symbols']['struct']) > 0:
            contents += ('\n' + '\n\n'.join(self.data['symbols']['struct']) +
                         '\n')
        contents += '\n'

        # Print out the data tables
        for sym in self.data.tables():
            columns = self.data.columns(sym)
            for k in range(self.data.size(sym)):
                line = list()
                line.append(sym)
                for col in columns:
                    if self.data.isarray(sym, col):
                        datum = ('{' + ' '.join([self.data.protect(x)
                                 for x in self.data[sym][col][k]]) + '}')
                    else:
                        datum = self.data.protect(self.data[sym][col][k])
                    line.append(datum)
                contents += '{0}\n'.format(' '.join(line))

        self.data._contents = contents
        self.data._parse()

        return

    def _check(self):
        """Performs a series of checks in the plPlugMapM file."""

        # Checks if there are NaN in the mag column (this causes problems
        # with the guider when trying to load the cart, see ticket #2492).
        if 'mag' not in self.data['PLUGMAPOBJ'].dtype.fields.keys():
            raise PlPlugMapMFileException(
                'no mag column found in the PLUGMAPOBJ table')
        else:
            nanMask = (np.isinf(self.data['PLUGMAPOBJ']['mag']) +
                       np.isnan(self.data['PLUGMAPOBJ']['mag']))
            if np.any(nanMask):
                warnings.warn(
                    'found some NaN values in the mag column of PLUGMAPOBJ. '
                    'Replacing them with -999., but this should not happen.',
                    UserWarning)
                self.data['PLUGMAPOBJ']['mag'][nanMask] = -999.

                # Updates the contents. Otherwise when we save the file to the
                # plPlugMapM record in the DB it will print the original
                # array.
                self.updateContents()

        return True

    def load(self, active=False, replace=False, dryRun=False):
        """Loads scan to the database.

        If `active=True`, the plugging is made active after loading it. If
        `replace=True` and the plugmap is already loaded, the entry will be
        overwritten.

        If `dryRun=True`, exists after running the checks.

        """

        if self.verbose:
            print('Loading PlPlugMapMFile object into DB.')

        # Checks if the platelist_dir env variable is set. This is needed
        # by path() in self.loadFibres.
        if 'PLATELIST_DIR' not in os.environ:
            if 'apogee' in self.data['instruments'].lower():
                raise PlPlugMapMFileException(
                    '$PLATELIST_DIR is not set. This is required to load '
                    'fibres for APOGEE. Please, make sure platelist is '
                    'installed and set up.')
            else:
                warnings.warn(
                    '$PLATELIST_DIR is not set up but the instrument list '
                    'does not contain apogee, so it should be ok.',
                    UserWarning)

        # First we run some checks on the plPlugMapM file
        result = self._check()
        nanMask = (np.isinf(self.data['PLUGMAPOBJ']['mag']) +
                   np.isnan(self.data['PLUGMAPOBJ']['mag']))
        if np.any(nanMask):
            print('Failed')

        if dryRun:
            return

        if not result:
            raise PlPlugMapMFileException('some of the checks failed.')

        # Creates plugging or retrieves it if already exists
        plugging = self._createPlugging(replace=replace)

        # Now it creates a new record for the plPlugMapM
        pM = self._createPlPlugMapM(plugging, replace=replace)

        # If this is and APOGEE plate, loads the fibres
        if 'apogee' in self.data['instruments'].lower():
            self.loadFibres(pM, replace=replace)

        # Populates the plugging_to_instrument table
        self._populatePluggingToInstrument()

        # Makes the plugging active, if so indicated.
        if active:
            self.makePluggingActive()

    def _getPlateID(self, plateid=None):
        """Returns the plateid as an integer.

        Also checks if a pointing is present in the plateid and raise a warning
        if it is different from the pointing in the plPlugMapM file.

        """

        if plateid is None:
            plateid = self.data['plateId']

        try:
            plateidInt = int(plateid)
            return plateidInt
        except:
            pass

        # The plateid is not an integer, so it means it must be in the form
        # XXXXY, where XXXX is the plateid and Y is the pointing. Let's use
        # a regex to retrieve both parts and check them against the pointing
        # in the file

        try:
            plateidGroups = re.search(r"^(\d+)(.*)", plateid).groups()
        except:
            raise PlPlugMapMFileException(
                'something went wrong when trying to assess '
                'the form of the plateid \'{0}\''.format(plateid))

        try:
            plateidInt = int(plateidGroups[0])
        except:
            raise PlPlugMapMFileException(
                'cannot retrieve an integer plateid from input \'{0}\''
                .format(plateid))

        if plateidGroups[1] != self.pointing:
            warnings.warn('pointing in plateid is {0} but pointing in '
                          'plPlugMapM file is {1}. Using {1}.'
                          .format(plateidGroups[1], self.pointing),
                          UserWarning)

        return plateidInt

    def _createPlugging(self, replace=False):
        """Creates a new plugging from the information in the plPlugMapM file.

        If the plugging already exists issues a warning and returns the
        plugging, unless `replace=True`, in which case the original record
        is overwritten.

        """

        if self.verbose:
            print('Creating plugging ...')

        plateID = self._getPlateID()
        fscan_mjd = self.data['fscanMJD']
        fscan_id = self.data['fscanId']
        cartPK = self._getCartPK()

        # Checks if a plugging already exists for this combination of
        # plateid and fscan.
        plugging = self.getPlugging()

        if plugging is not None and not replace:
            warnings.warn('plugging found for this plPlugMapM. Using it.',
                          UserWarning)
            return plugging

        # Checks that the plate exists and gets its pk
        session = Session()
        with session.begin(subtransactions=True):
            platePK = session.query(plateDB.Plate.pk).filter(
                plateDB.Plate.plate_id == plateID).scalar()

        if platePK is None:
            raise PlPlugMapMFileException(
                'no plate record found for plateid={0}'.format(plateID))

        # Creates the new plugging
        with session.begin(subtransactions=True):
            # If the plugging already exists and replace=True
            if plugging is not None and replace:
                warnings.warn('overwriting plugging pk={0} because '
                              'replace=True'.format(plugging.pk), UserWarning)
            else:
                plugging = plateDB.Plugging()
                session.add(plugging)

            plugging.fscan_mjd = fscan_mjd
            plugging.fscan_id = fscan_id
            plugging.plate_pk = platePK
            plugging.cartridge_pk = cartPK
            plugging.plugging_status_pk = 0
            session.flush()

        return plugging

    def _createPlPlugMapM(self, plugging, replace=False):
        """Adds a new plPlugMapM record to the database.

        If the plPlugMapM record for this plPlugMapM file already exists,
        raises a warning and returns the current record.

        """

        if self.verbose:
            print('Creating PlPlugMapM ...')

        fscan_mjd = self.data['fscanMJD']
        fscan_id = self.data['fscanId']

        # Checks if the record already exists.
        session = Session()
        with session.begin(subtransactions=True):
            try:
                pM = session.query(plateDB.PlPlugMapM).filter(
                    plateDB.PlPlugMapM.plugging_pk == plugging.pk,
                    plateDB.PlPlugMapM.fscan_id == fscan_id,
                    plateDB.PlPlugMapM.fscan_mjd == fscan_mjd,
                    plateDB.PlPlugMapM.pointing_name == self.pointing).one()
            except MultipleResultsFound:
                raise PlPlugMapMFileException('more than one PlPlugMapM '
                                              'records found for plugging '
                                              'pk={0}'.format(plugging.pk))
            except NoResultFound:
                pM = None

        # If the plPlugMapM already exists, checks the md5 and if passes the
        # test, returns the record
        if pM is not None and replace is False:
            if pM.md5_checksum != self.getMD5():
                raise PlPlugMapMFileException(
                    'found plPlugMapM record for this file but the MD5 in the '
                    'database is {0} while the MD5 for the file is {1}'
                    .format(pM.md5_checksum, self.getMD5()))

            warnings.warn('plPlugMapM record already in the DB. Using it.',
                          UserWarning)
            return pM

        # If the plPlugMapM does not exist, creates a new one. If replace=True,
        # overwrites the value
        with session.begin(subtransactions=True):

            if pM is not None and replace:
                warnings.warn('overwriting plPlugMapM pk={0} because '
                              'replace=True'.format(pM.pk), UserWarning)
            else:
                pM = plateDB.PlPlugMapM()
                session.add(pM)

            pM.plugging_pk = plugging.pk
            pM.dirname = self.dirname
            pM.filename = self.filename
            pM.file = str(self.data)
            pM.pointing_name = self.pointing
            pM.fscan_id = fscan_id
            pM.fscan_mjd = fscan_mjd
            pM.md5_checksum = self.getMD5()
            pM.checked_in = True
            session.flush()

        return pM

    def loadFibres(self, pM, replace=False):
        """Loads fibres from the plateHoles file for this plPlugMapM."""

        if self.verbose:
            print('Populating the fiber table for APOGEE plate ... ')

        plateHolesName = Path().name('plateHoles', plateid=self._getPlateID())

        # Make sure the plateholes file exists in the plateholes table
        # It needs to be added before the fiber table can be populated
        session = Session()
        with session.begin(subtransactions=True):
            try:
                session.query(plateDB.PlateHolesFile).filter(
                    plateDB.PlateHolesFile.filename == plateHolesName).one()
            except NoResultFound:
                raise PlPlugMapMFileException(
                    'Error: The plateHoles file \'{0}\' was not found in the '
                    'database for the plPlugMapM file \'{1}\' '
                    'Consequently, the \'fiber\' table cannot be populated. '
                    '(Was the script to load the plate holes table run?)'
                    .format(plateHolesName, pM.filename))

            except MultipleResultsFound:
                # This should really never happen. If it does, fix by adding a
                # unique contraint to the filename field of 'plate_holes_file'.
                raise PlPlugMapMFileException(
                    'Error: More than one entry in the plate_holes_file table '
                    'was found for the filename: \'{0}\''.format(pM.filename))

        # The plPlugMapM records should not have any fibre associated. We check
        # it. If there are, we raise an error except if replace=True.
        if len(pM.fibers) > 0:
            if replace is False:
                raise PlPlugMapMFileException(
                    'The PlPlugMapM record for filename={0} has fibres '
                    'associated. This should not happen unless you are '
                    'overwriting the records. You can try again with '
                    'replace=True'.format(pM.filename))
            else:
                warnings.warn('removing {0} fibres for PlPlugMapM with '
                              'filename={1}'.format(len(pM.fibers),
                                                    pM.filename), UserWarning)
                with session.begin(subtransactions=True):
                    fibers = session.query(plateDB.Fiber).filter(
                        plateDB.Fiber.pl_plugmap_m_pk == pM.pk)
                    fibers.delete()
                    session.flush()

        # When data is stored in postgres database, a number like 25.9983
        # might be stored as 25.998300001 or 25.99829999 so the (rounded)
        # values queried from the DB might not match exactly the (precise)
        # values from the pl_plugmap_m files. This method searches the database
        # for the matching value within a +/- sigma window for both x-focal
        # and y-focal. If sigma is very small, much smaller than the limit of
        # how close two fibers can be together, only one match will be found.

        plugMapObjs = self.data['PLUGMAPOBJ']
        sigmaX = .00001
        sigmaY = .00001

        fibreData = []

        # Creates and array of plateHoles
        with session.begin(subtransactions=True):
            ph_dbo = session.query(plateDB.PlateHole).join(
                plateDB.PlateHolesFile).filter(
                    plateDB.PlateHolesFile.filename ==
                    plateHolesName).all()

        plateHolesList = [(int(ph_dbo[ii].pk), float(ph_dbo[ii].xfocal),
                           float(ph_dbo[ii].yfocal))
                          for ii in range(len(ph_dbo))]
        plateHolesArray = np.array(plateHolesList)

        for (holeType, fiberId, spectrographId,
             xFocal, yFocal) in zip(plugMapObjs['holeType'],
                                    plugMapObjs['fiberId'],
                                    plugMapObjs['spectrographId'],
                                    plugMapObjs['xFocal'],
                                    plugMapObjs['yFocal']):

            if (holeType == 'OBJECT' and fiberId != -1 and
                    spectrographId == 2):

                # Finds the appropriate hole
                indices = np.where(
                    (plateHolesArray[:, 1] > (xFocal - sigmaX)) &
                    (plateHolesArray[:, 1] < (xFocal + sigmaX)) &
                    (plateHolesArray[:, 2] > (yFocal - sigmaY)) &
                    (plateHolesArray[:, 2] < (yFocal + sigmaY))
                )

                if len(indices) == 0:
                    raise PlPlugMapMFileException(
                        'Error: Problem filling fiber table for PlPlugMap {0}.'
                        ' No result found for plate hole at {1}, {2} ... '
                        'exiting'.format(pM.filename, xFocal, yFocal))
                elif len(indices) > 1:
                    raise PlPlugMapMFileException(
                        'Error: Problem filling fiber table for PlPlugMap {0}.'
                        ' Multiple results found for plate hole at '
                        '{1}, {2} ... exiting'.format(pM.filename, xFocal,
                                                      yFocal))

                plateHole = plateHolesArray[indices][0]
                # We are going to use bulk insert, so for now we just add the
                # data to a list.
                fibreData.append({'fiber_id': int(fiberId),
                                  'plate_hole_pk': plateHole[0],
                                  'pl_plugmap_m_pk': pM.pk})

        # Now we insert the data
        if len(fibreData) > 0:
            plateDB.db.engine.execute(
                plateDB.Fiber.__table__.insert(), fibreData)

    def _getCartPK(self, cartNo=None):
        """Returns the pk of a certain `cartNo`."""

        if cartNo is None:
            cartNo = self.data['cartridgeId']

        session = Session()
        with session.begin(subtransactions=True):
            pk = session.query(plateDB.Cartridge.pk).filter(
                plateDB.Cartridge.number == cartNo).scalar()
            if pk is None:
                raise PlPlugMapMFileException(
                    'no cartridge found with cartridge number {0}'
                    .format(cartNo))

        return pk

    def _initGuideNums(self):
        """Creates guidenums dictionary."""

        self._guidenums = {}

        for pointingNo in range(0, int(self.data['npointings'])):
            try:
                guidenums = self.data['guidenums{0}'.format(pointingNo + 1)]
            except KeyError:
                raise PlPlugMapMFileException(
                    'Expected to find keyword \'guidenums{0}\' to look up '
                    'pointing {0} in pointing_name, but, alas, didn\'t. '
                    '[PLATEDB: plPlugMap.py]'.format(pointingNo + 1))

            try:
                self._guidenums[self.pointing_name[pointingNo]] = guidenums
            except IndexError:
                raise PlPlugMapMFileException(
                    'Unable to lookup pointing {0} in pointing_name. '
                    '[PLATEDB: plPlugMap.py]'.format(pointingNo + 1))

    def _initGuide(self):
        """Create some helper objects for working with the guide probes."""

        data = self.data['PLUGMAPOBJ']
        guide = data[data['holeType'] == 'GUIDE']
        align = data[data['holeType'] == 'ALIGNMENT']
        # platedbActor wants record-like access
        dtype = guide.dtype.descr
        guide = np.core.records.fromrecords(guide, dtype=dtype)
        align = np.core.records.fromrecords(align, dtype=dtype)
        phi = 90 - np.arctan2(align.yFocal - guide.yFocal,
                              align.xFocal - guide.xFocal) * 180 / np.pi

        # Plates at LCO are rotated 180 degrees
        observatory = self.data.get('observatory', 'APO').upper()
        if observatory == 'LCO':
            phi += 180

        # normalise to [-90, 270] for humans
        phi[phi < -90] += 360
        phi[phi > 270] -= 360
        # append to guide and add a field name
        self._guide = append_fields(guide, 'phi', phi, usemask=False, asrecarray=True)

    def getPlugging(self):
        """Returns the plugging associated with a plugmap or None if
        doesn't exist."""

        plateID = self._getPlateID()
        fscan_mjd = self.data['fscanMJD']
        fscan_id = self.data['fscanId']
        cartPK = self._getCartPK()

        session = Session()
        with session.begin(subtransactions=True):
            try:
                plugging = session.query(plateDB.Plugging).join(
                    plateDB.Plate, plateDB.Cartridge).filter(
                        plateDB.Plugging.fscan_mjd == fscan_mjd,
                        plateDB.Plugging.fscan_id == fscan_id,
                        plateDB.Plate.plate_id == plateID,
                        plateDB.Cartridge.pk == cartPK).one()
            except MultipleResultsFound:
                raise PlPlugMapMFileException('more than one PlPlugMapM '
                                              'records found for fscan_mjd={0}'
                                              ' fscan_id={1}, plate_id={2}'
                                              .format(fscan_mjd, fscan_id,
                                                      plateID))
            except NoResultFound:
                plugging = None

        return plugging

    def getPlPlugMapM(self):
        """Returns the PlPlugMapM record from the DB if it exists."""

        session = Session()
        with session.begin(subtransactions=True):
            try:
                pM = session.query(plateDB.PlPlugMapM).filter(
                    plateDB.PlPlugMapM.md5_checksum == self.getMD5()).one()
            except NoResultFound:
                return None

        # Performs some sanity checks
        if int(pM.fscan_mjd) != int(self.data['fscanMJD']):
            raise PlPlugMapMFileException(
                'found record in the DB with same MD5 as the '
                'current PlPlugMapMFile object but with '
                'different fscan_mjd ({0} != {1})'
                .format(pM.fscan_mjd, self.data['fscanMJD']))

        if int(pM.fscan_id) != int(self.data['fscanId']):
            raise PlPlugMapMFileException(
                'found record in the DB with same MD5 as the '
                'current PlPlugMapMFile object but with '
                'different fscan_id ({0} != {1})'
                .format(pM.fscan_id, self.data['fscanId']))

        return pM

    def makePluggingActive(self):
        """Makes the plugging active."""

        plugging = self.getPlugging()

        if self.verbose:
            print('Making plugging pk={0} active ...'.format(plugging.pk))

        if plugging is None:
            raise PlPlugMapMFileException(
                'no plugging record for this PlPlugMapMFile '
                'object. Have you loaded the file yet?')

        makePluggingActive(plugging.pk)

    def getMD5(self):
        """Returns the MD5 of the file."""

        return hashlib.md5(str(self.data)).hexdigest()

    def _populatePluggingToInstrument(self):
        """Adds the plugged instruments to the plugging to instrument table."""

        plugging = self.getPlugging()

        instruments = self.listPluggedInstruments()

        if self.verbose:
            print('Instruments plugged: {0}'.format(instruments))

        session = Session()

        for instrument in instruments:

            physInstrument = 'BOSS' if instrument in ['BOSS', 'MaNGA'] \
                else 'APOGEE'
            label = physInstrument + ' Spectrograph'

            with session.begin():
                instrumentPK = session.query(plateDB.Instrument.pk).filter(
                    plateDB.Instrument.label == label).one()
                row = session.query(plateDB.PluggingToInstrument).filter(
                    plateDB.PluggingToInstrument.plugging_pk == plugging.pk,
                    plateDB.PluggingToInstrument.instrument_pk == instrumentPK,
                ).all()

                if len(row) == 1:
                    continue
                elif len(row) == 0:
                    session.add(plateDB.PluggingToInstrument(
                        plugging_pk=plugging.pk, instrument_pk=instrumentPK))
                else:
                    raise PluggingException(
                        'plugging_to_instrument contains duplicate records for'
                        ' plugging_pk={0}, instrument_pk={1}'
                        .format(plugging.pk, instrumentPK))

    def listPluggedInstruments(self):
        """Returns a list with the instruments plugged.

        Adapts Conor's code from Petunia and adds a check for eBOSS fibres.
        MaNGA is returned as its own instrument although the physical
        instrument is the BOSS spectrograph.

        """

        # We assume eBOSS is not co-plugging with anybody, so if the intrument
        # is BOSS, we just return that.
        if self.data['instruments'] == 'BOSS':
            return ['BOSS']
        elif self.data['instruments'] == 'APOGEE_SOUTH':
            return ['APOGEE South']

        gotManga = gotApogee = False

        for line in str(self.data).split('\n'):

            if gotManga and gotApogee:
                break

            if line.startswith('PLUGMAPOBJ'):

                fiberid = int(line.split()[-4])

                if 'MANGA_ALIGNMENT' in line:
                    # ignore, all other manga holes should be measured
                    continue

                if not gotApogee and 'OBJECT' in line:
                    # check that a fiber id was assigned
                    # it is the -4th (from end) value
                    gotApogee = fiberid != -1
                elif not gotManga and 'MANGA' in line:
                    gotManga = fiberid != -1

        if gotApogee and gotManga:
            return ['APOGEE', 'MaNGA']
        elif gotApogee:
            return ['APOGEE']
        elif gotManga:
            return ['MaNGA']

    @property
    def guidenums(self):
        return self._guidenums[self.pointing]

    @property
    def pointing(self):
        if 'pointing' not in self.data:
            warnings.warn('no pointing found. Assuming pointing=A',
                          UserWarning)
            return 'A'
        return self.data['pointing']

    @pointing.setter
    def pointing(self, value):
        self.data['pointing'] = value

    @property
    def cartridgeId(self):
        return self.data['cartridgeId']

    @cartridgeId.setter
    def cartridgeId(self, value):
        self.data['cartridgeId'] = value

    @property
    def pointing_name(self):
        if 'pointing_name' not in self.data:
            return list(string.ascii_uppercase)
        else:
            return self.data['pointing_name'].split()

    @pointing_name.setter
    def pointing_name(self, value):
        """Modifies the list of pointing names. `value` must be a list."""
        assert isinstance(value, list)
        self.data['pointing_name'] = ' '.join(value)

    @property
    def guide(self):
        return self._guide

    # helpful properties for platedbActor
    @property
    def mjd(self):
        return self.data['fscanMJD']

    @property
    def id(self):
        return self.data['fscanId']
