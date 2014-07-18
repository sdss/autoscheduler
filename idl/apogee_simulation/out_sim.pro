PRO OUT_SIM, time, schedule

; Determine whether we are at the beginning of a summer shutdown
if schedule.jd eq 2457202 then name = "year1" $
else if schedule.jd eq 2457574 then name = "year2" $
else if schedule.jd eq 2457945 then name = "year3" $
else if schedule.jd eq 2458301 then name = "year4" $
else if schedule.jd eq 2458672 then name = "year5" $
else if schedule.jd eq 2459031 then name = "year6" $
else return		; this is not a summer shutdown day, we don't need an output

; Print used and unused hours per LST to file
openw, lun, "output/LST_"+name+".txt", /get_lun
printf, lun, "LST", "APG -----", "MAN -----", "EBO -----", format='(A3, 3A14)'
for i=0, 23 do printf, lun, i, (*(time.lstapg))[i], (*(time.unuapg))[i], (*(time.lstman))[i], (*(time.unuman))[i], (*(time.lstebo))[i], (*(time.unuebo))[i], format='(I3, 6F7.1)'
printf, lun, "------------------------------------"
printf, lun, "TOT", total(*(time.lstapg)), total(*(time.unuapg)), total(*(time.lstman)), total(*(time.unuman)), total(*(time.lstebo)), total(*(time.unuebo)), format='(A3, 6F7.1)'
free_lun, lun

END