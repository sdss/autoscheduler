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

; ---- Pick Plates

if par.sim eq 0 then return

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