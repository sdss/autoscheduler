from __future__ import division
from sqlalchemy.sql import func
from sqlalchemy import or_
from autoscheduler.plateDBtools.database.apo.platedb.ModelClasses import *
from autoscheduler.plateDBtools.database.apo.apogeeqldb.ModelClasses import *
import sys

def completion(vplan, vdone, sn, cadence_flag):
    ''' Computes completion percentage of APOGEE-II plate '''
    # Something is wrong here...
    if vplan == 0: return 1

    try:
        # 90% of completion percentage is from number of visits
        visit_completion = 0.9 * min([1, vdone / vplan])
        # 10% of completion percentage is from S/N
        sn_completion = 0.1 * calculateSnCompletion(vplan, sn)
        return visit_completion + sn_completion
    except:
        raise RuntimeError("ERROR: unable to calculate completion for vplan: %d, vdone: %d, sn: %d\n%s" %\
            (vplan, vdone, sn, sys.exc_info()))


def calculateSnCompletion(vplan, sn):
    ''' Computes the S/N completion percentage '''
    # Something is wrong here...
    if vplan == 0: return 1

    try:
        sn_completion = min([1, sn / (3136*vplan)])
        return sn_completion
    except:
        raise RuntimeError("ERROR: unable to calculate S/N completion for vplan: %d, sn: %d\n%s" %\
        (vplan, sn, sys.exc_info()))


def getLocVerPlates(session,plateid):
    '''find plates with the same location_id+version as input plate'''
    try:
        #find version number for this plate
        version = getPlateVersion(session,plateid)
        valid_status_labels = ["Accepted", "Retired", "Bring Back"]
        #find all the APOGEE plates with the same location_id as the current plate
        #plate must have one of the above status labels
        loc_id = session.query(Plate.location_id).filter(Plate.plate_id==plateid).one()[0]
        loc_plates = session.query(Plate.plate_id).join(PlateToSurvey,Survey,PlateToPlateStatus,PlateStatus).\
                    filter(Survey.label.ilike("apogee%")).\
                    filter(PlateStatus.label.in_(valid_status_labels)).\
                    filter(Plate.location_id == loc_id).all()

        #only return plates with the same version number as original plate
        locver_plates=[]
        for pl in loc_plates:
            if getPlateVersion(session,pl) == version:
                locver_plates.append(pl)
        return locver_plates
    except:
        raise RuntimeError("ERROR: unable to find location_id and version details in database for plate: %s\n%s" %\
        (plateid, sys.exc_info()))

def getPlateVersion(session,plateid):
    '''get the version number for the input plate'''
    try:
        dvBase = session.query(DesignValue.value).\
                              join(DesignField, Design, Plate).\
                              filter(Plate.plate_id==plateid).distinct()
        short_ver = str(dvBase.filter(DesignField.label=='apogee_short_version').distinct()[0][0])
        long_ver = str(dvBase.filter(DesignField.label=='apogee_long_version').distinct()[0][0])
        med_ver = str(dvBase.filter(DesignField.label=='apogee_med_version').distinct()[0][0])
        version = short_ver+med_ver+long_ver
        return version
    except:
        raise RuntimeError("ERROR: unable to find plate version details in database for plate: %s\n%s" %\
            (plateid, sys.exc_info()))

def obshist(plateid, session):

    # Set initial variables
    sn2, vdone = 0.0, 0

    # Get global S/N and visit information

    try:
        #find all the APOGEE plates with the same location_id and version as the current plate
        locver_plates = getLocVerPlates(session,plateid)

        sndata = session.query(func.floor(Exposure.start_time/86400.0+0.3),\
                               func.sum(Quickred.snr_standard * Quickred.snr_standard),\
                               func.count(Quickred.snr_standard),\
                               func.sum(Reduction.snr * Reduction.snr),\
                               func.count(Reduction.snr)).\
                               join(ExposureFlavor, Observation, PlatePointing, Plate).\
                               outerjoin(Quickred, Reduction).\
                               filter(Plate.plate_id.in_(locver_plates)).\
                               filter(ExposureFlavor.label=='Object').\
                               filter(or_(Quickred.snr_standard >= 10.0, Reduction.snr >= 10.0)).\
                               group_by(func.floor(Exposure.start_time/86400.0+0.3)).distinct()

        if sndata.count() > 0: good_days = [x[0] for x in sndata]
        else: good_days = []

        for i in range(sndata.count()):
            # Determine which S/N to use, QL or reduction
            if sndata[i][3] != None:
                sn = float(sndata[i][3])
                sncnt = float(sndata[i][4])
            else:
                sn = float(sndata[i][1])
                sncnt = float(sndata[i][2])
            # If 2+ visits with S/N > 10, add visit to total
            if sncnt >= 2:
                vdone += 1
            # Always add S/N^2 to total
            sn2 += sn

        # Get individual exposure S/N information
        expdata = session.query(Exposure.pk,\
                                (Quickred.snr_standard * Quickred.snr_standard),\
                                (Reduction.snr * Reduction.snr),\
                                func.floor(Exposure.start_time/86400.0+0.3)).\
                                join(ExposureFlavor, Observation, PlatePointing, Plate).\
                                outerjoin(Quickred, Reduction).\
                                filter(Plate.plate_id.in_(locver_plates)).\
                                filter(ExposureFlavor.label=='Object').\
                                filter(or_(Quickred.snr_standard >= 10.0, Reduction.snr >= 10.0)).\
                                order_by(Exposure.pk).distinct()

        # Mark whether exposures are good or bad
        exposures = []
        for e in expdata:
            if int(e[3]) in good_days: this_good = True
            else: this_good = False
            exposures.append([e[0], e[1], e[2], this_good])

        # Get vplan information from the design value table
        dvdata = session.query(DesignValue.value).\
                              join(DesignField, Design, Plate).\
                              filter(Plate.plate_id==plateid).distinct()
    except:
        raise RuntimeError("ERROR: unable to find observation history in database for plate: %s\n%s" %\
            (plateid, sys.exc_info()))
        
    try:
        vplan = int(dvdata.filter(DesignField.label=='apogee_n_design_visits').first()[0])
    except:
        vplan = 0
    try:
        cadence_flag = dvdata.filter(DesignField.label=='apogee_design_type').first()[0]
    except:
        cadence_flag = ''

    return sn2, vdone, vplan, cadence_flag, exposures
  