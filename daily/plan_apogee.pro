PRO plan_apogee, timestruct, schedulestruct, params, obsstruct

; Determine number of blocks currently chosen for MaNGA
if schedulestruct.manstrt gt 0 and schedulestruct.manstrt lt schedulestruct.brtstrt then nman = round(n_elements(*(obsstruct.mantimes))/4.0) else nman = 0

; ==== Define Blocks for APOGEE-2
	alength = (schedulestruct.brtend - schedulestruct.brtstrt)*24.0
	nslots = fix(alength/((params.aexp + params.aovh)/60.0))
	
	if schedulestruct.brtstrt lt schedulestruct.drkstrt or schedulestruct.drkstrt eq 0 then begin
		; APOGEE starts night
		if alength - double(nslots) * (params.aexp + params.aovh)/60.0 gt (params.amintime)/60.0 then nslots++
		finalnslots = min([nslots, params.acart - nman])
		
		atimes = schedulestruct.brtstrt + dindgen(finalnslots) * (params.aexp + params.aovh)/60.0/24.0
		if nslots gt 1 then aexplengths = replicate((params.aexp + params.aovh)/60.0, finalnslots-1)
		if nslots gt 1 then aexplengths = [aexplengths, params.aexp/60.0] else aexplengths = [params.aexp/60.0]
		
		; Adjust dark time program start time, if necessary
		if schedulestruct.drkstrt gt 0 then schedulestruct.drkstrt = schedulestruct.brtstrt + total(aexplengths)/24.0
	endif else begin
		; APOGEE starts after dark time programs
		if alength - double(nslots) * (params.aexp + params.aovh)/60.0 gt (params.amintime + params.aovh)/60.0 then nslots++
		finalnslots = min([nslots, params.acart - nman])
		
		atimes = schedulestruct.brtstrt + dindgen(finalnslots) * (params.aexp + params.aovh)/60.0/24.0 + params.aovh/60.0/24.0
		aexplengths = replicate((params.aexp + params.aovh)/60.0, finalnslots)
	endelse
	
	timestruct.obsapg += total(aexplengths)
	obsstruct.apgtimes = ptr_new(atimes)
	obsstruct.apglengths = ptr_new(aexplengths)

; ==== Compute LSTs For Each Block
	apglst = (*(timestruct.apglst))
	OBSERVATORY, 'apo', obs_struct
	fake_ra = replicate(0.0,n_elements(atimes)) & fake_dec = replicate(0.0,n_elements(atimes))
	eq2hor, fake_ra, fake_dec, atimes+aexplengths/24.0/2.0, alt, az, obsname='apo'
	altaz2hadec, alt, az, obs_struct.latitude, ha, dec
	
	for i=0, n_elements(ha)-1 do apglst[fix(ha[i]/15.0)] += aexplengths[i]
	timestruct.apglst = ptr_new(apglst)
END