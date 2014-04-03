PRO EBOSS, ebo, schedule, time, obs, weather, par, timeseed, lst=lst
; Check to see whether eBOSS observes tonight
if schedule.eboss eq 0 then return

; ---- Define eBOSS blocks for tonight 
blength = (schedule.bosend - schedule.bosstrt) * 24.0
nblocks = fix(blength / (par.bexp / 60.0))
if nblocks eq 0 then return

; Determine slot start times + exposure lengths
btimes = schedule.bosstrt + dindgen(nblocks) * par.bexp / 60.0 / 24.0
blengths = replicate(par.bexp / 60.0, nblocks)

; ---- Save blocks to obs struct
time.totebo += total(blengths)
obs.ebotim = ptr_new(btimes)
obs.ebolen = ptr_new(blengths)

; ---- Compute LSTs for tonight's blocks
blst = (*(time.lstebo))
OBSERVATORY, 'apo', apo
fakera = replicate(0.0,n_elements(btimes)) & fakedec = replicate(0.0,n_elements(btimes))
eq2hor, fakera, fakedec, btimes + blengths / 24.0 / 2.0, alt, az, obsname='apo'
altaz2hadec, alt, az, apo.latitude, ha, dec
for i=0, n_elements(ha)-1 do blst[fix(ha[i]/15.0)] += blengths[i]
time.lstebo = ptr_new(blst)
if keyword_set(lst) then return			; If we only want LSTs, we return here.

; ---- Prioritize Plates
; Base Priority
ebo.priority = 100.0 * ebo.manpriority
; Already Plugged
wplugged = where(ebo.plugged gt 0, nplugged)
if nplugged gt 0 then ebo[wplugged].priority += 5000.0
; Declination
ebo.priority -= 50.0 * exp( -(ebo.dec - 30.0)^2.0 / (2.0 * (20.0)^2.0))
; Completion
wcomplete = where(ebo.snb ge par.bsnb and ebo.snr ge par.bsnr, ncomplete)
if ncomplete gt 0 then ebo[wcomplete].priority = -2
; Drilling
wnotdrilled = where(ebo.drillmjd gt schedule.jd-2400000, nnotdrilled)
if nnotdrilled gt 0 then ebo[wnotdrilled].priority = -3

; ---- Determine Observability
obsarr = dblarr(n_elements(ebo), n_elements(*(obs.ebotim)))
for i=0, n_elements(ebo)-1 do begin
	OBSERVABILITY, ebo[i], (*(obs.ebotim)), (*(obs.ebolen)), par.bmaxz, par.bmoon, obsvalues
	; Adjust obsvalues based on necessary observations
	; Determine number of necessary observations to complete
	if ebo[i].snb eq 0 or ebo[i].snr eq 0 then nneeded = 4 $
	else nneeded = max([(par.bsnb - ebo[i].snb) / 3.0 + 1, (par.bsnr - ebo[i].snr) / 8.0 + 1, 1])
	; Determine number of possible slots tonight
	wobs = where(obsvalues ge 0.05, nobs)
	if nobs lt nneeded then obsvalues /= 10.0
	obsarr[i,*] = obsvalues
endfor

; ---- Pick Plates
tmpchosen = replicate(-1, n_elements(*(obs.ebotim)))
for i=0, n_elements(*(obs.ebotim))-1 do begin
	; Figure out if we've over-committed already
	wchosen = where(tmpchosen ge 0, nchosen)
	if nchosen ge par.bcart then continue
	; Find highest priority plate in this slot
	highpri = max(obsarr[*,i], hiidx)
	if highpri lt 1 then begin
		print, highpri
		print, "   WARNING: No EBO plates for block @ LST = "+strtrim(string(fix(ha[i]/15.0)),2)
		continue
	endif
	; Figure out how many slots this plate needs
	if ebo[hiidx].snb eq 0 or ebo[hiidx].snr eq 0 then nneeded = 4 $
	else nneeded = max([(par.bsnb - ebo[hiidx].snb) / 3.0 + 1, (par.bsnr - ebo[hiidx].snr) / 8.0 + 1, 1])
	wavail = where(obsarr[hiidx,i:n_elements(*(obs.ebotim))-1] ge 0.05, navail)
	; Choose this plate and assume it covers the entire number of needed observations, or available blocks
	tmpchosen[i] = hiidx
	i += min([nneeded, navail]) - 1
endfor
wchosen = where(tmpchosen ge 0, nchosen)
chosen = replicate(0, nchosen)
for i=0, nchosen-1 do chosen[i] = tmpchosen[wchosen[i]]
obs.eboplt = ptr_new(chosen)
if par.sim eq 0 then return		; If we don't want to simulate observing, we exit now.

; ---- Simulate Observing
; If this is a bad weather night, we note that time and return
if weather[0] eq 0 then begin
	time.weaebo += total(blengths)
	return
endif
; Begin looping through the night
for t=0, n_elements(btimes)-1 do begin
	; If this is a marginal night, check to see whether block can be used.
	if weather[0] eq 1 then begin
		; Entire block is covered by bad weather
		if weather[1] le btimes[t] and weather[2] ge btimes[t] + blengths[t] / 24.0 then begin
			time.weaebo += blengths[t]
			continue
		endif else begin
			; We will assume that if > 40% of the block is covered in bad weather, we can't use it
			weabeg = max([btimes[t], weather[1]])
			weaend = min([btimes[t] + blengths[t] / 24.0, weather[2]])
			weapct = (weaend - weabeg) / (blengths[t] / 24.0)
			if weapct gt 0.40 then begin
				time.weaebo += blengths[t]
				continue
			endif
		endelse	
	endif
	time.obsebo += blengths[t]
endfor

END