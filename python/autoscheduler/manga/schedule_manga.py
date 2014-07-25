from __future__ import print_function, division
from autoscheduler.manga.Totoro.scheduler import Nightly

def schedule_manga(schedule, errors, plan=False, loud=True):
	# Get raw output from MaNGA submodule
	manga_obj = Nightly(startDate=schedule['man_start'], endDate=schedule['man_end'])
	manga_output = manga_obj.getOutput()
	