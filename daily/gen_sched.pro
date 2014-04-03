PRO GEN_SCHED, schedulestruct, filename, output=output

; Read in schedule and compute necessary switching times
if ~file_test(filename+".frm.dat") then begin
	print, "==== GENERATING SCHEDULE ===="
	spawn, "cat "+filename, timelines
	schedulestruct = replicate({jd:0.0D, eboss:0, manga:0, mangapct: 0.0, brtstrt:0.0D, brtend:0.0D, drkstrt:0.0D, drkend:0.0D, bosstrt:0.0D, bosend:0.0D, manstrt:0.0D, manend:0.0D, ebosspos:0}, n_elements(timelines))
	timetenth = fix(n_elements(timelines)/10.0)
	for i=0L, n_elements(timelines)-1 do begin
		if i mod timetenth eq 0 then print, "   " + strtrim(string(i/timetenth*10.0,format='(I3)'),2) + "% Complete..."
		tmp = strsplit(timelines[i],' :',/extract)
		schedulestruct[i].jd = double(tmp[0]) + 2400000.0
	
		; Figure out twilight times for this day
		res_element = 1.D / (24.D * 60.D) & npoints = LONG(1.0 / res_element) + 1
		minutes = dindgen(npoints) * res_element + 0.291666666 + schedulestruct[i].jd
		SUNPOS, minutes, ra_sun, dec_sun
		EQ2HOR, ra_sun, dec_sun, minutes, alt_sun, az_sun, OBSNAME='apo'
		
		; Figure out twilight for tonight
		bright_twilight_start = -8.0
		if schedulestruct[i].jd le 2456948 then begin bright_twilight_end = -8.0 ; Summer 2014                                                                                                
		endif else if schedulestruct[i].jd gt 2456948 and schedulestruct[i].jd le 2457102 then begin bright_twilight_end = -12.0 ; winter 2014-15                                                           
		endif else if schedulestruct[i].jd gt 2457102 and schedulestruct[i].jd le 2457302 then begin bright_twilight_end = -8.0 ; summer 2015                                                               
		endif else if schedulestruct[i].jd gt 2457302 and schedulestruct[i].jd le 2457481 then begin bright_twilight_end = -12.0 ; winter 2015-16                                                           
		endif else if schedulestruct[i].jd gt 2457481 and schedulestruct[i].jd le 2457657 then begin bright_twilight_end = -8.0 ; summer 2016                                                               
		endif else if schedulestruct[i].jd gt 2457657 and schedulestruct[i].jd le 2457834 then begin bright_twilight_end = -12.0 ; winter 2016-17                                                           
		endif else if schedulestruct[i].jd gt 2457834 and schedulestruct[i].jd le 2458017 then begin bright_twilight_end = -8.0 ; summer 2017                                                               
		endif else if schedulestruct[i].jd gt 2458017 and schedulestruct[i].jd le 2458198 then begin bright_twilight_end = -12.0 ; winter 2017-18                                                           
		endif else if schedulestruct[i].jd gt 2458198 and schedulestruct[i].jd le 2458396 then begin bright_twilight_end = -8.0 ; summer 2018                                                               
		endif else if schedulestruct[i].jd gt 2458396 and schedulestruct[i].jd le 2458575 then begin bright_twilight_end = -12.0 ; winter 2018-19                                                           
		endif else if schedulestruct[i].jd gt 2458575 and schedulestruct[i].jd le 2458750 then begin bright_twilight_end = -8.0 ; summer 2019                                                               
		endif else if schedulestruct[i].jd gt 2458750 and schedulestruct[i].jd le 2458929 then begin bright_twilight_end = -12.0 ; winter 2019-20                                                           
		endif else if schedulestruct[i].jd gt 2458929 then begin bright_twilight_end = -8.0 ; summer 2020                                                                                     
		endif
		
		where_darktime = WHERE(alt_sun lt -15, ndarktime)
		where_brighttime_start = where(alt_sun lt bright_twilight_start, nbrighttime_start)
		where_brighttime_end = where(alt_sun lt bright_twilight_end, nbrighttime_end)
	
		; Figure out switching times for today
		if fix(tmp[1]) eq 0 then begin    										; ------------------- Dark Time Full Night
			schedulestruct[i].eboss = 1 & schedulestruct[i].manga = 2
			schedulestruct[i].mangapct = double(tmp[6])
			schedulestruct[i].ebosspos = fix(tmp[5])
			schedulestruct[i].drkstrt = minutes[where_darktime[0]]
			schedulestruct[i].drkend = minutes[where_darktime[ndarktime-1]]
		
		endif else if fix(tmp[1]) ge 3 and fix(tmp[1]) le 5 then begin    		; ------------------- Dark Time Start Split Night
			switchtime = schedulestruct[i].jd + (double(tmp[7]) + double(tmp[8]) / 60.0) / 24.0 + 0.5
			schedulestruct[i].drkstrt = minutes[where_darktime[0]]
			schedulestruct[i].drkend = switchtime & schedulestruct[i].brtstrt = switchtime
			schedulestruct[i].brtend = minutes[where_brighttime_end[nbrighttime_end-1]]
			if fix(tmp[1]) eq 3 then schedulestruct[i].manga = 1
			if fix(tmp[1]) eq 4 then schedulestruct[i].eboss = 1
			if fix(tmp[1]) eq 5 then begin
				schedulestruct[i].manga = 2
				schedulestruct[i].eboss = 1
				schedulestruct[i].mangapct = double(tmp[6])
				schedulestruct[i].ebosspos = fix(tmp[5])
			endif

		endif else if fix(tmp[1]) ge 6 and fix(tmp[1]) le 8 then begin    		; ------------------- Bright Time Start Split Night
			switchtime = schedulestruct[i].jd + (double(tmp[7]) + double(tmp[8]) / 60.0) / 24.0 + 0.5
			schedulestruct[i].brtstrt = minutes[where_brighttime_start[0]]
			schedulestruct[i].brtend = switchtime & schedulestruct[i].drkstrt = switchtime
			schedulestruct[i].drkend = minutes[where_darktime[ndarktime-1]]
			if fix(tmp[1]) eq 7 then schedulestruct[i].manga = 1
			if fix(tmp[1]) eq 8 then schedulestruct[i].eboss = 1
			if fix(tmp[1]) eq 6 then begin
				schedulestruct[i].manga = 2
				schedulestruct[i].eboss = 1
				schedulestruct[i].mangapct = double(tmp[6])
				schedulestruct[i].ebosspos = fix(tmp[5])
			endif
		
		endif else if fix(tmp[1]) eq 10 then begin    							; ------------------- Bright Time Full Night
			schedulestruct[i].brtstrt = minutes[where_brighttime_start[0]]
			schedulestruct[i].brtend = minutes[where_brighttime_end[nbrighttime_end-1]]
		
		endif else begin    													; ------------------- Engineering Time
			schedulestruct[i].drkstrt = minutes[where_brighttime_start[0]]
			schedulestruct[i].drkend = minutes[where_brighttime_end[nbrighttime_end-1]]
		endelse
	endfor

	; Print out this generated schedule for future quick-use
	if keyword_set(output) then begin
		openw, lun, filename+".frm.dat", /get_lun
		for i=0, n_elements(schedulestruct)-1 do begin
			printf, lun, schedulestruct[i], format='(F10.1, 2I5, F5.2, 8F20.6, I5)'
		endfor
		free_lun, lun
	endif
	
; Schedule has already been generated. Read in that new file
endif else begin
	spawn, "cat "+filename+".frm.dat", timelines
	schedulestruct = replicate({jd:0.0D, eboss:0, manga:0, mangapct: 0.0, brtstrt:0.0D, brtend:0.0D, drkstrt:0.0D, drkend:0.0D, bosstrt:0.0D, bosend:0.0D, manstrt:0.0D, manend:0.0D, ebosspos:0}, n_elements(timelines))
	for i=0, n_elements(timelines)-1 do begin
		tmp = strsplit(timelines[i],/extract)
		for j=0, n_elements(tmp)-1 do schedulestruct[i].(j) = double(tmp[j])
	endfor
endelse

END