PRO MANGA, man, schedule, time, obs, weather, par, lst=lst
; Check to see whether MaNGA observes tonight
if schedule.manga eq 0 then return

; ---- Define MaNGA blocks for tonight
mlength = (schedule.manend - schedule.manstrt) * 24.0
time.totman += mlength
mtimes = schedule.manstrt + dindgen(fix(mlength)) / 24.0

; ---- Compute LSTs for tonight's blocks
mlst = (*(time.lstman))
OBSERVATORY, 'apo', apo
fakera = replicate(0.0,n_elements(mtimes)) & fakedec = replicate(0.0,n_elements(mtimes))
eq2hor, fakera, fakedec, mtimes + 0.5 / 24.0, alt, az, obsname='apo'
altaz2hadec, alt, az, apo.latitude, ha, dec
for i=0, n_elements(ha)-1 do mlst[fix(ha[i]/15.0)] += 1.0
time.lstman = ptr_new(mlst)
if keyword_set(lst) then return

; Determine On-Sky and Lost-To-Weather hours
if weather[0] eq 0 then time.weaman += fix(mlength) $
else if weather[0] eq 2 then time.obsman += fix(mlength) $
else begin
	; Determine whether bad weather time is outside of MaNGA range
	if weather[2] lt schedule.manstrt or weather[1] gt schedule.manstrt + double(fix(mlength)) / 24.0 then time.obsman += fix(mlength) $
	else begin
		weabeg = max([schedule.manstrt, weather[1]])
		weaend = min([schedule.manstrt + double(fix(mlength)) / 24.0, weather[2]])
		weapct = (weaend - weabeg) / (double(fix(mlength)) / 24.0)
		time.obsman += double(fix(mlength)) * (1.0 - weapct)
		time.weaman += double(fix(mlength)) * weapct
	endelse
endelse




END