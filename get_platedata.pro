PRO GET_PLATEDATA, apg, man, ebo, par

if par.sim eq 1 then begin
; ------- READ IN DATA FROM FILES ------

	; Read in APOGEE plate list
	spawn, "cat "+par.apgplatesfile, apglines
	apg = replicate({name:'', plateid:0, fieldid:0, apgver:0, ra:0.0, dec:0.0, ha:0.0, vplan:0, vdone:0, sn:0.0, manpriority:0, priority:0.0, hist:'', plugged:0, minha:0.0, maxha:0.0, drillmjd:0L, cadenceflag:0}, n_elements(apglines))
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
endelse




END