from __future__ import print_function, division
import astropysics.obstools as obs
import numpy as np
import sys
import matplotlib.pyplot as plt
import json

weather = 0.50
south_frac = 0.75
apg_frac = 1
man_frac = 13
ebo_frac = 6

apo = obs.Site(32.789278, -105.820278)
schedule = np.loadtxt(sys.argv[1])
apg_lst, man_lst, ebo_lst = np.zeros(24), np.zeros(24), np.zeros(24)
apg_met, man_met, ebo_met = [], [], []

for d in range(schedule.shape[0]):
	# APOGEE-II LST Calculations
	apg_start, apg_end = schedule[d,4], schedule[d,5]
	if apg_start > 1:
		apg_length = int((apg_end - apg_start) * 24 * 60 / 87 + 0.4)
		midpts = apg_start + np.arange(apg_length)*(87/60/24) + 0.5/24
		apg_nightlst = [apo.localSiderialTime(x) for x in midpts]
		for l in apg_nightlst: apg_lst[int(l)] += 87/60
		if len(apg_met) == 0: apg_met.append([int(schedule[d,0]-2400000), len(apg_nightlst)])
		else: apg_met.append([int(schedule[d,0]-2400000), len(apg_nightlst) + apg_met[-1][1]])
	else:
		if len(apg_met) == 0: apg_met.append([int(schedule[d,0]-2400000), 0])
		else: apg_met.append([int(schedule[d,0]-2400000), apg_met[-1][1]])
		

	# eBOSS LST Calculations
	ebo_start, ebo_end = schedule[d,8], schedule[d,9]
	if ebo_start > 1:
		ebo_length = int((ebo_end - ebo_start) * 24 * 60 / 16.5 + 0.4)
		midpts = ebo_start + np.arange(ebo_length)*(16.5/60/24) + 8.25/60/24
		ebo_nightlst = [apo.localSiderialTime(x) for x in midpts]
		ebo_nightlen = 0.0
		for l in ebo_nightlst:
			if int(l) > 6 and int(l) <= 18:
				ebo_lst[int(l)] += 16.5/60
				ebo_nightlen += 1
			else: 
				ebo_lst[int(l)] += 16.5/60 * south_frac
				ebo_nightlen += 1 * south_frac
		if len(ebo_met) == 0: ebo_met.append([int(schedule[d,0]-2400000), int(ebo_nightlen)])
		else: ebo_met.append([int(schedule[d,0]-2400000), int(ebo_nightlen) + ebo_met[-1][1]])
	else:
		if len(ebo_met) == 0: ebo_met.append([int(schedule[d,0]-2400000), 0])
		else: ebo_met.append([int(schedule[d,0]-2400000), ebo_met[-1][1]])


	# MaNGA LST Calculations
	man_start, man_end = schedule[d,10], schedule[d,11]
	if man_start > 1:
		man_length = int((man_end - man_start) * 24 * 60 / 16.5 + 0.4)
		midpts = man_start + np.arange(man_length)*(16.5/60/24) + 8.25/60/24
		man_nightlst = [apo.localSiderialTime(x) for x in midpts]
		man_nightlen = 0.0
		for l in man_nightlst:
			if int(l) > 6 and int(l) <= 18:
				man_lst[int(l)] += 16.5/60
				man_nightlen += 1
			else: 
				man_lst[int(l)] += 16.5/60 * south_frac
				man_nightlen += 1 * south_frac
		if len(man_met) == 0: man_met.append([int(schedule[d,0]-2400000), int(man_nightlen)])
		else: man_met.append([int(schedule[d,0]-2400000), int(man_nightlen) + man_met[-1][1]])
	else:
		if len(man_met) == 0: man_met.append([int(schedule[d,0]-2400000), 0])
		else: man_met.append([int(schedule[d,0]-2400000), man_met[-1][1]])

# Make LST plot for each survey
plt.plot(np.arange(24), apg_lst, 'b-', label="APOGEE-II")
plt.plot(np.arange(24), man_lst, 'r-', label="MaNGA")
plt.plot(np.arange(24), ebo_lst, 'g-', label="eBOSS")
plt.ylabel("# of Hours")
plt.xlabel("LST")
plt.legend()
plt.savefig(sys.argv[1]+'--lst.png')

# Print out LST summary stats
of = open(sys.argv[1]+'--lst.txt', 'w')
print("%3s %6s %6s %6s                  %7s %7s" % ('LST', 'APOGEE', 'MaNGA', 'eBOSS', 'MAN Adj', 'EBO Adj'), file=of)
for l in range(24):
	if l > 6 and l <= 18:
		print("%3d %6d %6d %6d                  %7d %7d" % (l, apg_lst[l], man_lst[l], ebo_lst[l], man_lst[l], ebo_lst[l]), file=of)
	else:
		print("%3d %6d %6d %6d   %2d%% Effective: %7d %7d" % (l, apg_lst[l], man_lst[l], ebo_lst[l], south_frac*100, 
																man_lst[l] / south_frac, ebo_lst[l] / south_frac), file=of)
print('------------------------                  ---------------', file=of)
print("%3s %6d %6d %6d                  %7d %7d" % ('TOT', np.sum(apg_lst), 
										np.sum([man_lst[x] / south_frac if x < 6 or x > 18 else man_lst[x] for x in range(len(man_lst))]), 
										np.sum([ebo_lst[x] / south_frac if x < 6 or x > 18 else ebo_lst[x] for x in range(len(ebo_lst))]), 
										np.sum(man_lst), np.sum(ebo_lst)), file=of)
of.close()

# Print out metrics JSON
full_met = []
for i in range(len(apg_met)):
	apg_cnt = apg_met[i][1] * weather / apg_frac
	man_cnt = man_met[i][1] * weather / man_frac
	ebo_cnt = ebo_met[i][1] * weather / ebo_frac
	full_met.append([apg_met[i][0], int(apg_cnt), int(man_cnt), int(ebo_cnt)])
of = open(sys.argv[1]+'--metrics.json', 'w')
json.dump(full_met, of)
of.close()



