PRO APOGEE, apg, schedule, time, obs, weather, par, seed, lst=lst
; Check to see whether APOGEE-II observes tonight
if schedule.brtstrt lt 1 then return

; ---- Define APOGEE-II blocks for tonight
nightlen = (schedule.brtend - schedule.brtstrt) * 24.0
nslots = min([fix(nightlen / ((par.aexp + par.aovh) / 60.0)), par.acart])
if nslots eq 0 then return

; Determine slot start times + exposure lengths
atimes = schedule.brtstrt + dindgen(nslots) * (par.aexp + par.aovh)/60.0/24.0
alengths = replicate((par.aexp + par.aovh) / 60.0, nslots)

; APOGEE-II starts the split night (we can adjust the end time)
if schedule.brtstrt lt schedule.drkstrt then begin
	; Determine whether we should add an exposure (leftover time > 30min)
	if nslots lt par.acart and nightlen - total(alengths) gt 0.5 then begin
		atimes = [atimes, schedule.brtstrt + double(nslots) * (par.aexp + par.aovh) / 60.0 / 24.0]
		alengths = [alengths, par.aexp / 60.0]
	endif
	; Because APOGEE is first, the last exposure will not have overhead
	alengths[n_elements(alengths)-1] = par.aexp / 60.0
	
	; Adjust the dark time program start time, if necessary
	if schedule.manga eq 1 and (schedule.eboss eq 0 or schedule.manstrt lt schedule.bosstrt) then schedule.manstrt = schedule.brtstrt + total(alengths)/24.0
	if schedule.eboss eq 1 and (schedule.manga eq 0 or schedule.bosstrt lt schedule.manstrt) then schedule.bosstrt = schedule.brtstrt + total(alengths)/24.0
	
; APOGEE-II ends the night OR APOGEE-II is the only survey tonight (end time is fixed)
endif else begin
	; Determine whether we can add an exposure (leftover time - overhead > 30min)
	if nslots lt par.acart and nightlen - total(alengths)  gt (0.5 + par.aovh/60.0) then begin
		atimes = [atimes, schedule.brtstrt + double(nslots) * (par.aexp + par.aovh) / 60.0 / 24.0]
		alengths = [alengths, nightlen - total(alengths)]
	endif
endelse

; ---- Save blocks to obs struct
time.totapg += total(alengths)
obs.apgtim = ptr_new(atimes)
obs.apglen = ptr_new(alengths)

; ---- Compute LSTs for tonights blocks
alst = (*(time.lstapg))
OBSERVATORY, 'apo', apo
fakera = replicate(0.0,n_elements(atimes)) & fakedec = replicate(0.0,n_elements(atimes))
eq2hor, fakera, fakedec, atimes + alengths / 24.0 / 2.0, alt, az, obsname='apo'
altaz2hadec, alt, az, apo.latitude, ha, dec
for i=0, n_elements(ha)-1 do alst[fix(ha[i]/15.0)] += alengths[i]
time.lstapg = ptr_new(alst)
if keyword_set(lst) then return			; If we only want LSTs, we return here.

; Print out night length and number of scheduled blocks
openw, nite, "output/APGblocks.txt", /get_lun, /append
printf, nite, schedule.jd-2400000, alengths
free_lun, nite

; ---- Prioritize Plates
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
	; Drilling
	if apg[i].drillmjd - (schedule.jd-2400000) gt 370 then apg[i].priority = -3
	; In-Order Completion
	wfield = where(apg[i].fieldid eq apg.fieldid, nfield)
	for j=0, nfield-1 do if apg[i].apgver gt apg[wfield[j]].apgver and apg[wfield[j]].priority gt 1 then apg[i].priority /= 2.0
endfor

; ---- Determine Observability
obsarr = dblarr(n_elements(apg), n_elements(*(obs.apgtim)))
for i=0, n_elements(apg)-1 do begin
	OBSERVABILITY, apg[i], (*(obs.apgtim)), (*(obs.apglen)) - par.aovh/60.0, par.amaxz, par.amoon, obsvalues
	obsarr[i,*] = obsvalues
endfor

; ---- Pick Plates
amiss = (*(time.unuapg))
nplt = replicate(0, n_elements(*(obs.apgtim)))
for i=0, n_elements(*(obs.apgtim))-1 do begin
	wavail = where(obsarr[*,i] ge 0.05, navail)
	nplt[i] = navail
endfor
; Order picking of plates from fewest to most
pickorder = sort(nplt)
time.unuapg = ptr_new(amiss)

; Loop through slots and choose plates
chosen = replicate(0, n_elements(*(obs.apgtim)))
for i=0, n_elements(pickorder)-1 do begin
	cslot = pickorder[i]
	wavail = where(obsarr[*,cslot] ge 0.05, navail)
	if navail eq 0 then begin
		; Throw a warning if we have no possible plates in a slot
		print, "   WARNING: No APG2 plates for block @ LST = "+strtrim(string(fix(ha[cslot]/15.0)),2)
		amiss[fix(ha[cslot]/15.0)] += alengths[cslot]
		chosen[cslot] = -1
		continue
	endif
	priorder = sort(obsarr[wavail,cslot])
	chosen[cslot] = wavail[priorder[n_elements(priorder)-1]]
	; Remove the currently chosen plate from being chosen again
	if apg[chosen[cslot]].stackflag eq 0 then for s=0, n_elements(obsarr[chosen[cslot],*])-1 do obsarr[chosen[cslot],s] = -10.0 $
	; If this plates stack flag is set, do not remove next block
	else for s=cslot+2, n_elements(obsarr[chosen[cslot],*])-1 do obsarr[chosen[cslot],s] = -10.0
endfor
time.unuapg = ptr_new(amiss)
obs.apgplt = ptr_new(chosen)
; Check for stacked fields
for p=0, n_elements(chosen)-1 do begin
	if chosen[p] lt 0 or p ge n_elements(*(obs.apgplt)) then continue
	wthis = where((*(obs.apgplt))[p] eq (*(obs.apgplt)), nthis)
	if nthis gt 1 then begin
		print, "  APG2 STACK CHOSEN"
		; Make new arrays for night times, lengths and plates
		newtime = dblarr(n_elements(*(obs.apgtim))-1) & newlength = dblarr(n_elements(*(obs.apglen))-1)
		newchosen = replicate(0, n_elements(*(obs.apgplt))-1)
		; Save all values previous to the stack
		for s=0, p do begin
			newtime[s] = (*(obs.apgtim))[s] & newlength[s] = (*(obs.apglen))[s] & newchosen[s] = (*(obs.apgplt))[s]
		endfor
		; Add this block and the next together
		newlength[p] = (*(obs.apglen))[p] + (*(obs.apglen))[p+1]
		; Save all values after the stack
		for s=p+2, n_elements(*(obs.apgtim))-1 do begin
			newtime[s-1] = (*(obs.apgtim))[s] & newlength[s-1] = (*(obs.apglen))[s] & newchosen[s-1] = (*(obs.apgplt))[s]
		endfor
		; Save all new arrays to the obs struct
		obs.apgtim = ptr_new(newtime) & obs.apglen = ptr_new(newlength) & obs.apgplt = ptr_new(newchosen)
	endif
endfor
if par.sim eq 0 then return		; If we dont want to simulate observing, we exit now.

; ---- Simulate Observing
; If this a bad weather night, we note that time and return
if weather[0] eq 0 then begin
	for s=0, n_elements(*(obs.apglen))-1 do begin
		thislen = (*(obs.apglen))[s] - par.aovh/60.0
		if s eq n_elements(chosen)-1 and schedule.brtstrt lt schedule.drkstrt then thislen += par.aovh/60.0
		time.weaapg += total(thislen)
	endfor
	return
endif
; Begin looping through the night
for s=0, n_elements(*(obs.apgplt))-1 do begin
	weapct = 0
	; Break up observation into 7.5min exposures
	thislen = (*(obs.apglen))[s] - par.aovh/60.0
	if s eq n_elements(*(obs.apgplt))-1 and schedule.brtstrt lt schedule.drkstrt then thislen += par.aovh/60.0
	; Clear night, can use entire observation
	if weather[0] eq 2 then begin
		ints = round(thislen / 0.125)
	; Marginal Night, check how much of night we can use
	endif else begin
		; Check if bad weather region is outside this block
		if weather[1] gt (*(obs.apgtim))[s] + thislen/24.0 or weather[2] lt (*(obs.apgtim))[s] then ints = round(thislen / 0.125) $
		; Bad weather region is inside block
		else begin
			totints = round(thislen / 0.125)
			weabeg = max([(*(obs.apgtim))[s], weather[1]])
			weaend = min([(*(obs.apgtim))[s] + thislen/24.0, weather[2]])
			; Figure out what % of this block is taken up by weather, and scale number of exposures off that
			weapct = (weaend - weabeg) / (thislen/24.0)
			ints = round(totints * (1.0 - weapct))
			; Count time lost to weather
			time.weaapg += 0.125 * (totints - ints)
			if ints eq 0 then continue
		endelse
	endelse
	
	; Loop through integrations and simulate S/N
	sn = dblarr(ints)
	for i=0, ints-1 do begin
		; Count observed time
		time.obsapg += 0.125
	
		; Clear night
		if weather[0] eq 2 then begin
			snmean = 600
			snsigma = 40
		; Marginal night
		endif else begin
			snmean = 300
			snsigma = 80
		endelse
		; Generate random numbers and convert to gaussian
		rand1 = randomu(seed) & rand2 = randomu(seed)
		sn[i] = snsigma * sqrt(-2.*alog(rand1))*cos(2.*!PI*rand2) + snmean
	endfor
	
	; Check to see whether this is a valid plate
	if (*(obs.apgplt))[s] lt 0 then continue
	
	; Save observing results
	wgood = where(sn gt 100, ngood)
	; Check to see whether this design has been drilled multiple times
	wplate = where(apg[(*(obs.apgplt))[s]].fieldid eq apg.fieldid and apg[(*(obs.apgplt))[s]].apgver eq apg.apgver, nplate)
	; 2+ S/N > 10 exposures good enough for cadence visit
	if ngood ge 2 then begin
		apg[wplate].vdone++
		apg[wplate].hist += string(schedule.jd, format='(I7)') + ","
	endif
	; Any S/N > 10 exposures are added to S/N
	if ngood gt 0 then apg[wplate].sn += total(sn[wgood])
	
	; Write history of observation to file
	openw, nite, "output/APGnightly.txt", /get_lun, /append
	printf, nite, (*(obs.apgtim))[s]-2400000, apg[(*(obs.apgplt))[s]].plateid, ngood, "/", n_elements(sn), sqrt(total(sn[wgood])), thislen, weapct, format='(F14.5, 2I5, A2, I2, F6.1, 2F6.2)'
	free_lun, nite
endfor












END