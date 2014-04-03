PRO OUTPUT_FINAL, timestruct, params, carts

; Print time-sharing results to screen
totaltime = timestruct.totapg + timestruct.totman + timestruct.totboss + timestruct.toteng
timediff = (timestruct.totapg + timestruct.totman + timestruct.totboss) - (timestruct.obsapg + timestruct.obsman + timestruct.obsboss)
print, "APG: ", timestruct.totapg, timestruct.obsapg
print, "MAN: ", timestruct.totman, timestruct.obsman
print, "BOS: ", timestruct.totboss, timestruct.obsboss
print, "ENG: ", timestruct.toteng
print, "-------------------------------------"
print, "TOT: ", totaltime, timediff


; ---- Print LST Results to File
	openw, lun, "output/LSThrs.txt", /get_lun
	apglst = (*(timestruct.apglst)) & manlst = (*(timestruct.manlst)) & boslst = (*(timestruct.bosslst))
	for i=0, n_elements(apglst)-1 do printf, lun, i, apglst[i], manlst[i], boslst[i], format='(I5, 3F10.2)'
	printf, lun, ""
	printf, lun, 'NGC', total(apglst[6:19]), total(manlst[6:19]), total(boslst[6:19]), format='(A-5, 3F10.2)'
	printf, lun, 'SGC', total(apglst[0:5])+total(apglst[20:23]), total(manlst[0:5])+total(manlst[20:23]), total(boslst[0:5])+total(boslst[20:23]), format='(A-5, 3F10.2)'
	printf, lun, 'TOT', total(apglst), total(manlst), total(boslst), format='(A-5, 3F10.2)'
	free_lun, lun
	print, "ADJ: ", total(manlst[6:19])+(total(manlst[0:5])+total(manlst[20:23]))/1.4, total(boslst[6:19])+(total(boslst[0:5])+total(boslst[20:23]))/1.4
	
; ---- Print Cart Totals to File
	openw, lun, "output/carts.txt", /get_lun
	printf, lun, "Survey", indgen(17), format='(A-8, 17I6)' & printf, lun, ""
	printf, lun, "APG2", carts[0,0:16], format='(A-8, 17I6)'
	printf, lun, "MaNGA", carts[1,0:16], format='(A-8, 17I6)'
	printf, lun, "eBOSS", carts[2,0:16], format='(A-8, 17I6)' & printf, lun, ""
	printf, lun, "AP+MAN", carts[3,0:16], format='(A-8, 17I6)'
	printf, lun, "EBOSS+MAN", carts[4,0:16], format='(A-8, 17I6)'
	printf, lun, "TOTAL", carts[5,0:16], format='(A-8, 17I6)'

END