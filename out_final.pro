PRO OUT_FINAL, time, par, apg, man, ebo

; ---- Print time-sharing results to screen
print, " ", "TOT", "OBS", "WEA", format='(A5, 3A7)'
print, "APG:", time.totapg, time.obsapg, time.weaapg, time.weaapg / (time.weaapg + time.obsapg) * 100, format='(A5, 3F7.1, I3)'
print, "MAN:", time.totman, time.obsman, time.weaman, time.weaman / (time.weaman + time.obsman) * 100, format='(A5, 3F7.1, I3)'
print, "EBO:", time.totebo, time.obsebo, time.weaebo, time.weaebo / (time.weaebo + time.obsebo) * 100, format='(A5, 3F7.1, I3)'
print, "-------------------------------------"
print, "Total Time: ", time.obs

; ---- Print out final APOGEE-II status
openw, lun, "output/apogee.txt", /get_lun
for i=0, n_elements(apg)-1 do begin
	if apg[i].name eq '' then continue
	; Determine what year this plate is drilled in
	if apg[i].drillmjd le 57202 then drillyear = "Y1" $
	else if apg[i].drillmjd le 57574 then drillyear = "Y2" $
	else if apg[i].drillmjd le 57945 then drillyear = "Y3" $
	else if apg[i].drillmjd le 58301 then drillyear = "Y4" $
	else if apg[i].drillmjd le 58672 then drillyear = "Y5" $
	else if apg[i].drillmjd le 59031 then drillyear = "Y6" $
	else drillyear = "Y?"
	; Print out relevant summary data
	printf, lun, apg[i].name, apg[i].ra, apg[i].dec, apg[i].plateid, drillyear, apg[i].apgver, apg[i].ha, apg[i].manpriority, apg[i].vplan, apg[i].vdone, sqrt(apg[i].sn), apg[i].minha, apg[i].maxha, apg[i].priority, apg[i].hist, format='(A-12, 2F14.5, I8, A4, I8, F8.1, 3I8, 3F8.1, F12.1, 5X, A)'
endfor
free_lun, lun



END