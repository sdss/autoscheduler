PRO SET_PARAMS, params

; Define necessary parameters
params =   {schedulefile: "../schedules/Sch_base.sdss3.txt", $			; Schedule filename
			apgplatesfile: "platelists/apogee2_2016-02-10_forBen.dat", $				; APOGEE-II plate list filename
			bosplatesfile: "platelists/EBOSS.1113.txt", $		; eBOSS plate list filename
			
			sim: 1, $				; Are we simulating?

			aexp: 60.0, $			; apogee-II exposure length
			aovh: 20.0, $			; apogee-II overhead
			acart: 9, $				; number of apogee-II carts
			amaxz: 3.0, $			; apogee-II maximum airmass
			amoon: 54000.0, $		; apogee-II moon avoidance limit (in arcseconds)
			asn: 3136, $			; apogee-II target S/N^2 per visit 
			
			bexp: 16.5, $			; eboss exposure length
			bovh: 16.5, $			; eboss overhead
			bcart: 8, $				; number of eboss carts
			bmintime: 10.0, $		; minimum amount of time left over to add an extra slot
			bsnb: 10.0, $			; eboss desired S/N^2 in the blue chip
			bsnr: 25.0, $			; eboss desired S/N^2 in the red chip
			bmoon: 108000.0, $		; eboss moon avoidance (in arcseconds)
			bmaxz: 2.0}			; eboss maximum airmass

	
END