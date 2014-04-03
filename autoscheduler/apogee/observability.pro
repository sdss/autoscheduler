PRO OBSERVABILITY, platedata, obstimes, obslengths, maxz, moonthresh, obsvalues

	obsvalues = replicate(platedata.priority, n_elements(obstimes))
	OBSERVATORY, 'apo', observparams

; Determine airmass values throughout exposures
	; Beginning of exposure
		EQ2HOR, replicate(platedata.ra, n_elements(obstimes)), replicate(platedata.dec, n_elements(obstimes)), obstimes, alt, az, OBSNAME='apo'
		ALTAZ2HADEC, alt, az, observparams.latitude, ha, dec
		where_highha = where(ha gt 180, n_highha) & if n_highha gt 0 then ha[where_highha] -= 360.0
		secz = 1.0D / cos((90.0D - alt) * !DPI / 180.0D)
		where_bad = where(ha lt platedata.minha or ha gt platedata.maxha or secz lt 1.003 or secz gt maxz, n_bad)
		if n_bad gt 0 then obsvalues[where_bad] = -0.1
		
	; Middle of exposure
		EQ2HOR, replicate(platedata.ra, n_elements(obstimes)), replicate(platedata.dec, n_elements(obstimes)), obstimes + 0.5D * obslengths/24.0, alt, az, OBSNAME='apo'
		ALTAZ2HADEC, alt, az, observparams.latitude, ha, dec
		where_highha = where(ha gt 180, n_highha) & if n_highha gt 0 then ha[where_highha] -= 360.0
		secz = 1.0D / cos((90.0D - alt) * !DPI / 180.0D)
		where_bad = where(ha lt platedata.minha or ha gt platedata.maxha or secz lt 1.003 or secz gt maxz, n_bad)
		if n_bad gt 0 then obsvalues[where_bad] = -0.2
		midpointha = ha
		
	; End of exposure
		EQ2HOR, replicate(platedata.ra, n_elements(obstimes)), replicate(platedata.dec, n_elements(obstimes)), obstimes + 0.9D * obslengths/24.0, alt, az, OBSNAME='apo'
		ALTAZ2HADEC, alt, az, observparams.latitude, ha, dec
		where_highha = where(ha gt 180, n_highha) & if n_highha gt 0 then ha[where_highha] -= 360.0
		secz = 1.0D / cos((90.0D - alt) * !DPI / 180.0D)
		where_bad = where(ha lt platedata.minha or ha gt platedata.maxha or secz lt 1.003 or secz gt maxz, n_bad)
		if n_bad gt 0 then obsvalues[where_bad] = -0.3


; Determine Moon Distance
	MOONPOS, obstimes + obslengths/24.0/2.0, moonra, moondec
	rarad = platedata.ra * !DPI / 180.0
	moonrarad = moonra * !DPI / 180.0
	decrad = platedata.dec * !DPI / 180.0
	moondecrad = moondec * !DPI / 180.0
	GCIRC, 0, rarad, decrad, moonrarad, moondecrad, dis
	moondist = dis * 206265.0d
	where_moonclose = where(moondist lt moonthresh, n_moonclose)
	if n_moonclose gt 0 then obsvalues[where_moonclose] = -1.0
	
; Gaussian priority bump based on time from transit
	where_valid = where(obsvalues gt 0, n_valid)
	if n_valid gt 0 then obsvalues[where_valid] += 50.0 * exp( - (platedata.ha - midpointha[where_valid])^2.0 / 2.0 )


END