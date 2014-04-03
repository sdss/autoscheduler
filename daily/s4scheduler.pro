PRO S4SCHEDULER, testing=testing
starttime = systime(/seconds)

; Clear nightly schedule output file
	openw, timelun, "output/nightly.txt", /get_lun
	printf, timelun, "      JD          				APOGEE                  			MaNGA                   			eBOSS"
	free_lun, timelun

; Read in parameters from command line
schedulefilename = (command_line_args())[0]

; Specify needed parameters
set_params, params

; Generate Schedule (if necessary), or read in the pre-formatted file
gen_sched, schedulestruct, schedulefilename, output=1

; Create structures to store used time
timestruct = {totapg:0.0, totman:0.0, totboss:0.0, toteng:0.0, obsapg:0.0, obsman:0.0, obsboss:0.0, apglst:ptr_new(dblarr(24)), manlst:ptr_new(dblarr(24)), bosslst:ptr_new(dblarr(24))}
carts = dblarr(6,17)

; Now loop through days and compute usable LSTs
print, "" & print, ""
print, "==== SCHEDULING BLOCKS ===="
schedtenth = fix(n_elements(schedulestruct)/10.0)
for i=0, n_elements(schedulestruct)-1 do begin
	if i mod schedtenth eq 0 then print, "   " + strtrim(string(i/schedtenth*10.0,format='(I3)'),2) + "% Complete..."
	
	; Generate structure responsible for handling observation data
	obsstruct = {apgtimes:ptr_new([0]), apglengths:ptr_new([0]), mantimes:ptr_new([0]), manlengths:ptr_new([0]), bostimes:ptr_new([0]), boslengths:ptr_new([0])}
	
	; Observe APOGEE-2 if scheduled tonight (AND goes at beginning of night)
	if schedulestruct[i].brtstrt gt 1 and schedulestruct[i].brtstrt lt schedulestruct[i].drkstrt then begin
		timestruct.totapg += (schedulestruct[i].brtend - schedulestruct[i].brtstrt) * 24.0
		plan_apogee, timestruct, schedulestruct[i], params, obsstruct
	endif
	
	; Observe Dark Time Surveys if scheduled tonight
	if schedulestruct[i].eboss gt 0 or schedulestruct[i].manga gt 0 then begin
		
		; Figure out time split tonight
		if schedulestruct[i].manga eq 0 then begin					; eBOSS Only Night
			schedulestruct[i].bosstrt = schedulestruct[i].drkstrt
			schedulestruct[i].bosend = schedulestruct[i].drkend
		endif else if schedulestruct[i].eboss eq 0 then begin		; MaNGA Only Night
			schedulestruct[i].manstrt = schedulestruct[i].drkstrt
			schedulestruct[i].manend = schedulestruct[i].drkend
		endif else begin											; Split Dark Time
			dlength = (schedulestruct[i].drkend - schedulestruct[i].drkstrt)
			if schedulestruct[i].ebosspos eq 2 then begin				; MaNGA goes first
				schedulestruct[i].manstrt = schedulestruct[i].drkstrt
				schedulestruct[i].manend = schedulestruct[i].drkstrt + schedulestruct[i].mangapct * dlength
				schedulestruct[i].bosstrt = schedulestruct[i].drkstrt + schedulestruct[i].mangapct * dlength
				schedulestruct[i].bosend = schedulestruct[i].drkend
			endif else begin										; eBOSS goes first
				schedulestruct[i].bosstrt = schedulestruct[i].drkstrt
				schedulestruct[i].bosend = schedulestruct[i].drkend - schedulestruct[i].mangapct * dlength
				schedulestruct[i].manstrt = schedulestruct[i].drkend - schedulestruct[i].mangapct * dlength
				schedulestruct[i].manend = schedulestruct[i].drkend
			endelse
		endelse
		
		; Compute amount of time used by each dark survey tonight
			timestruct.totman += (schedulestruct[i].manend - schedulestruct[i].manstrt) * 24.0
			timestruct.totboss += (schedulestruct[i].bosend - schedulestruct[i].bosstrt) * 24.0
		
		; Observe MaNGA if scheduled tonight
		if schedulestruct[i].manstrt gt 0 then plan_manga, timestruct, schedulestruct[i], params, obsstruct
		
		; Observe eBOSS if scheduled tonight
		if schedulestruct[i].bosstrt gt 0 then plan_eboss, timestruct, schedulestruct[i], params, obsstruct
	endif   ; ----- End Planning Dark Time
	
	; Observe APOGEE-2 if scheduled tonight (AND goes at end of night)
	if schedulestruct[i].brtstrt gt 1 and schedulestruct[i].brtstrt gt schedulestruct[i].drkstrt then begin
		timestruct.totapg += (schedulestruct[i].brtend - schedulestruct[i].brtstrt) * 24.0
		plan_apogee, timestruct, schedulestruct[i], params, obsstruct
	endif
	
	; Account for Engineering Time
	if schedulestruct[i].eboss eq 0 and schedulestruct[i].manga eq 0 and schedulestruct[i].drkstrt gt 0 then begin
		elength = (schedulestruct[i].drkend - schedulestruct[i].drkstrt) * 24.0
		timestruct.toteng += elength
	endif
	
	; ==== Print Out Legible Schedule ====
	output_nightly, schedulestruct[i], obsstruct, params, carts
endfor

; ==== Print Out Final Totals ====
output_final, timestruct, params, carts


endtime = systime(/seconds)
print, "SCHEDULER COMPLETE: " + string((double(endtime) - double(starttime))/60.0, format='(F5.1)') + " minutes."

END 