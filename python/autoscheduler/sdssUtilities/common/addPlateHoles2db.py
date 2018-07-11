# Demitri Muna, NYU, 2009.04
# Re-mixed by Adam Burton, UVA 2011.04
__author__ = 'Neville Shane <nss5b@virginia.edu>'

'''
This routine takes the information from the plateholes output files and populates the database.
Based on the original script plateHoles2db.py

INPUTS: plateruns - a python list of one or more plateruns to process
        plateId - if only one plate is to be processed, this is the id of that plate.
        overwrite - True to overwrite database entries if plateholes file already exists in DB
                    False to skip
        session - database session. If none, then this function will create one. If a session is
            specified, it is the calling function's responsibility to rollback and dispose
            in the event of an exception.
        verbose - provide verbose output.

USAGE:  Specify one or more platerun to process as arguments, e.g.
        from sdss.apogee import addPlateHoles2db
    result = addPlateHoles2db.run(plateruns,plateId,overwrite)

    Examples:
    To populate with platerun 2013.04.a.apogee:
    result=addPlateHoles2db.run(['2013.04.a.apogee'])

    To populate with plateruns 2013.04.a.apogee and 2013.04.b.apogee:
    result==addPlateHoles2db.run(['2013.04.a.apogee','2013.04.b.apogee'])

    To just populate with plate 6104
    result=addPlateHoles2db.run(plateId=6104)

    To automatically overwrite any plateholes that already exist in the DB
    result=addPlateHoles2db.run(['2013.04.a.apogee'],overwrite)


Script prerequisites:
---------------------
setup sdss_python_module
setup platelist

NOTE: The "_dbo" suffix indicates that the variable holds a database object (dbo).
       i.e., an SQLAlchemy object that represents a record from the database.
'''
# -------------------------------------------------------------------
# Import statements
# -------------------------------------------------------------------
#import pdb  # call "pdb.set_trace()" to break on that line. (http://docs.python.org/library/pdb.html#debugger-commands)
# -----------------------------------------
# The snippet below is to hide the warning:
#/usr/local/python/lib/python2.7/site-packages/sqlalchemy/engine/reflection.py:40: SAWarning: Skipped unsupported reflection of expression-based index q3c_spectrum_idx
# WARNING: SAWarning: Skipped unsupported reflection of expression-based index q3c_psc_idx [sqlalchemy.util.langhelpers]
# -----------------------------------------
import warnings
warnings.filterwarnings(action="ignore", message="Skipped unsupported reflection")
warnings.filterwarnings(action="ignore", message='Predicate of partial index')

import os
import sqlalchemy
from autoscheduler.


 autoscheduler.
 autoscheduler.sdssUtilies.yanny import yanny

# ------------------------------------------------------------------- end imports


# ===========================================================
# Define a quick function to return a string path to the individual
# plateHoles.par files. CHANGE THIS TO $PLATELIST_DIR FORMAT.
# ============================================================

def file_path_gen(PlateIdNumber):

        id="{0:06d}".format(int(PlateIdNumber))
        plateFolder =id[0:-2]+'XX'
        filePathName =  os.environ["PLATELIST_DIR"] + "/plates/"+plateFolder+ \
                        "/"+str(id)+"/plateHoles-" + \
                        str(id)+".par"

        return(filePathName)


# ===========================================================
# Define a quick function to return a string filename for the individual
# plateHoles.par files. CHANGE THIS TO $PLATELIST_DIR FORMAT.
# ============================================================

def file_name_gen(PlateIdNumber):

        id="{0:06d}".format(int(PlateIdNumber))
        fileName = "plateHoles-" + str(id)+".par"

        return(fileName)


# ============================================================
# Define method to load given plateHOLES into the datbase.
# ============================================================
def load_plateholes_into_db(platePlans,overwrite,session,verbose):
    from sdss.internal.database.apo.platedb.ModelClasses import Plate, PlateHolesFile, PlateHole, PlateHoleType, ObjectType
    #Loop over all plates in the platerun
    for plate in platePlans:

        #Get the path name to the plate's platehole.par and filename
        plateHolesFilePath = file_path_gen(plate["plateid"])
        plateHolesFileName = file_name_gen(plate["plateid"])

        #Print some info to the screen
        if verbose:
            print "Processing plate: ", plate["plateid"]
            print "Looking for file: ", plateHolesFileName, "Path to file : ", plateHolesFilePath


        #Open and Read the plateHoles - XXXXX.par file
        if not os.path.exists(plateHolesFilePath):
            print("could not locate plate holes file for plate %i, with path %s"%(plate["plateid"], plateHolesFilePath))
            raise RuntimeError("could not locate plate holes file for plate %i, with path %s"%(plate["plateid"], plateHolesFilePath))
        plateHolesYanny = yanny(plateHolesFilePath)
        plateHoles = plateHolesYanny.list_of_dicts('STRUCT1') #Returns array of dict objects

        #Query for the Plate in the Plate table based on the plateid
        try:
            plate_dbo = session.query(Plate).filter_by(plate_id=plate["plateid"]).one()
        except sqlalchemy.orm.exc.NoResultFound:
            if verbose:
                print "Could not find plate id: ", plate["plateid"], "in the database. Has the plate been added?"
            #Continue on to next Plate rather than processing this one
            continue


        #Populate the plate_holes_file table.
        try:
            phf_dbo = session.query(PlateHolesFile).filter_by(filename=plateHolesFileName).one()

            if not overwrite:
                if verbose:
                    print "%s file already loaded into database, skipping (use '--overwrite' to replace)." \
                        % plateHolesFileName
                continue

        except sqlalchemy.orm.exc.NoResultFound:
            if verbose:
                print "Adding plate holes file: ", plateHolesFileName, "to plate holes table"
            phf_dbo = PlateHolesFile(filename=plateHolesFileName)
            session.add(phf_dbo)
            phf_dbo.plate = plate_dbo


        #first remove any existing plateholes associated with the plate_holes_file
        n_existing_holes = len(phf_dbo.plateHole)
        if n_existing_holes > 0:
            try:
                if verbose:
                    print "Removing existing PlateHole entries from table"
                session.query(PlateHole).filter_by(plate_holes_file_pk=phf_dbo.pk).delete()
            except:
                raise RuntimeError("Failed to remove existing PlateHole entries from table")



        #Loop over all PlateHoles on each plate
        #with a counter, platehole_num, to keep track of the # of holes processed
        platehole_num = 0

        for platehole in plateHoles:
            platehole_num+=1
            if verbose:
                print "Processing plate hole number: ", platehole_num
            #Populate the plate_hole table from par file
            ph_dbo = PlateHole()
            session.add(ph_dbo)
            ph_dbo.plateHolesFile       =   phf_dbo
            ph_dbo.xfocal               =   platehole["xfocal"]
            ph_dbo.yfocal               =   platehole["yfocal"]
            ph_dbo.tmass_h              =   platehole["tmass_h"]
            ph_dbo.tmass_j              =   platehole["tmass_j"]
            ph_dbo.tmass_k              =   platehole["tmass_k"]
            ph_dbo.pointing_number      =   platehole["pointing"]
            ph_dbo.apogee_target1       =   platehole["apogee2_target1"] if "apogee2_target1" in platehole else None
            ph_dbo.apogee_target2       =   platehole["apogee2_target2"] if "apogee2_target2" in platehole else None

            #Populate the rest of the plate_hole table from queries.
            try:
                pht_dbo = session.query(PlateHoleType).filter_by(label=platehole["holetype"]).one()
                ph_dbo.plateHoleType = pht_dbo
                if verbose:
                    print "Hole Type PK: ", pht_dbo.label
            except sqlalchemy.orm.exc.NoResultFound:
                raise RuntimeError("Plate Hole Type: %s does not appear in Hole Type Table." \
                     "Add it to the Plate Hole Type table manually and load this plate again...exiting." \
                     % platehole["holetype"])



            try:
                ot_dbo = session.query(ObjectType).filter_by(label=platehole["targettype"]).one()
                ph_dbo.objectType = ot_dbo
                if verbose:
                    print "Object Type PK: ", ot_dbo.label
            except sqlalchemy.orm.exc.NoResultFound:
                raise RuntimeError("Object Type: %s does not appear in Object Type Table." \
                    "Add it to the Object Type table manually and load this plate again...exiting" \
                    % platehole["targettype"])

        if verbose:
            print "END OF PLATE"

        #commit to database
        # try:
        #     if verbose:
        #         print "Commiting..."
        #     session.commit()
        #     #session.rollback()
        #     session.begin()
        # except:
        #     if verbose:
        #         print "Rolling Back..."
        #     session.rollback()
        #     session.begin()

            #End Loop over Holes
        if verbose:
            print "Plate ID :", plate["plateid"], "Finished"

    #End Loop Over Plates


def run(plateruns=[],plateId=None,overwrite=False,session=None,verbose=False):

    using_local_session = False
    if session is None:
        # create our own db connection
        try:
            from sdss.internal.database.connections.APODatabaseAdminLocalConnection import db
            #from sdss.internal.database.connections.APODatabaseDevAdminLocalConnection import db #dev database for testing
        except ImportError as e:
            raise RuntimeError('Error on import - did you "setup sdss_python_module" before running this script??\n')
        using_local_session = True
        # Make a unique database session (i.e. transaction).
        session = db.Session()


    for iplaterun in plateruns:
        if "apogee" not in iplaterun.lower():
            db.engine.dispose()
            raise RuntimeError("A non-apogee platerun was found in the list of plateruns." \
                "Only specify Apogee plateruns for this program.")


    # ---------------------------
    # Read "platePlans.par" file.
    # ---------------------------

    if ((os.environ).has_key("PLATELIST_DIR") == False):
        raise RuntimeError('$PLATELIST_DIR has not been defined. Try running "setup platelist" and try again.')
    else:
        platePlansFile = os.environ["PLATELIST_DIR"] + "/platePlans.par"

    # Read plateplans from file.
    platePlansYanny = yanny(platePlansFile)
    platePlans = platePlansYanny.list_of_dicts('PLATEPLANS') # returns an array of dictionary objects

    # Filter out platePlans that are not among the plateruns specified (if specified).
    if len(plateruns) > 0:
        platePlans = [x for x in platePlans if x["platerun"] in plateruns] # how cool is this?

    # Are we to process just one plate?
    if plateId:
        platePlans = [x for x in platePlans if int(x["plateid"]) == int(plateId)]


       #platePlans is now a list of dictionaries corresponding to the plateplan.par file
       #platePlans: if you say for plate in platePlans, then plate["plateid"] is the ID
       #of each plate that will be loaded into the plateholes table...


    if len(platePlans) == 0:
        raise RuntimeError("No plates were found for that platerun.")

    with session.begin():

        try:
            load_plateholes_into_db(platePlans,overwrite,session,verbose) # the actual work
        except RuntimeError as e:
            raise RuntimeError("ERROR: Failed in call to load_plateholes_into_db for platePlans %s\n"%(platePlans,) + str(e))

        if verbose:
            print "END OF PROGRAM"

        if using_local_session:
            print "USING LOCAL SESSION!!!!!!!!!!!"
            session.commit()
            #session.rollback() #for debugging
            session.close()

            db.engine.dispose() # cleanly disconnect from the database









