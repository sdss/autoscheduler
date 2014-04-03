PRO SET_PARAMS, params

; Define necessary parameters
params =   {aexp: 60.0, $			; apogee-II exposure length
			aovh: 15.0, $			; apogee-II overhead
			acart: 9, $				; number of apogee-II carts
			amintime: 30.0, $		; minimum amount of time left over to add an extra cart
			amaxz: 3.0, $			; apogee-II maximum airmass
			aminz: 1.003, $			; apogee-II zenith avoidance limit
			amoon: 54000.0, $		; apogee-II moon avoidance limit (in arcseconds)
			amoonb: 36000.0, $		; apogee-II moon avoidance limit (in arcsecond) for bulge fields
			
			bexp: 16.5, $			; eboss exposure length
			bovh: 16.5, $			; eboss overhead
			bcart: 8, $				; number of eboss carts
			bmintime: 10.0, $		; minimum amount of time left over to add an extra slot
			
			mexp: 16.5, $			; manga exposure length (one offset position)
			movh: 16.5, $			; manga overhead
			mcart: 6}				; number of manga carts

END