PRO plan_eboss, timestruct, schedulestruct, params, obsstruct

; ==== Define Blocks for eBOSS ====
	nslots = fix((schedulestruct.bosend - schedulestruct.bosstrt) / (params.bexp/60.0/24.0))

	; Determine the number of 16.5 minute blocks to break the time into
	if schedulestruct.manstrt gt 0 then begin
		; MaNGA is observed tonight, and cutoff has already been adjusted. eBOSS has a hard limit.
		finalnslots = min([nslots, params.bcart*4])
	endif else begin
		; Ending time is adjustable (either APOGEE or twilight limit)
		if (schedulestruct.bosend - schedulestruct.bosstrt) - double(nslots) * params.bexp/60.0/24.0 gt params.bmintime/60.0/24.0 then nslots++
		finalnslots = min([nslots, params.bcart*4])
		
		; If APOGEE follows, adjust its start time
		if schedulestruct.bosstrt lt schedulestruct.brtstrt then begin
			newend = schedulestruct.bosstrt + double(finalnslots) * params.bexp/60.0/24.0
			schedulestruct.brtstrt = newend
		endif
	endelse
	
	; Define slots
	btimes = schedulestruct.bosstrt + dindgen(finalnslots) * params.bexp/60.0/24.0
	bexplengths = replicate(params.bexp/60.0, finalnslots)
	
	timestruct.obsboss += total(bexplengths)
	obsstruct.bostimes = ptr_new(btimes)
	obsstruct.boslengths = ptr_new(bexplengths)
	
; ==== Compute LSTs for Each Block ====
	boslst = (*(timestruct.bosslst))
	OBSERVATORY, 'apo', obs_struct
	fake_ra = replicate(0.0,n_elements(btimes)) & fake_dec = replicate(0.0,n_elements(btimes))
	eq2hor, fake_ra, fake_dec, btimes+bexplengths/24.0/2.0, alt, az, obsname='apo'
	altaz2hadec, alt, az, obs_struct.latitude, ha, dec
	
	for i=0, n_elements(ha)-1 do boslst[fix(ha[i]/15.0)] += bexplengths[i]
	timestruct.bosslst = ptr_new(boslst)






END