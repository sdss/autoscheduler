; ---- APOGEE-II Simulating Module
PRO S4AS, lst=lst
; Begin timing
asbegintime = systime(/seconds)
timeseed = asbegintime
weather = [-1, 0, 0]

; Read in parameters from command line (if any)
for i=0, n_elements(command_line_args())-1 do begin
	if strpos((command_line_args())[i], 'lst') ge 0 then lst=1
endfor

; Read in scheduler parameters from file
set_params, par

; Read in schedule
spawn, "cat "+par.schedulefile+".frm.dat", timelines
schedule = replicate({jd:0.0D, eboss:0, manga:0, mangapct: 0.0, brtstrt:0.0D, brtend:0.0D, drkstrt:0.0D, drkend:0.0D, bosstrt:0.0D, bosend:0.0D, manstrt:0.0D, manend:0.0D, ebosspos:0}, n_elements(timelines))
for i=0, n_elements(timelines)-1 do begin
	tmp = strsplit(timelines[i],/extract)
	for j=0, n_elements(tmp)-1 do schedule[i].(j) = double(tmp[j])
endfor

; Create necessary tracking structs
; Store time-tracking information
time = {tot:0.0, totapg:0.0, totman:0.0, totebo:0.0, toteng:0.0, $			; total hours assigned
		obs:0.0, obsapg:0.0, obsman:0.0, obsebo:0.0, $						; usable on-sky time
		wea:0.0, weaapg:0.0, weaman:0.0, weaebo:0.0, $						; time lost to bad weather
		lstapg:ptr_new(dblarr(24)), lstman:ptr_new(dblarr(24)), lstebo:ptr_new(dblarr(24)), $		; usable on-sky time per LST
		unuapg:ptr_new(dblarr(24)), unuman:ptr_new(dblarr(24)), unuebo:ptr_new(dblarr(24))}			; unused time per LST

; Read in plate data (either from file or PlateDB)
get_platedata, apg, man, ebo, par

; Determine beginning and ending run days
if par.sim eq 1 then begin
	startdate = 0
	enddate = n_elements(schedule)-1
endif else begin
	currjd = round(systime(/JULIAN),/L64)
	wtoday = where(currjd eq schedule.jd, ntoday)
	if ntoday eq 0 then begin
		print, "!!! ERROR: MJD"+string(currjd-2400000, format='(I5)')+" DOES NOT EXIST IN SCHEDULE FILE"
		EXIT
	endif
	startdate = wtoday[0]
	enddate = wtoday[0]
endelse

; If we are simulating, we need to initialize several output files
if par.sim eq 1 then begin
	openw, nite, "output/APGnightly.txt", /get_lun
	free_lun, nite
endif

; Begin loop through days
for d=startdate, enddate do begin
	; Print progress, if we are simulating
	if par.sim eq 1 then print, "Scheduling MJD "+string(schedule[d].jd-2400000,format='(I5)') + "... " + string(double(d)/double(enddate-startdate)*100.0,format='(F5.1)') + "% Complete"
	
	; Determine weather for tonight
	if par.sim eq 1 then gen_weather, timeseed, schedule[d], weather, time
	
	; Generate stucture to hold observational data for tonight
	obs = {apgtim:ptr_new([0]), apglen:ptr_new([0]), apgplt:ptr_new([-1]), apgcrt:ptr_new([-1]), $
			mantim:ptr_new([0]), manlen:ptr_new([0]), manplt:ptr_new([-1]), mancrt:ptr_new([-1]), $
			ebotim:ptr_new([0]), ebolen:ptr_new([0]), eboplt:ptr_new([-1]), ebocrt:ptr_new([-1]) }
			
	; Plan APOGEE-II if it goes first tonight
	if schedule[d].brtstrt lt schedule[d].drkstrt then apogee, apg, schedule[d], time, obs, weather, par, timeseed, lst=lst
	; Plan MaNGA if it exists tonight
	;manga, man, schedule[d], time, obs, weather, par, lst=lst
	; Plan eBOSS if it exists tonight
	;eboss, ebo, schedule[d], time, obs, weather, par, timeseed, lst=lst
	; Plan APOGEE-II if it does last tonight
	if schedule[d].brtstrt gt schedule[d].drkstrt then apogee, apg, schedule[d], time, obs, weather, par, timeseed, lst=lst
	; Account for Engineering Time
	if schedule[d].eboss eq 0 and schedule[d].manga eq 0 and schedule[d].drkstrt gt 0 then time.toteng += (schedule[i].drkend - schedule[i].drkstrt) * 24.0
	
	; See if we need to print out intermittent summaries in the simulation
	if par.sim eq 1 then out_sim, time, schedule[d]
endfor

; Print out final results
out_final, time, par, apg, man, ebo

; Print out completion time
asendtime = systime(/seconds)
print, "Scheduler Complete: "+string((asendtime - asbegintime)/60.0, format='(F5.1)')+" minutes."


END