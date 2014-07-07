from Totoro import Session, plateDB

session = Session()

with session.begin():
            survey = session.query(plateDB.Survey).join(
                plateDB.PlateToSurvey).join(plateDB.Plate).filter(
                    plateDB.Plate.pk == 11049, plateDB.Survey.label=='MaNGA').count()

print(survey)

from Totoro.utils import isPlateComplete

print(isPlateComplete(7495, format='id'))
