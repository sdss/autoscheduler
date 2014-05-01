import datetime

# READ_SCHEDULE
# DESCRIPTION: reads in scheduler formatted nightly schedule
# INPUT: filename -- name of the base schedule file supplied by survey coordinator
# OUTPUT: schedule -- list of dicts that contain the relevant survey times for each night.
def read_schedule(filename, mjd=-1, surveys=['apogee','eboss','manga']):
	# Read in formatted file
	schf = open(filename, 'r')
	schlines = schf.read().splitlines()
	schf.close()
	# Assign values to schedule dict list
	schedule = []
	for i in range(len(schlines)):
		tmp = schlines[i].split()
		# Assign already-computed values to dict
		schedule.append({'jd': float(tmp[0]), 'eboss': int(tmp[1]), 'manga': int(tmp[2]), 'bright_start': float(tmp[4]), 
						 'bright_end': float(tmp[5]), 'dark_start': float(tmp[6]), 'dark_end': float(tmp[7]), 
						 'eboss_start': float(tmp[8]),'eboss_end': float(tmp[9]), 'manga_start': float(tmp[10]), 'manga_end': float(tmp[11])})
	# Determine what line in the schedule to use for tonight
	if mjd < 0: tonight = round(get_juldate())
	else: tonight = 2400000 + mjd
	print ("[PY] Scheduling MJD %5d" % (tonight - 2400000))
	
	# Find line to use in the schedule file
	currjd = [x for x in range(len(schedule)) if schedule[x]['jd'] == tonight]
	if not len(currjd) > 0:
		raise AssertionError, "MJD %5d does not exist in schedule file." % (tonight-2400000)
		
	# See if schedule needs to be adjusted based on what surveys are being run tonight
	# TO-DO
	
	return schedule[currjd[0]]
	
	
def get_juldate():
	dt = datetime.datetime.utcnow()
	L = int((dt.month-14.0)/12.0)
	julian = dt.day - 32075 + int(1461*(dt.year+4800l+L)/4.0) + int(367*(dt.month - 2-L*12)/12.0) - int(int(3*((dt.year+4900l+L)/100.0))/4.0)
	julian += ((dt.hour/24.0) + (dt.minute/(24.0*60.0)) + (dt.second/86400.) + (dt.microsecond/(86400.*1e6)) - 0.5)	
	return julian
