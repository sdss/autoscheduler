PRO OUTPUT_NIGHTLY, schedule, obsstruct, params, carts
openw, lun, "output/nightly.txt", /get_lun, /append

; Determine APOGEE start + end LSTs
astrlst = -1 & aendlst = -1 & napg = 0
if ptr_valid(obsstruct.apgtimes) and schedule.brtstrt gt 0 then begin
	abegend = [min(*(obsstruct.apgtimes)), max(*(obsstruct.apgtimes))+params.aexp/60.0/24.0]
	napg = n_elements(*(obsstruct.apgtimes))
	OBSERVATORY, 'apo', obs_struct
	fake_ra = replicate(0.0,2) & fake_dec = replicate(0.0,2)
	eq2hor, fake_ra, fake_dec, abegend, alt, az, obsname='apo'
	altaz2hadec, alt, az, obs_struct.latitude, ha, dec
	astrlst = ha[0]/15.0 & aendlst = ha[1]/15.0
endif

; Determine MaNGA start + end LSTs
mstrlst = -1 & mendlst = -1 & nman = 0
if ptr_valid(obsstruct.mantimes) and schedule.manstrt gt 0 then begin
	mbegend = [min(*(obsstruct.mantimes)), max(*(obsstruct.mantimes))+params.mexp/60.0/24.0]
	nman = round(n_elements(*(obsstruct.mantimes))/4.0)
	OBSERVATORY, 'apo', obs_struct
	fake_ra = replicate(0.0,2) & fake_dec = replicate(0.0,2)
	eq2hor, fake_ra, fake_dec, mbegend, alt, az, obsname='apo'
	altaz2hadec, alt, az, obs_struct.latitude, ha, dec
	mstrlst = ha[0]/15.0 & mendlst = ha[1]/15.0
endif

; Determine eBOSS start + end LSTs
bstrlst = -1 & bendlst = -1 & nbos = 0
if ptr_valid(obsstruct.bostimes) and schedule.bosstrt gt 0 then begin
	bbegend = [min(*(obsstruct.bostimes)), max(*(obsstruct.bostimes))+params.bexp/60.0/24.0]
	nbos = round(n_elements(*(obsstruct.bostimes))/4.0)
	OBSERVATORY, 'apo', obs_struct
	fake_ra = replicate(0.0,2) & fake_dec = replicate(0.0,2)
	eq2hor, fake_ra, fake_dec, bbegend, alt, az, obsname='apo'
	altaz2hadec, alt, az, obs_struct.latitude, ha, dec
	bstrlst = ha[0]/15.0 & bendlst = ha[1]/15.0
endif

printf, lun, schedule.jd-2400000, total(*(obsstruct.apglengths)), napg, astrlst, aendlst, total(*(obsstruct.manlengths)), nman, mstrlst, mendlst, total(*(obsstruct.boslengths)), nbos, bstrlst, bendlst, format='(I10, F16.2, I5, 2F8.2, F15.2, I5, 2F8.2, F15.2, I5, 2F8.2)'

; Update cart array to log number of cartridges used per survey
carts[0,napg]++ & carts[1,nman]++ & carts[2,nbos]++
if napg gt 0 and nman gt 0 then carts[3,napg+nman]++
if nman gt 0 and nbos gt 0 then carts[4,nman+nbos]++
carts[5,napg+nman+nbos]++

free_lun, lun
END