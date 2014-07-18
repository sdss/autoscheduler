PRO GET_PLATEDATA, apg, man, ebo, par

if par.sim eq 1 then begin
; ------- READ IN DATA FROM FILES ------

	; Read in APOGEE-II plate list
	spawn, "cat "+par.apgplatesfile, apglines
	apg = replicate({name:'', plateid:0, fieldid:0, apgver:0, ra:0.0, dec:0.0, ha:0.0, vplan:0, vdone:0, sn:0.0, manpriority:0, priority:0.0, hist:'', plugged:0, minha:0.0, maxha:0.0, drillmjd:0L, cadenceflag:0, stackflag:0}, n_elements(apglines))
	fieldidctr = 1000
	for i=0, n_elements(apglines)-1 do begin
		if strpos(apglines[i], ";") lt 3 then continue
		tmp = strsplit(apglines[i],/extract)
		; Read in basic plate info
		apg[i].name = tmp[0]
		apg[i].apgver = fix(tmp[5])
		apg[i].ra = double(tmp[1])
		apg[i].dec = double(tmp[2])
		apg[i].ha = double(tmp[11]) * 15.0
		apg[i].vplan = fix(tmp[6])
		apg[i].plateid = 5000 + i
		apg[i].manpriority = fix(tmp[9])
		; Determine drill date
		if tmp[10] eq 'Y1' then apg[i].drillmjd = 0 $
		else if tmp[10] eq 'Y2' then apg[i].drillmjd = 57203 $
		else if tmp[10] eq 'Y3' then apg[i].drillmjd = 57548 $
		else if tmp[10] eq 'Y4' then apg[i].drillmjd = 57946 $
		else if tmp[10] eq 'Y5' then apg[i].drillmjd = 58302 $
		else if tmp[10] eq 'Y6' then apg[i].drillmjd = 59032 $
		else print, "ERROR: DRILL YEAR: ",tmp[10]
		; Determine cadence flag
		if tmp[7] eq 'kep_koi' then apg[i].cadenceflag = 5 $
		else if apg[i].vplan eq 3 then apg[i].cadenceflag = 2 $
		else if apg[i].vplan eq 1 then apg[i].cadenceflag = 0 $
		else apg[i].cadenceflag = 1
		; Determine stacking flag
		if apg[i].vplan gt 10 then apg[i].stackflag = 1
		; Figure out fieldID
		wfield = where(apg[i].name eq apg.name, nfield)
		if nfield gt 1 then apg[i].fieldid = apg[wfield[0]].fieldid $
		else begin
			apg[i].fieldid = fieldidctr
			fieldidctr++
		endelse
		; Figure out observability range
		if apg[i].dec lt 35 then range = 0.9779 * apg[i].dec + 27.22 $
		else range = -1.0402 * apg[i].dec + 97.0
		if range lt 30 then range = 30.0
			apg[i].minha = apg[i].ha - range / 2.0
			apg[i].maxha = apg[i].ha + range / 2.0
	endfor

	; Read in eBOSS Plate List
	spawn, "cat "+par.bosplatesfile, bosslines
	ebo = replicate({plateid:0, ra:0.0D, dec:0.0D, ha:0.0, minha:0.0, maxha:0.0, manpriority:0, drillmjd:0L, priority:0.0, snr:0.0, snb:0.0, nvisits:0, nunplugged:0, plugged:0, hist:''}, n_elements(bosslines))
	for i=0, n_elements(bosslines)-1 do begin
		tmp = strsplit(bosslines[i],/extract)
		ebo[i].ra = double(tmp[0])
		ebo[i].dec = double(tmp[1])
		ebo[i].ha = double(tmp[2])
		ebo[i].manpriority = fix(tmp[3])
		ebo[i].drillmjd = long(tmp[4])
		ebo[i].plateid = 7000 + i
	
		if ebo[i].dec lt -10 then range = 30.0 $
		else if ebo[i].dec lt 35 then range = 0.9779 * ebo[i].dec + 27.22 $
		else range = -1.0402 * ebo[i].dec + 97.0
			ebo[i].minha = ebo[i].ha - range / 2.0
			ebo[i].maxha = ebo[i].ha + range / 2.0
	endfor
endif else begin
; ------- READ IN DATA FROM PLATEDB -------
	starttime = systime(1,/seconds)

	; Read in APOGEE-II plate data
	qstr="SELECT plt.location_id, ptg.center_ra, ptg.center_dec, plt.plate_id, pltg.hour_angle, pltg.priority, plt.design_pk, plt.name, pltg.ha_observable_max, pltg.ha_observable_min "+$
    	"FROM ((((((platedb.plate AS plt "+$
    		"INNER JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk = plt.pk)) "+$
    		"INNER JOIN platedb.plate_pointing AS pltg ON (pltg.plate_pk=plt.pk)) "+$
    		"INNER JOIN platedb.pointing AS ptg ON (pltg.pointing_pk=ptg.pk)) "+$
    		"INNER JOIN platedb.plate_location AS ploc ON (ploc.pk=plt.plate_location_pk)) "+$
    		"INNER JOIN platedb.plate_to_plate_status AS p2ps ON (p2ps.plate_pk=plt.pk))"+$
    		"INNER JOIN platedb.plate_status AS plts ON (plts.pk=p2ps.plate_status_pk))"+$
    	"WHERE p2s.survey_pk=1 AND plt.plate_id >= 4800 AND plts.label = 'Accepted' AND ploc.label = 'APO' "+$
    	"ORDER BY plt.plate_id"
	get_sql_col, qstr, locid, ra, dec, plateid, ha, prio, design_pk, names, hamax, hamin,/string
	
	; Generate APOGEE-II data structure
	apg = replicate({name:'', plateid:0, fieldid:0, apgver:0, ra:0.0, dec:0.0, ha:0.0, vplan:0, vdone:0, sn:0.0, manpriority:0, priority:0.0, hist:'', plugged:0, minha:0.0, maxha:0.0, drillmjd:0L, cadenceflag:0, stackflag:0}, n_elements(ra))
	
	; Save data from SQL query to array
	for i=0, n_elements(ra)-1 do begin
		apg[i].name = names[i]
		apg[i].plateid = plateid[i]
		apg[i].fieldid = locid[i]
		apg[i].ra = ra[i]
		apg[i].dec = dec[i]
		apg[i].ha = ha[i]
		apg[i].manpriority = prio[i]
		apg[i].minha = hamin[i]
		apg[i].maxha = hamax[i]
		; Add queries for these flags
		;apg[i].cadenceflag = 
		;apg[i].stackflag = 
	
		get_sql_col, "SELECT array_to_string(array_agg(dv.value),',') FROM platedb.design_value as dv WHERE (dv.design_field_pk=342 OR dv.design_field_pk=343 OR dv.design_field_pk=344 OR dv.design_field_pk=351) AND dv.design_pk="+design_pk[i], dvdata, /string
		tmp = strsplit(dvdata,',',/extract)
		apg[i].apgver = string(tmp[0], tmp[1], tmp[2], format='(I02,I01,I01)')
		if n_elements(tmp) ge 4 then apg[i].vplan = tmp[3] else apg[i].vplan = 3
	endfor
	apgsqltime = systime(1,/seconds)
	print, "[SQL]: READ IN APOGEE-II PLATES (", (apgsqltime-starttime)/60.0, "min)", format='(A,F3.1,A)'
	
	; Read in previous APOGEE-II observations
	qstr="SELECT plt.plate_id, obs.mjd, sum(qr.snr_standard^2.0), count(qr.snr_standard), sum(apr.snr^2.0), count(apr.snr) "+$
    	"FROM ((((((platedb.exposure AS exp "+$
        	"JOIN apogeeqldb.quickred AS qr ON (exp.pk=qr.exposure_pk)) "+$
            "LEFT JOIN apogeeqldb.reduction AS apr ON (exp.pk=apr.exposure_pk)) "+$
            "LEFT JOIN platedb.exposure_flavor AS expf ON (expf.pk=exp.exposure_flavor_pk)) "+$
            "LEFT JOIN platedb.observation AS obs ON (exp.observation_pk=obs.pk)) "+$
            "LEFT JOIN platedb.plate_pointing AS pltg ON (obs.plate_pointing_pk=pltg.pk)) "+$
            "RIGHT JOIN platedb.plate AS plt ON (pltg.plate_pk=plt.pk)) "+$
    	"WHERE exp.survey_pk=1 AND expf.label='Object' AND qr.snr_standard!='NaN' AND (qr.snr_standard >= 10.0 OR apr.snr >= 10.0) "+$
        "GROUP BY plt.plate_id, obs.mjd ORDER BY plt.plate_id"
	get_sql_col, qstr, plateid, obsmjd, snql, snqlcnt, snred, snredcnt, /string
	apgobssqltime = systime(1,/seconds)
	print, "[SQL]: READ IN APOGEE-II OBSERVATIONS (", (apgobssqltime-apgsqltime)/60.0, "min)", format='(A,F3.1,A)'
	
	; Print past observations to file (only useful for diagnostics)
	;openw, lun, "apgobs.txt", /get_lun
	;for i=0, n_elements(plateid)-1 do printf, lun, plateid[i], obsmjd[i], snql[i], snqlcnt[i], snred[i], snredcnt[i], format='(2I6, I8, I3, I8, I3)'
	;free_lun, lun
	
	; Add previous observation information to APG
	for i=0, n_elements(plateid)-1 do begin
		if plateid[i] eq 0 then continue
		; Find all other versions of this plate
		thisplate = where(apg.plateid eq plateid[i], nplate)
		if nplate eq 0 then continue
		ver = where(apg[thisplate[0]].fieldid eq apg.fieldid and apg[thisplate[0]].apgver eq apg.apgver, nver)
		if nver eq 0 then continue
		
		; Determine which S/N to use, reduction or QL
		if snred[i] gt 0 then begin
			sn = snred[i]
			sncnt = snredcnt[i]
		endif else begin
			sn = snql[i]
			sncnt = snqlcnt[i]
		endelse
		
		; Determine whether we can add MJD to observation history
		if sncnt ge 2 then apg[ver].hist += string(obsmjd[i], format='(I5)')+","
		; Add S/N to total
		apg[ver].sn += sn
	endfor
	apgobstime = systime(1,/seconds)
	print, "[IDL]: PARSED APOGEE-II OBSERVATIONS (", (apgobstime-apgobssqltime)/60.0, "min)", format='(A,F3.1,A)'
	
	; Read in all currently plugged plates
	qstr="SELECT crt.number, plt.plate_id, p2s.survey_pk "+$
        "FROM (((((platedb.active_plugging AS ac "+$
        	"JOIN platedb.plugging AS plg ON (ac.plugging_pk=plg.pk)) "+$
        	"LEFT JOIN platedb.cartridge AS crt ON (plg.cartridge_pk=crt.pk)) "+$
        	"LEFT JOIN platedb.plate AS plt ON (plg.plate_pk=plt.pk)) "+$
        	"LEFT JOIN platedb.plate_to_survey AS p2s ON (p2s.plate_pk=plt.pk)) "+$
        	"LEFT JOIN platedb.plate_pointing as pltg ON (pltg.plate_pk=plt.pk)) "+$
        "ORDER BY crt.number"
	get_sql_col, qstr, cartid, plateid, survey, /string
	
	; Loop through currently plugged plates and mark them in the data structs
	for i=0, n_elements(cartid)-1 do begin
		if survey[i] eq 1 then begin	; APOGEE-II
			wplate = where(plateid eq apg.plateid, nplate)
			if nplate eq 0 then continue
			apg[wplate[0]].plugged = cartid[i]
		endif else if survey[i] eq 2 then begin		; eBOSS
			wplate = where(plateid eq ebo.plateid, nplate)
			if nplate eq 0 then continue
			ebo[wplate[0]].plugged = cartid[i]
		endif else if survey[i] eq 35 then begin	; MaNGA
			wplate = where(plateid eq man.plateid, nplate)
			if nplate eq 0 then continue
			man[wplate[0]].plugged = cartid[i]
		endif
	endfor
	
endelse




END