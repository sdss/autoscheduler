; APOGEE
; DESCRIPTION: main IDL routine which takes input from Python autoscheduler and makes plate decisions
; INPUT: 'apogee.as' -- text file which contains all plate information
;		 schedule -- important schedule times throughout the night, passed as command line arguments
; OUTPUT: chosen -- observing slot start times for the current night, plate choices for each slot
;					and expected exposure times
PRO APOGEE, test=test

; ---- Define APOGEE-II parameters
par = {aexp: 60.0, aovh: 20.0, acart: 9, amaxz: 3.0, amoon: 54000.0, asn: 3136}
schedule = {jd:0L, manga:0, eboss:0, brtstrt:0.0D, brtend:0.0D, drkstrt:0.0D, bosstrt:0.0D, manstrt:0.0D}
for i=0, n_elements(command_line_args())-1 do schedule.(i) = double((command_line_args())[i])

; ---- Read in APOGEE-II plate information
spawn, "cat apgplates.as", plateinfo
apg = replicate({name:'', plateid:0, fieldid:0, apgver:0, ra:0.0, dec:0.0, ha:0.0, vplan:0, vdone:0, sn:0.0, manpriority:0, priority:0.0, plugged:0, minha:0.0, maxha:0.0, cadenceflag:0, stackflag:0, hist:''}, n_elements(plateinfo))
for i=0, n_elements(plateinfo)-1 do begin
	tmp = strsplit(plateinfo[i], /extract)
	if n_elements(tmp) lt 5 then continue
	apg[i].name = tmp[0]
	if n_elements(tmp) gt 17 then apg[i].hist = tmp[17]
	for j=1,16 do apg[i].(j) = double(tmp[j])
endfor
spawn, "rm apgplates.as"

; ---- Define APOGEE-II blocks for tonight
block_start = systime(1,/seconds)
nightlen = (schedule.brtend - schedule.brtstrt) * 24.0
nslots = min([fix(nightlen / ((par.aexp + par.aovh) / 60.0)), par.acart])
if nslots eq 0 then return

; Determine slot start times + exposure lengths
atimes = schedule.brtstrt + dindgen(nslots) * (par.aexp + par.aovh)/60.0/24.0
alengths = replicate((par.aexp + par.aovh) / 60.0, nslots)

; APOGEE-II starts the split night (we can adjust the end time)
if schedule.brtstrt lt schedule.drkstrt then begin
	; Determine whether we should add an exposure (leftover time > 45min)
	if nslots lt par.acart and nightlen - total(alengths) gt 0.75 then begin
		atimes = [atimes, schedule.brtstrt + double(nslots) * (par.aexp + par.aovh) / 60.0 / 24.0]
		alengths = [alengths, par.aexp / 60.0]
	endif
	; Because APOGEE is first, the last exposure will not have overhead
	alengths[n_elements(alengths)-1] = par.aexp / 60.0
	
; APOGEE-II ends the night OR APOGEE-II is the only survey tonight (end time is fixed)
endif else begin
	; Determine whether we can add an exposure (leftover time - overhead > 30min)
	if nslots lt par.acart and nightlen - total(alengths)  gt (0.5 + par.aovh/60.0) then begin
		atimes = [atimes, schedule.brtstrt + double(nslots) * (par.aexp + par.aovh) / 60.0 / 24.0]
		alengths = [alengths, nightlen - total(alengths)]
	endif
endelse
block_end = systime(1,/seconds)
print, "[IDL] APOGEE-II blocks determined (" + string((block_end-block_start)/60.0, format='(F3.1)') + " min)"

; ---- Determine LSTs for all blocks tonight
OBSERVATORY, 'apo', apo
fakera = replicate(0.0,n_elements(atimes)) & fakedec = replicate(0.0,n_elements(atimes))
eq2hor, fakera, fakedec, atimes + alengths / 24.0 / 2.0, alt, az, obsname='apo'
altaz2hadec, alt, az, apo.latitude, ha, dec

; ---- Prioritize Plates
pri_start = systime(1,/seconds)
; Base Priorities
apg.priority = 100.0 * apg.manpriority
; Already Plugged
wplugged = where(apg.plugged gt 0, nplugged)
if nplugged gt 0 then apg[wplugged].priority += 100.0
; Declination
apg.priority -= 50.0 * exp( -(apg.dec - 30.0)^2.0 / (2.0 * (20.0)^2.0))
; Ecliptic
euler, apg.ra, apg.dec, ecllon, ecllat, 3
apg.priority += 50.0 * exp( -(ecllat)^2.0 / (2.0 * (7.5)^2.0))

for i=0, n_elements(apg)-1 do begin
	; Completion
	; "Regular" completion rules: all visits and S/N
	if apg[i].stackflag eq 0 and apg[i].vdone ge apg[i].vplan and apg[i].sn ge long(par.asn) * long(apg[i].vplan) then apg[i].priority = -2 $
	; "Stack" completion rules: only S/N
	else if apg[i].stackflag eq 1 and apg[i].sn ge long(par.asn) * long(apg[i].vplan) then apg[i].priority = -2
	; Cadence
	obshist = double(strsplit(apg[i].hist, ',', /extract))
	if apg[i].cadenceflag eq 1 then begin
		; 4+ visit "regular" cadence rules
		if schedule.jd - max(obshist) lt 3 then apg[i].priority = -1
	endif else if apg[i].cadenceflag eq 2 then begin
		; 3 visit "regular" cadence rules
		if schedule.jd - max(obshist) lt 3 then apg[i].priority = -1
		if apg[i].vdone eq 2 and schedule.jd - min(obshist) lt 26 then apg[i].priority = -1
	endif else if apg[i].cadenceflag eq 5 then begin
		; Kepler KOI cadence rules
		if apg[i].vdone eq 1 and schedule.jd - min(obshist) lt 180 then apg[i].priority = -1
	endif
	; In-Order Completion
	wfield = where(apg[i].fieldid eq apg.fieldid, nfield)
	for j=0, nfield-1 do if apg[i].apgver gt apg[wfield[j]].apgver and apg[wfield[j]].priority gt 1 then apg[i].priority /= 2.0
endfor
pri_end = systime(1,/seconds)
print, "[IDL] APOGEE-II plates prioritized (" + string((pri_end-pri_start)/60.0, format='(F3.1)') + " min)"

; ---- Determine Observability
obs_start = systime(1,/seconds)
obsarr = dblarr(n_elements(apg), n_elements(atimes))
for i=0, n_elements(apg)-1 do begin
	OBSERVABILITY, apg[i], atimes, alengths - par.aovh/60.0, par.amaxz, par.amoon, obsvalues
	obsarr[i,*] = obsvalues
endfor
obs_end = systime(1,/seconds)
print, "[IDL] APOGEE-II plate observability determined (" + string((obs_end-obs_start)/60.0, format='(F3.1)') + " min)"

; ---- Pick Plates
nplt = replicate(0, n_elements(atimes))
for i=0, n_elements(atimes)-1 do begin
	wavail = where(obsarr[*,i] ge 0.05, navail)
	nplt[i] = navail
endfor
; Order picking of plates from fewest to most
pickorder = sort(nplt)

; Loop through slots and choose plates
choose_start = systime(1,/seconds)
chosen = replicate(0, n_elements(atimes))
for i=0, n_elements(pickorder)-1 do begin
	cslot = pickorder[i]
	wavail = where(obsarr[*,cslot] ge 0.05, navail)
	if navail eq 0 then begin
		; Throw a warning if we have no possible plates in a slot
		print, "[IDL] WARNING: No APG2 plates for block @ LST = "+strtrim(string(fix(ha[cslot]/15.0)),2)
		chosen[cslot] = -1
		continue
	endif
	priorder = sort(obsarr[wavail,cslot])
	chosen[cslot] = wavail[priorder[n_elements(priorder)-1]]
	; Remove the currently chosen plate from being chosen again
	if apg[chosen[cslot]].stackflag eq 0 then for s=0, n_elements(obsarr[chosen[cslot],*])-1 do obsarr[chosen[cslot],s] = -10.0 $
	; If this plate's stack flag is set, do not remove next block
	else for s=cslot+2, n_elements(obsarr[chosen[cslot],*])-1 do obsarr[chosen[cslot],s] = -10.0
endfor

; Loop through again and supply 2 backup options
backup1 = replicate(0, n_elements(atimes)) & backup2 = replicate(0, n_elements(atimes))
for i=0, n_elements(atimes)-1 do begin
	wavail = where(obsarr[*,i] ge 0.05, navail)
	; Choose first backup
	if navail ge 1 then begin
		priorder = sort(obsarr[wavail,i])
		backup1[i] = wavail[priorder[n_elements(priorder)-1]]
		obsarr[backup1[i],i] = -10.0
	endif else backup1[i] = -1
	; Choose second backup
	if navail ge 2 then begin
		priorder = sort(obsarr[wavail,i])
		backup2[i] = wavail[priorder[n_elements(priorder)-1]]
	endif else backup2[i] = -1
endfor

; Check for stacked fields
for p=0, n_elements(chosen)-1 do begin
	if chosen[p] lt 0 or p ge n_elements(chosen) then continue
	wthis = where(chosen[p] eq chosen, nthis)
	if nthis gt 1 then begin
		print, "[IDL] APG2 STACK CHOSEN"
		; Make new arrays for night times, lengths and plates
		newtime = dblarr(n_elements(atimes)-1)
		newlength = dblarr(n_elements(alengths)-1)
		newchosen = replicate(0, n_elements(chosen)-1)
		; Save all values previous to the stack
		for s=0, p do begin
			newtime[s] = atimes[s] & newlength[s] = alengths[s] & newchosen[s] = chosen[s]
		endfor
		; Add this block and the next together
		newlength[p] = alengths[p] + alengths[p+1]
		; Save all values after the stack
		for s=p+2, n_elements(atimes)-1 do begin
			newtime[s-1] = atimes[s] & newlength[s-1] = alengths[s] & newchosen[s-1] = chosen[s]
		endfor
		; Save all new arrays
		atimes = newtime & alengths = newlength & chosen = newchosen
	endif
endfor
choose_end = systime(1,/seconds)
print, "[IDL] APOGEE-II plates chosen (" + string((block_end-block_start)/60.0, format='(F3.1)') + " min)"

; Return chosen plates
for i=0, n_elements(atimes)-1 do begin
	if chosen[i] ge 0 then thisplate = apg[chosen[i]].plateid else thisplate = -1
	if backup1[i] ge 0 then thisbak1 = apg[backup1[i]].plateid else thisbak1 = -1
	if backup2[i] ge 0 then thisbak2 = apg[backup2[i]].plateid else thisbak2 = -1
	print, "[CHOSEN]", atimes[i], alengths[i], thisplate, thisbak1, thisbak2, format='(A8, 2X, 2F20.7, 3I6)'
endfor



END
