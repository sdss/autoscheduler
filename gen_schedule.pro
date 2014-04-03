PRO GEN_SCHEDULE, schedule, filename

; Read in schedule and compute necessary switching times
if ~file_test(filename+".frm.dat") then begin
	print, "==== GENERATING SCHEDULE ===="
	spawn, "cat "+filename, timelines
	schedule = replicate({jd:0.0D, eboss:0, manga:0, mangapct: 0.0, brtstrt:0.0D, brtend:0.0D, drkstrt:0.0D, drkend:0.0D, bosstrt:0.0D, bosend:0.0D, manstrt:0.0D, manend:0.0D, ebosspos:0}, n_elements(timelines))
	timetenth = fix(n_elements(timelines)/10.0)
	for i=0L, n_elements(timelines)-1 do begin
		if i mod timetenth eq 0 then print, "   " + strtrim(string(i/timetenth*10.0,format='(I3)'),2) + "% Complete..."
		tmp = strsplit(timelines[i],' :',/extract)
		schedule[i].jd = double(tmp[0]) + 2400000.0
	
		; Figure out twilight times for this day
		res_element = 1.D / (24.D * 60.D) & npoints = LONG(1.0 / res_element) + 1
		minutes = dindgen(npoints) * res_element + 0.291666666 + schedule[i].jd
		SUNPOS, minutes, ra_sun, dec_sun
		EQ2HOR, ra_sun, dec_sun, minutes, alt_sun, az_sun, OBSNAME='apo'
		
		; Figure out twilight for tonight
		bright_twilight_start = -8.0
		if schedule[i].jd le 2456948 then begin bright_twilight_end = -8.0 ; Summer 2014                                                                                                
		endif else if schedule[i].jd gt 2456948 and schedule[i].jd le 2457102 then begin bright_twilight_end = -12.0 ; winter 2014-15                                                           
		endif else if schedule[i].jd gt 2457102 and schedule[i].jd le 2457302 then begin bright_twilight_end = -8.0 ; summer 2015                                                               
		endif else if schedule[i].jd gt 2457302 and schedule[i].jd le 2457481 then begin bright_twilight_end = -12.0 ; winter 2015-16                                                           
		endif else if schedule[i].jd gt 2457481 and schedule[i].jd le 2457657 then begin bright_twilight_end = -8.0 ; summer 2016                                                               
		endif else if schedule[i].jd gt 2457657 and schedule[i].jd le 2457834 then begin bright_twilight_end = -12.0 ; winter 2016-17                                                           
		endif else if schedule[i].jd gt 2457834 and schedule[i].jd le 2458017 then begin bright_twilight_end = -8.0 ; summer 2017                                                               
		endif else if schedule[i].jd gt 2458017 and schedule[i].jd le 2458198 then begin bright_twilight_end = -12.0 ; winter 2017-18                                                           
		endif else if schedule[i].jd gt 2458198 and schedule[i].jd le 2458396 then begin bright_twilight_end = -8.0 ; summer 2018                                                               
		endif else if schedule[i].jd gt 2458396 and schedule[i].jd le 2458575 then begin bright_twilight_end = -12.0 ; winter 2018-19                                                           
		endif else if schedule[i].jd gt 2458575 and schedule[i].jd le 2458750 then begin bright_twilight_end = -8.0 ; summer 2019                                                               
		endif else if schedule[i].jd gt 2458750 and schedule[i].jd le 2458929 then begin bright_twilight_end = -12.0 ; winter 2019-20                                                           
		endif else if schedule[i].jd gt 2458929 then begin bright_twilight_end = -8.0 ; summer 2020                                                                                     
		endif
		
		where_darktime = WHERE(alt_sun lt -15, ndarktime)
		where_brighttime_start = where(alt_sun lt bright_twilight_start, nbrighttime_start)
		where_brighttime_end = where(alt_sun lt bright_twilight_end, nbrighttime_end)
	
		; Figure out switching times for today
		if fix(tmp[1]) eq 0 then begin    										; ------------------- Dark Time Full Night
			schedule[i].eboss = 1 & schedule[i].manga = 2
			schedule[i].mangapct = double(tmp[6])
			schedule[i].ebosspos = fix(tmp[5])
			schedule[i].drkstrt = minutes[where_darktime[0]]
			schedule[i].drkend = minutes[where_darktime[ndarktime-1]]
		
		endif else if fix(tmp[1]) ge 3 and fix(tmp[1]) le 5 then begin    		; ------------------- Dark Time Start Split Night
			switchtime = schedule[i].jd + (double(tmp[7]) + double(tmp[8]) / 60.0) / 24.0 + 0.5
			schedule[i].drkstrt = minutes[where_darktime[0]]
			schedule[i].drkend = switchtime & schedule[i].brtstrt = switchtime
			schedule[i].brtend = minutes[where_brighttime_end[nbrighttime_end-1]]
			if fix(tmp[1]) eq 3 then schedule[i].manga = 1
			if fix(tmp[1]) eq 4 then schedule[i].eboss = 1
			if fix(tmp[1]) eq 5 then begin
				schedule[i].manga = 2
				schedule[i].eboss = 1
				schedule[i].mangapct = double(tmp[6])
				schedule[i].ebosspos = fix(tmp[5])
			endif

		endif else if fix(tmp[1]) ge 6 and fix(tmp[1]) le 8 then begin    		; ------------------- Bright Time Start Split Night
			switchtime = schedule[i].jd + (double(tmp[7]) + double(tmp[8]) / 60.0) / 24.0 + 0.5
			schedule[i].brtstrt = minutes[where_brighttime_start[0]]
			schedule[i].brtend = switchtime & schedule[i].drkstrt = switchtime
			schedule[i].drkend = minutes[where_darktime[ndarktime-1]]
			if fix(tmp[1]) eq 7 then schedule[i].manga = 1
			if fix(tmp[1]) eq 8 then schedule[i].eboss = 1
			if fix(tmp[1]) eq 6 then begin
				schedule[i].manga = 2
				schedule[i].eboss = 1
				schedule[i].mangapct = double(tmp[6])
				schedule[i].ebosspos = fix(tmp[5])
			endif
		
		endif else if fix(tmp[1]) eq 10 then begin    							; ------------------- Bright Time Full Night
			schedule[i].brtstrt = minutes[where_brighttime_start[0]]
			schedule[i].brtend = minutes[where_brighttime_end[nbrighttime_end-1]]
		
		endif else begin    													; ------------------- Engineering Time
			schedule[i].drkstrt = minutes[where_brighttime_start[0]]
			schedule[i].drkend = minutes[where_brighttime_end[nbrighttime_end-1]]
		endelse
	endfor

	; Print out this generated schedule for future quick-use
	openw, lun, filename+".frm.dat", /get_lun
	for i=0, n_elements(schedule)-1 do begin
		printf, lun, schedule[i], format='(F10.1, 2I5, F5.2, 8F20.6, I5)'
	endfor
	free_lun, lun
	
; Schedule has already been generated. Read in that new file
endif else begin
	spawn, "cat "+filename+".frm.dat", timelines
	schedule = replicate({jd:0.0D, eboss:0, manga:0, mangapct: 0.0, brtstrt:0.0D, brtend:0.0D, drkstrt:0.0D, drkend:0.0D, bosstrt:0.0D, bosend:0.0D, manstrt:0.0D, manend:0.0D, ebosspos:0}, n_elements(timelines))
	for i=0, n_elements(timelines)-1 do begin
		tmp = strsplit(timelines[i],/extract)
		for j=0, n_elements(tmp)-1 do schedule[i].(j) = double(tmp[j])
	
		; Find dark-time survey times tonight
		if schedule[i].eboss gt 0 or schedule[i].manga gt 0 then begin
			; Figure out time split tonight
			if schedule[i].manga eq 0 then begin					; eBOSS Only Night
				schedule[i].bosstrt = schedule[i].drkstrt
				schedule[i].bosend = schedule[i].drkend
			endif else if schedule[i].eboss eq 0 then begin			; MaNGA Only Night
				schedule[i].manstrt = schedule[i].drkstrt
				schedule[i].manend = schedule[i].drkend
			endif else begin										; Split Dark Time
				dlength = (schedule[i].drkend - schedule[i].drkstrt)
				if schedule[i].ebosspos eq 2 then begin				; MaNGA goes first
					schedule[i].manstrt = schedule[i].drkstrt
					schedule[i].manend = schedule[i].drkstrt + schedule[i].mangapct * dlength
					schedule[i].bosstrt = schedule[i].drkstrt + schedule[i].mangapct * dlength
					schedule[i].bosend = schedule[i].drkend
				endif else begin									; eBOSS goes first
					schedule[i].bosstrt = schedule[i].drkstrt
					schedule[i].bosend = schedule[i].drkend - schedule[i].mangapct * dlength
					schedule[i].manstrt = schedule[i].drkend - schedule[i].mangapct * dlength
					schedule[i].manend = schedule[i].drkend
				endelse
			endelse
		endif
	endfor
endelse

END