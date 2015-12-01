from __future__ import print_function, division
from time import time
import os
import math
import sdss.internal.database.apo.platedb.ModelClasses as plateDB
from sqlalchemy import or_
from sqlalchemy import desc

# EBOPLATE OBJECT DENITION
# DESCRIPTION: eBOSS Plate Object
class eboplate(object):
    # Identifying plate information
    plateid = 0
    platepk = -1
    
    # Plate pointing information
    ra = 0.0
    dec = 0.0
    ha = 0.0
    maxha = 0.0
    minha = 0.0
    
    # Scheduling info
    snr = 0.0
    snb = 0.0
    manual_priority = 0.0
    priority = 0.0
    plugged = 0
    
    # Number of visits to complete
    def visleft(self, par):
        rleft = (par['snr'] - self.snr) / par['snr_avg']
        bleft = (par['snb'] - self.snb) / par['snb_avg']
        maxleft = max([rleft, bleft])
        if maxleft <= 0: return int(0)
        return int(math.ceil(maxleft))

# GET_PLATES
# DESCRIPTION: Reads in eBOSS plate information from platedb
# INPUT: none
# OUTPUT: ebo -- list of dicts with all eBOSS plate information
def get_plates(plan=False, loud=True):
    # Create database connection
    if (os.path.dirname(os.path.realpath(__file__))).find('utah.edu') >= 0: from sdss.internal.database.connections.UtahLocalConnection import db
    else: from sdss.internal.database.connections.APODatabaseUserLocalConnection import db
    session = db.Session()

    # Look at all plates for plugging purposes
    stage1_start = time()
    if plan:
       # Pull all information on eBOSS plates
        ebossPlates = session.query(plateDB.Plate, plateDB.Pointing, plateDB.PlatePointing).join(plateDB.PlateToSurvey, plateDB.Survey, plateDB.PlatePointing, plateDB.Pointing, plateDB.PlateLocation, plateDB.PlateToPlateStatus, plateDB.PlateStatus).filter(or_(plateDB.Survey.label == 'eBOSS', plateDB.Survey.label == 'BOSS'), or_(plateDB.PlateStatus.label == 'Accepted',plateDB.PlateStatus.label == 'Special'), plateDB.PlateLocation.label == 'APO', plateDB.Plate.plate_id >= 4800).order_by(desc(plateDB.PlatePointing.priority)).all()

        # Add all incomplete plates to be analyzed
        ebo = []
        for p in ebossPlates:
            if p.Plate.calculatedCompletionStatus() == 'Complete' or p.Plate.calculatedCompletionStatus() == 'Force Complete': continue
            ebo.append(eboplate())
            ebo[-1].ra = p.Pointing.center_ra
            ebo[-1].dec = p.Pointing.center_dec
            ebo[-1].plateid = p.Plate.plate_id
            ebo[-1].ha = p.PlatePointing.hour_angle
            ebo[-1].manual_priority = p.PlatePointing.priority
            try:
                ebo[-1].maxha = p.PlatePointing.ha_observable_max
                ebo[-1].minha = p.PlatePointing.ha_observable_min
            except:
                pass
            ebo[-1].platepk = p.Plate.pk
            ebo[-1].plugged = 0
    else:
        plugged_plates = session.execute("SET SCHEMA 'platedb'; "+
            "SELECT crt.number, plt.plate_id, plt.pk "+
            "FROM ((((((platedb.active_plugging AS ac "+
                "JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
                "LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
                "LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
                "LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
                "LEFT JOIN platedb.survey AS surv ON (p2s.survey_pk = surv.pk)) "+
                "LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
            "WHERE surv.label='BOSS' OR surv.label='eBOSS' ORDER BY crt.number").fetchall() 
        ebo = []
        for i in range(len(plugged_plates)):
            ebo.append(eboplate())
            ebo[-1].plateid = int(plugged_plates[i][1])
            ebo[-1].platepk = int(plugged_plates[i][2])
    stage1_end = time()
    if loud: print("[SQL] Read in eBOSS plates (%.3f sec)" % ((stage1_end - stage1_start)))
    
    # Determine what is currently plugged
    stage3_start = time()
    stage3 = session.execute("SET SCHEMA 'platedb'; "+
        "SELECT crt.number, plt.plate_id "+
        "FROM ((((((platedb.active_plugging AS ac "+
            "JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+
            "LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+
            "LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+
            "LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+
            "LEFT JOIN platedb.survey AS surv ON (p2s.survey_pk = surv.pk)) "+
            "LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+
        "WHERE surv.label='BOSS' OR surv.label='eBOSS' ORDER BY crt.number").fetchall() 
    # Save currently plugged plates to data
    for c,p in stage3:
        wplate = [x for x in range(len(ebo)) if ebo[x].plateid == p]
        if len(wplate) == 0: continue
        wplate = wplate[0]
        ebo[wplate].plugged = c
    stage3_end = time()
    if loud: print("[SQL] Read in currently plugged eBOSS plates (%.3f sec)" % ((stage3_end - stage3_start)))
        
    return ebo
    
