PRO plan_manga, timestruct, schedulestruct, params, obsstruct

; Determine number of blocks currently chosen for APOGEE
if schedulestruct.brtstrt gt 0 and schedulestruct.manstrt gt schedulestruct.brtstrt then napg = n_elements(*(obsstruct.apgtimes)) else napg = 0

; ==== Define Blocks for MaNGA
	mlength = (schedulestruct.manend - schedulestruct.manstrt) * 24.0
	nslots = round(mlength/(params.mexp/60.0))
	if nslots lt 3 then return
	
	; MaNGA starts night, don't need overhead at beginning of night
	if (schedulestruct.brtstrt eq 0 or schedulestruct.manstrt lt schedulestruct.brtstrt) and (schedulestruct.bosstrt eq 0 or schedulestruct.manstrt lt schedulestruct.bosstrt) then nslots--
	
	finalnslots = min([nslots, (params.acart - napg)*4, (params.mcart)*4])
	if finalnslots eq 0 then begin
		print, "    WARNING: Insufficient number of MaNGA carts (mjd="+string(schedulestruct.jd-2400000, format='(I5)')+")"
		return
	endif
	
	; MaNGA goes at end of dark time
	if schedulestruct.bosstrt gt 0 and schedulestruct.bosstrt lt schedulestruct.manstrt then begin
		newmanstart = schedulestruct.manend - double(finalnslots) * params.mexp/60.0/24.0
		schedulestruct.bosend = newmanstart
	endif else newmanstart = schedulestruct.manstrt
	
	mtimes = newmanstart + dindgen(finalnslots) * params.mexp/60.0/24.0
	mexplengths = replicate(params.mexp/60.0, finalnslots)
	
	; Adjust survey start times, if necessary
	if schedulestruct.bosstrt gt schedulestruct.manstrt then schedulestruct.bosstrt = newmanstart + double(finalnslots) * params.mexp/60.0/24.0
	if schedulestruct.brtstrt gt schedulestruct.manstrt and schedulestruct.bosstrt eq 0 then schedulestruct.brtstrt = newmanstart + double(finalnslots) * params.mexp/60.0/24.0
	
	
	timestruct.obsman += total(mexplengths)
	obsstruct.mantimes = ptr_new(mtimes)
	obsstruct.manlengths = ptr_new(mexplengths)
	
; ==== Compute LSTs for Each Block
	manlst = (*(timestruct.manlst))
	OBSERVATORY, 'apo', obs_struct
	fake_ra = replicate(0.0,n_elements(mtimes)) & fake_dec = replicate(0.0,n_elements(mtimes))
	eq2hor, fake_ra, fake_dec, mtimes+mexplengths/24.0/2.0, alt, az, obsname='apo'
	altaz2hadec, alt, az, obs_struct.latitude, ha, dec
	
	for i=0, n_elements(ha)-1 do manlst[fix(ha[i]/15.0)] += mexplengths[i]
	timestruct.manlst = ptr_new(manlst)

END