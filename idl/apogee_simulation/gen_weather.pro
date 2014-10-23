PRO GEN_WEATHER, seed, schedule, weather, time

weather = [2,0,0]

;; Base weather probabilities
;gthresh = 0.20
;bthresh = 0.67
;
;; Adjust probabilities based on history
;if weather[0] eq 0 then begin
;	gthresh *= 1.1
;	bthresh *= 1.1
;endif else if weather[0] eq 2 then begin
;	gthresh *= 0.9
;	bthresh *= 0.9
;endif
;
;; Determine night start time
;if schedule.brtstrt eq 0 then nightbeg = schedule.drkstrt $
;else if schedule.drkstrt eq 0 then nightbeg = schedule.brtstrt $
;else nightbeg = min([schedule.brtstrt, schedule.drkstrt])
;	
;; Determine night end time
;if schedule.brtend eq 0 then nightend = schedule.drkend $
;else if schedule.drkend eq 0 then nightend = schedule.brtend $
;else nightend = max([schedule.brtend, schedule.drkend])
;	
;; Determine night length
;nightlen = nightend - nightbeg
;
;; Generate global random number to determine weather type
;globrand = randomu(seed)
;if globrand gt bthresh then begin				; Bad weather, the whole night is lost.
;	weather = [0, 0, 0]
;	time.wea += nightlen * 24.0
;endif else if globrand lt gthresh then begin	; Good weather, the whole night is usable.
;	weather = [2, 0, 0]
;	time.obs += nightlen * 24.0
;endif else begin							; Marginal weather, some of the night is lost.
;	; Generate two random numbers, to signify beginning and end of lost time
;	rand1 = (1.0 * randomu(seed) - 0.25) * nightlen + nightbeg
;	rand2 = nightend - (1.0 * randomu(seed) - 0.25) * nightlen
;	weather = [1, min([rand1, rand2]), max([rand1, rand2])]
;	
;	; Determine how much time is lost tonight
;	if weather[1] gt nightend or weather[2] lt nightbeg then begin
;		; Bad weather is outside the range of nighttime, no lost time
;		time.obs += nightlen * 24.0
;	endif else begin
;		; Determine when the bad weather kicks in
;		badstart = max([weather[1], nightbeg])
;		badend = min([weather[2], nightend])
;		time.wea += (badend - badstart) * 24.0
;		time.obs += (nightlen - badend + badstart) * 24.0
;	endelse
;endelse

END