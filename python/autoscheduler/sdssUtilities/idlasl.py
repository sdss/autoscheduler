import numpy as np

def idlMod(a, b):
	"""
		Emulate 'modulo' behavior of IDL.
		
		Parameters
		----------
		a : float or array
				Numerator
		b : float
				Denominator
		
		Returns
		-------
		IDL modulo : float or array
				The result of IDL modulo operation.
	"""
	if isinstance(a, np.ndarray):
		s = np.sign(a)
		m = np.mod(a, b)
		m[(s < 0)] -= b
	else:
		m = a % b
		if a < 0: m -= b
	return m

def cirrange(x, radians=False):
	if radians:
		m = 2.0 * np.pi
	else:
		m = 360.0
	return x % m
	
def nutate(jd, radian=False, plot=False):

	#form time in Julian centuries from 1900.0
	jdcen = (np.array(jd, ndmin=1) - 2451545.0)/36525.0
	
	#Mean elongation of the Moon
	coef_moon = [1.0/189474.0, -0.0019142, 445267.111480, 297.85036]
	d = np.polyval(coef_moon, jdcen)*np.pi/180.
	d = cirrange(d, radians=True)

	#Sun's mean anomaly
	coef_sun = [-1.0/3e5, -0.0001603, 35999.050340, 357.52772]
	sun = np.polyval(coef_sun, jdcen)*np.pi/180.
	sun = cirrange(sun, radians=True)

	# Moon's mean anomaly
	coef_mano = [1.0/5.625e4, 0.0086972, 477198.867398, 134.96298]
	mano = np.polyval(coef_mano, jdcen)*np.pi/180.
	mano = cirrange(mano, radians=True)

	# Moon's argument of latitude
	coef_mlat = [-1.0/3.27270e5, -0.0036825, 483202.017538, 93.27191]
	mlat = np.polyval(coef_mlat, jdcen)*np.pi/180.
	mlat = cirrange(mlat, radians=True)
	
	# Longitude of the ascending node of the Moon's mean orbit on the ecliptic,
	#	measured from the mean equinox of the date
	coef_moe = [1.0/4.5e5, 0.0020708, -1934.136261, 125.04452]
	omega = np.polyval(coef_moe, jdcen)*np.pi/180.
	omega = cirrange(omega, radians=True)

	d_lng = np.array([0.,-2.,0.,0.,0.,0.,-2.,0.,0.,-2,-2,-2,0,2,0,2,0,0,-2,0,2,0,0,-2,0,-2,0,0,2, \
					 -2,0,-2,0,0,2,2,0,-2,0,2,2,-2,-2,2,2,0,-2,-2,0,-2,-2,0,-1,-2,1,0,0,-1,0,0, \
					 2,0,2], float)

	m_lng = np.array([0,0,0,0,1,0,1,0,0,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,2,1,0,-1,0,0,0,1,1,-1,0, \
					 0,0,0,0,0,-1,-1,0,0,0,1,0,0,1,0,0,0,-1,1,-1,-1,0,-1], float)

	mp_lng = np.array([0,0,0,0,0,1,0,0,1,0,1,0,-1,0,1,-1,-1,1,2,-2,0,2,2,1,0,0,-1,0,-1, \
						0,0,1,0,2,-1,1,0,1,0,0,1,2,1,-2,0,1,0,0,2,2,0,1,1,0,0,1,-2,1,1,1,-1,3,0], float)

	f_lng = np.array([0,2,2,0,0,0,2,2,2,2,0,2,2,0,0,2,0,2,0,2,2,2,0,2,2,2,2,0,0,2,0,0, \
					 0,-2,2,2,2,0,2,2,0,2,2,0,0,0,2,0,2,0,2,-2,0,0,0,2,2,0,0,2,2,2,2], float)

	om_lng = np.array([1,2,2,2,0,0,2,1,2,2,0,1,2,0,1,2,1,1,0,1,2,2,0,2,0,0,1,0,1,2,1, \
						1,1,0,1,2,2,0,2,1,0,2,1,1,1,0,1,1,1,1,1,0,0,0,0,0,2,0,0,2,2,2,2], float)

	sin_lng = np.array([-171996, -13187, -2274, 2062, 1426, 712, -517, -386, -301, 217, \
						 -158, 129, 123, 63, 63, -59, -58, -51, 48, 46, -38, -31, 29, 29, 26, -22, \
						 21, 17, 16, -16, -15, -13, -12, 11, -10, -8, 7, -7, -7, -7, \
						 6,6,6,-6,-6,5,-5,-5,-5,4,4,4,-4,-4,-4,3,-3,-3,-3,-3,-3,-3,-3 ], float)
 
	sdelt = np.array([-174.2, -1.6, -0.2, 0.2, -3.4, 0.1, 1.2, -0.4, 0., -0.5, 0., 0.1, \
					 0.,0.,0.1, 0.,-0.1,0.,0.,0.,0.,0.,0.,0.,0.,0.,0., -0.1, 0., 0.1, \
					 0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.] , float)

	cos_lng = np.array([ 92025, 5736, 977, -895, 54, -7, 224, 200, 129, -95,0,-70,-53,0, \
							-33, 26, 32, 27, 0, -24, 16,13,0,-12,0,0,-10,0,-8,7,9,7,6,0,5,3,-3,0,3,3, \
							0,-3,-3,3,3,0,3,3,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ], float)

	cdelt = np.array([8.9, -3.1, -0.5, 0.5, -0.1, 0.0, -0.6, 0.0, -0.1, 0.3, \
					 0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0., \
					 0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.], float)

	# Sum the periodic terms 
	n = jdcen.size
	nut_lon = np.zeros(n)
	nut_obliq = np.zeros(n)
	arg = np.outer(d_lng,d) + np.outer(m_lng,sun) + np.outer(mp_lng,mano) + \
				np.outer(f_lng,mlat) + np.outer(om_lng,omega)
	arg = np.transpose(arg)
	sarg = np.sin(arg)
	carg = np.cos(arg)
	for i in range(n):
		nut_lon[i] = 0.0001*np.sum( (sdelt*jdcen[i] + sin_lng)*sarg[i] )
		nut_obliq[i] = 0.0001*np.sum( (cdelt*jdcen[i] + cos_lng)*carg[i] )
	
	# Until here result are in arcseconds!
	# Convert to degrees
	nut_lon /= 3600.
	nut_obliq /= 3600.
	if radian:
		nut_lon *= (np.pi/180.)
		nut_obliq *= (np.pi/180.)
	
	return nut_lon, nut_obliq
	
def co_nutate(jd, ra, dec, radian=False, full_output=False):
	"""
		Compute the changes in RA and DEC due to the Earth's nutation.
		
		Parameters
		----------
		jd : float or array
				 The Julian date. If given as array,
				 its size must match that of `ra` and `dec`.
		ra : float or array
				 The right ascension in degrees.
				 If array, it must be same size as `dec`.
		dec : float or array
				 The declination in degrees.
				 If array, it must be same size as ra.
		radian : boolean, optional
				 Results are returned in radian instead of in degrees.
				 The default is False.
		plot : boolean, optional
				 If True, the results are plotted.
				 For single value `jd`, the change in `ra` and `dec` is plotted
				 versus `ra` and `dec`.
				 For an array of JDs, ra and dec is plotted versus JD.
				 The default is False
		full_output : boolean, optional 
				 If True, the result will also contain the obliquity of the ecliptic,
				 the nutation in the longitude and the nutation in the
				 obliquity of the ecliptic. The default is False.

		Returns
		-------
		dRa : float or array
				The change in right ascension [by default in deg].
		dDec : float or array
				The change in declination [by default in deg].
		True obliquity : float, optional
				The true obliquity of the ecliptic [by default in deg].
				Only if `full_output` is True.
		dLong : float or array, optional
				The nutation in longitude [by default in deg].
				Only if `full_output` is True.
		dObliquity : float or array, optional
				The nutation in the obliquity of the ecliptic [by default in deg].
				Only if `full_output` is True.
	"""
	
	ra = np.array(ra)
	dec = np.array(dec)
	num = ra.size
		
	# Julian centuries from J2000 of jd.
	jdcen = (np.array(jd) - 2451545.0)/36525.0

	# Must calculate obliquity of ecliptic
	nut = nutate(jd)
	# Change degrees to seconds
	d_psi = nut[0]*3600.
	d_eps = nut[1]*3600.

	eps0 = 23.4392911*3600. - 46.8150*jdcen - 0.00059*jdcen**2 + 0.001813*jdcen**3
	# True obliquity of the ecliptic in radians
	eps = (eps0 + d_eps)/3600.*(np.pi/180.)

	ce = np.cos(eps)
	se = np.sin(eps)

	# convert ra-dec to equatorial rectangular coordinates
	x = np.cos(ra*np.pi/180.) * np.cos(dec*np.pi/180.)
	y = np.sin(ra*np.pi/180.) * np.cos(dec*np.pi/180.)
	z = np.sin(dec*np.pi/180.)

	# apply corrections to each rectangular coordinate
	x2 = x - (y*ce + z*se)*d_psi * (np.pi/(180.*3600.))
	y2 = y + (x*ce*d_psi - z*d_eps) * (np.pi/(180.*3600.))
	z2 = z + (x*se*d_psi + y*d_eps) * (np.pi/(180.*3600.))
		
	# convert back to equatorial spherical coordinates
	r = np.sqrt(x2**2 + y2**2 + z2**2)
	xyproj = np.sqrt(x2**2 + y2**2)

	ra2 = x2 * 0.
	dec2= x2 * 0.

	if num == 1:
		# Calculate Ra and Dec in RADIANS (later convert to DEGREES)
		if np.logical_and( xyproj == 0 , z != 0 ):
			# Places where xyproj==0 (point at NCP or SCP)
			dec2 = np.arcsin(z2/r)
			ra2 = 0.
		if xyproj != 0:
			# places other than NCP or SCP
			ra2 = np.arctan2( y2 , x2 )
			dec2 = np.arcsin( z2/r )			
	else:
		w1 = np.where( np.logical_and( xyproj == 0 , z != 0 ) )[0]
		w2 = np.where( xyproj != 0 )[0]
		# Calculate Ra and Dec in RADIANS (later convert to DEGREES)
		if len(w1) > 0:
			# Places where xyproj==0 (point at NCP or SCP)
			dec2[w1] = np.arcsin(z2[w1]/r[w1])
			ra2[w1] = 0.
		if len(w2) > 0:
			# Places other than NCP or SCP
			ra2[w2] = np.arctan2( y2[w2] , x2[w2] )
			dec2[w2] = np.arcsin( z2[w2]/r[w2] )

	# Convert into DEGREES
	ra2 = ra2/np.pi*180.
	dec2 = dec2/np.pi*180.
	d_psi /= 3600.
	d_eps /= 3600.

	if num == 1:
		if ra2 < 0.: ra2 += 360.
	else:
		w = np.where( ra2 < 0. )[0]
		if len(w) > 0: ra2[w] += 360.

	# Return changes in ra and dec
	d_ra = (ra2 - ra)
	d_dec = (dec2 - dec)

	if radian:
		# convert result to RADIAN
		d_ra *= (np.pi/180.)
		d_dec *= (np.pi/180.)
		d_psi *= (np.pi/180.)
		d_eps *= (np.pi/180.)
	else:
		eps = eps/np.pi*180. # eps in DEGREES

	if full_output:
		return d_ra, d_dec, eps, d_psi, d_eps		
	else:
		return d_ra, d_dec
		
def co_aberration(jd, ra, dec, radian=False):
	"""
		Computes the changes in RA and DEC due to annual aberration.
		
		Parameters
		----------
		jd : float or array
				 The Julian date(s). If array, must be the same size as
				 `ra` and `dec`.
		ra : float or array
				 The right ascension in degrees.
				 If array, it must be the same size as `dec`.
		dec : float or array
				 The declination in degrees.
				 If array, it must be the same size as `ra`.
		radian : boolean, optional
				 Results are returned in radian instead of degrees.
				 The default is False.
						 
		Returns
		-------
		dRa : float or array
				The change in right ascension [by default in deg].
		dDec : float or arrays
				The change in declination [by default in deg].
	"""

	ra = np.array(ra, ndmin=1)
	dec = np.array(dec, ndmin=1)
	jd = np.array(jd, ndmin=1)

	# Julian centuries from J2000 of jd.
	jdcen = ( jd - 2451545.0 ) / 36525.0
	# Must calculate obliquity of ecliptic
	res = nutate(jd)
	d_eps = res[1]

	eps0 = 23.4392911*3600. - 46.8150*jdcen - 0.00059*jdcen**2 + 0.001813*jdcen**3
	eps = (eps0/3600. + d_eps)*(np.pi/180.)	#true obliquity of the ecliptic in radians
	
	if jd.size == 1:
		sunlon = np.ravel(sunpos(jd, full_output=True)[3])
	else:
		sunlon = np.zeros( jd.size )
		for i in range(jd.size):
			sunlon[i] = np.ravel(sunpos(jd[i], full_output=True)[3])

	# Earth's orbital eccentricity
	e = 0.016708634 - 0.000042037*jdcen - 0.0000001267*jdcen**2
	# Longitude of perihelion in degrees 
	pi = 102.93735 + 1.71946*jdcen + 0.00046*jdcen**2 
	# Constant of aberration in arcseconds
	k = 20.49552
	
	# Trigonometric Functions
	cd = np.cos(dec*np.pi/180.)
	sd = np.sin(dec*np.pi/180.)
	ce = np.cos(eps)
	te = np.tan(eps)
	cp = np.cos(pi*np.pi/180.)
	sp = np.sin(pi*np.pi/180.)
	cs = np.cos(sunlon*np.pi/180.)
	ss = np.sin(sunlon*np.pi/180.)
	ca = np.cos(ra*np.pi/180.)
	sa = np.sin(ra*np.pi/180.)

	term1 = (ca*cs*ce+sa*ss)/cd
	term2 = (ca*cp*ce+sa*sp)/cd
	term3 = (cs*ce*(te*cd-sa*sd)+ca*sd*ss)
	term4 = (cp*ce*(te*cd-sa*sd)+ca*sd*sp)

	# in ARCSECONDS
	d_ra = -k * term1 + e*k * term2
	d_dec = -k * term3 + e*k * term4
	d_ra /= 3600.
	d_dec /= 3600.

	if radian:
		# Convert result into radian
		d_ra *= (np.pi/180.)
		d_dec *= (np.pi/180.)

	return d_ra, d_dec
	
def ct2lst(jd, lon):
	"""
		Converts the Local Civil Time (given as Julian Date) into Local Mean Sidereal Time.
		
		Parameters
		----------
		jd : float or array
				 The Local Civil Time as Julian date (UT).
				 If given as array, its size must be equal to that of `lon`.
		lon : float or array
				 The right ascension in DEGREES.
								 
		Returns
		-------
		Time : list
				A list holding the Local Mean Sidereal Time in hours (0 - 24)
				for the given Julian dates and right ascensions.				
	"""

	jd_vals = np.array(jd)
	lon_vals = np.array(lon)
	
	# Useful constants, see Meeus, p.84
	c = np.array([280.46061837, 360.98564736629, 0.000387933, 38710000.0 ], float)
	jd2000 = 2451545.0
	t0 = jd_vals - jd2000
	time = t0/36525.0
	
	# Compute GST in seconds.
	theta = c[0] + (c[1] * t0) +	( c[2] - time / c[3] ) * time**2
	
	# Compute LST in hours.
	lst = ( theta + lon_vals )/15.0
	neg = np.where(lst < 0.0)[0]
	if len(neg) > 0:
		lst[neg] = 24.0 + idlMod(lst[neg], 24.)
	
	# Local sidereal time in hours (0. to 24.)
	lst = idlMod(lst, 24.0)

	return lst
	
def precess(ra, dec, equinox1, equinox2, FK4 = False, radian=False):
	"""
		Precess coordinates from EQUINOX1 to EQUINOX2.
	
		Parameters
		----------
		ra, dec, equinox1, equinox2 : float
				Position and equinox
		FK4 : boolean
				Set to True to obtain output in FK4 system.
		radian : boolean
				If True, `ra` and `dec` must be given in radian (degrees otherwise). 

		Returns
		-------
		Position : list of ra and dec
				A list with [ra, dec] precessed from equinox 1 to equinox 2.
	"""
	deg_to_rad = np.pi/180.0

	if not radian:
		# ra, dec are given in degrees
		ra_rad = ra*deg_to_rad		 # Convert to double precision if not already
		dec_rad = dec*deg_to_rad
	else:
		ra_rad = ra ; dec_rad = dec

	a = np.cos( dec_rad )


	x = [a*np.cos(ra_rad), a*np.sin(ra_rad), np.sin(dec_rad)] # input direction

	sec_to_rad = deg_to_rad/3600.0

	# Use PREMAT function to get precession matrix from Equinox1 to Equinox2

	r = premat(equinox1, equinox2, FK4 = FK4)

	x2 = np.dot(r,x)			# rotate to get output direction cosines

	ra_rad = np.arctan2(x2[1],x2[0])
	dec_rad = np.arcsin(x2[2])

	if not radian:
		ra = ra_rad/deg_to_rad
		ra = ra + int(ra < 0.0)*360.0						# RA between 0 and 360 degrees
		dec = dec_rad/deg_to_rad
	else:
		ra = ra_rad ; dec = dec_rad
		ra = ra + int(ra < 0.0)*2.0*np.pi

	return [ra, dec]
	
def premat( equinox1, equinox2, FK4 = False):

	deg_to_rad = np.pi/180.0
	sec_to_rad = deg_to_rad/3600.0

	t = 0.001*(equinox2 - equinox1)

	if not FK4:
		st = 0.001*(equinox1 - 2000.0)
		# Compute 3 rotation angles
		A = sec_to_rad * t * (23062.181 + st*(139.656 +0.0139*st) \
				+ t*(30.188 - 0.344*st+17.998*t))

		B = sec_to_rad * t * t * (79.280 + 0.410*st + 0.205*t) + A

		C = sec_to_rad * t * (20043.109 - st*(85.33 + 0.217*st) \
				+ t*(-42.665 - 0.217*st -41.833*t))

	else:
		st = 0.001*(equinox1 - 1900.0)
		# Compute 3 rotation angles

		A = sec_to_rad * t * (23042.53 + st*(139.75 +0.06*st) \
				+ t * (30.23 - 0.27*st+18.0*t))

		B = sec_to_rad * t * t * (79.27 + 0.66*st + 0.32*t) + A

		C = sec_to_rad * t * (20046.85 - st*(85.33 + 0.37*st) \
				+ t*(-42.67 - 0.37*st -41.8*t))

	sina = np.sin(A) ;	sinb = np.sin(B)	; sinc = np.sin(C)
	cosa = np.cos(A) ;	cosb = np.cos(B)	; cosc = np.cos(C)

	r = np.zeros((3,3))
	r[::,0] = np.array([ cosa*cosb*cosc-sina*sinb, sina*cosb+cosa*sinb*cosc,	cosa*sinc])
	r[::,1] = np.array([-cosa*sinb-sina*cosb*cosc, cosa*cosb-sina*sinb*cosc, -sina*sinc])
	r[::,2] = np.array([-cosb*sinc, -sinb*sinc, cosc])
	return r
	
def hadec2altaz(ha, dec, lat, ws=False, radian=False):
	"""
		Convert hour angle and declination into horizon (alt/az) coordinates.
		
		Parameters
		----------
		ha : float or array
				Local apparent hour angle in DEGREES.
		dec : float or array
				Local apparent declination in DEGREES.
		lat : float or array
				Local latitude in DEGREES.
		radian : boolean, optional
				If True, the result is returned in radian
				instead of in degrees (default is False).
		ws : boolean, optional
				Set this to True, if the azimuth shall be measured West from South.
				Default is to measure azimuth East from North.

		Returns
		-------
		Altitude : list
				A list holding the Local Apparent Altitude [deg].
		Apparent Azimuth : list
				The Local Apparent Azimuth [deg].
	"""
	
	ha = np.array(ha)
	dec = np.array(dec)
	lat = np.array(lat)
	
	sh = np.sin(ha*np.pi/180.)
	ch = np.cos(ha*np.pi/180.)
	sd = np.sin(dec*np.pi/180.)
	cd = np.cos(dec*np.pi/180.)
	sl = np.sin(lat*np.pi/180.)
	cl = np.cos(lat*np.pi/180.)

	x = - ch * cd * sl + sd * cl
	y = - sh * cd
	z = ch * cd * cl + sd * sl
	r = np.sqrt(x**2 + y**2)

	# Now get Alt, Az
	az = np.arctan2(y,x) / (np.pi/180.)
	alt = np.arctan2(z,r) / (np.pi/180.)

	# Correct for negative AZ
	if ha.size==1:
		if az < 0: az += 360.
	else:
		w = np.where(az < 0)[0]
		if len(w) > 0: az[w] += 360.

	# Convert AZ into West from South, if desired
	if ws: az = idlMod( (az + 180.), 360.)
	
	if radian:
		alt *= np.pi/180.
		az *= np.pi/180.

	return alt, az
	
def co_refract_forward(alt, pressure=1010., temperature=10.0):
	"""
		Converts the observed into the apparent (real) altitude.
		
		The *observed altitude* is the altitude that a star is seen
		to be with a telescope. This is where it appears in the sky.
		The observed altitude is always greater than the
		the *apparent altitude*, which is the altitude that a star would
		be at, if there were no atmosphere (sometimes called "true" altitude).
		
		Parameters
		----------
		alt : float or array
				Observed altitude of an object in DEGREES.
		pressure : float or array, optional
				Atmospheric pressure in MILLIBAR.
				Default pressure is 1010 mbar. If a single value is
				given, it will be used for all given altitudes.
		temperature : float or array, optional
				Ground temperature in degrees Celsius.
				Default temperature is 10 Celsius. If a single value is
				given, it will be used for all given altitudes.
				 
		Returns
		-------
		Altitude correction : array
				An array holding the altitude correction [deg]. To convert
				observed altitude into apparent (real) altitude, the
				correction needs to be subtracted from the observed
				altitude.
	"""
	
	alt = np.array(alt, ndmin=1)
	pres = np.array(pressure, ndmin=1)
	# Temperature in Kelvin
	temper = np.array(temperature, ndmin=1) + 273.15

	# You observed the altitude alt, and would like to know what the "apparent" 
	# altitude is (the one behind the atmosphere).
	R = 0.0166667 / np.tan( (alt + 7.31/(alt+4.4))*np.pi/180. )

	w = np.where(alt < 15.)[0]
	if len(w) > 0:
		R[w] = 3.569*(0.1594 + 0.0196*alt[w] + 0.00002*alt[w]**2)/(1.+0.505*alt[w]+0.0845*alt[w]**2)

	tpcor = pres/1010. * 283./temper
	R *= tpcor

	return R
	
def co_refract(alt, observer_alt=0.0, pressure=None, temperature=None, epsilon=0.25, convert_to_observed=False, full_output=True):
	"""
		Convert between apparent (real) altitude and observed altitude.
		
		This routine converts between the apparent (real) altitude 
		of the object, which does not include the
		influence of the atmosphere, and the observed
		altitude, which is the altitude as seen
		through the atmosphere.
		
		The `convert_to_observed` flag determines the direction of the
		conversion. By default, observed altitude is converted into
		apparent altitude.
		
		Parameters
		----------
		alt : float or array
				Altitude of an object in DEGREES. Whether the value is
				interpreted as apparent or observed altitude depends on the
				`convert_to_observed` flag. By default, it refers to the
				apparent (real) altitude.
		observer_alt : float or array, optional
				Altitude of the observer in METER. Default is 0 (sea level).
		pressure : float or array, optional
				Atmospheric pressure in MILLIBAR.
				Default pressure is 1010 mbar.
				If `observer_alt` is given, an estimate for the real
				atmospheric pressure is calculated and used.
		temperature : float or array, optional
				Atmospheric temperature at the observing location in Celsius.
				If not specified, the temperature will be calculated
				assuming a ground temperature of 10 degrees Celsius.
		epsilon : float, optional
				If convert_to_observed is TRUE, it specifies the accuracy of
				the calculated altitude in ARCSECONDS that should be reached 
				by the iteration process.
		convert_to_observed : boolean, optional
				If set True, an iterative method is used to calculate
				the observed altitude of an object, which includes
				atmospheric refraction. If False (default), the given altitude
				will be interpreted as the observed altitude and the apparent (real)
				altitude will be calculated using :py:func:`co_refract_forward`.
		full_output : boolean, optional
				If True (default), pressure and temperature used in the calculation
				will be returned as well.

		Returns
		-------
		Altitude : array
				By default, this will be the observed altitude of the object in
				degrees. If `convert_to_observed` was set to False, the number
				refers to the apparent (real) altitude.
		Pressure : array
				The pressure [mbar] used in the calculations (only returned if
				`full_output` is True).
		Temperature : array
				The temperature used in the calculations [K] (only returned if
				`full_output` is True).
	"""
	old_alt = np.array(alt, ndmin=1)
		
	if observer_alt is not None:
		# Observer altitude has been given
		obsalt = np.array(observer_alt, ndmin=1)
	else:
		# Assume that observer is on the ground (altitude 0).
		obsalt = np.zeros(old_alt.size)

	if temperature is not None:
		# Temperature is given
		temper = np.array(temperature, ndmin=1)
		# Convert temperature to Kelvin
		temper += 273.15
	else:
		# No temperature has been specified. Use approximation
		# based on altitude of observer.
		# 
		# Temperature lapse rate [deg C per meter]
		alpha = 0.0065
		temper = np.zeros(old_alt.size) + 283. - alpha*obsalt
		ind = np.where(obsalt > 11000.)[0]
		if len(ind) > 0:
			temper[ind] = 211.5

	# Estimate Pressure based on altitude, using U.S. Standard Atmosphere formula.
	if pressure is not None:
		# Pressure has been specified
		pres = np.array(pressure, ndmin=1)
	else:
		# Use default atmospheric pressure
		pres = 1010.*(1.0-6.5/288000.0*obsalt)**5.255

	if not convert_to_observed:
		altout = old_alt - co_refract_forward(old_alt, pressure=pres, temperature=temper-273.15)
	else:
		# Convert from real to observed altitude
		altout = np.zeros(old_alt.size)
		for i in xrange(altout.size):
			dr = co_refract_forward(old_alt[i], pressure=pres[i], temperature=temper[i]-273.15)
			# Guess of observed location
			cur = old_alt[i] + dr
			while True:
				last = cur.copy()
				dr = co_refract_forward(cur, pressure=pres[i], temperature=temper[i]-273.15)
				cur = old_alt[i] + dr
				if np.abs(last - cur)*3600. < epsilon:
					break
			altout[i] = cur.copy()

	if full_output:
		return altout, pres, temper
	else:
		return altout
		
def eq2hor(jd, ra, dec, observatory=None, lon=None, lat=None, alt=None, B1950=False, doprecess=True, nutate=True, aberration=True, refract=True):
	"""
		Convert celestial coordinates (RA/DEC) to local horizon coordinates (ALT/AZ).
		
		This routine is typically accurate to about 1 arcsec.
		It considers Earth's precession, nutation, aberration,
		and refraction (if keywords are True).
		
		Parameters
		----------
		jd : float or array
				The Julian date(s)
		ra : float or array
				The right ascension in DEGREES.
		dec : float or array
				The declination in DEGREES.
		observatory : string, {HS}, optional
				A string identifying the observatory. If given,
				the observer's longitude, latitude, and altitude
				are set automatically (and must not be given
				separately then).
		lon : float
				 East longitude of the observer in DEGREES.
				 Specify West longitude with a negative sign.
				 Default is the longitude of the Hamburger Sternwarte.
		lat : float
				 Latitude of the observer in DEGREES.
				 Default is the latitude of the Hamburger Sternwarte.
		alt : float
				 Altitude of the observer in METER.
				 Default is the altitude of the Hamburger Sternwarte.
		B1950 : boolean, optional
				 If True, your RA and DEC coordinates are given for epoch B1950 FK4.
				 If False, RA and DEC are given for epoch J2000 FK5.
				 Default is FALSE.
		precess : boolean, optional
				 If True (default), Earth's precess motion is considered
				 in the calculations.
		nutate : boolean, optional
				 If True (default), Earth's nutation is considered
				 in the calculations.
		aberration : boolean, optional
				 If True (default), the annual aberration is considered
				 in the calculations.
		refraction : boolean, optional
				 If True, the atmospheric refraction is considered
				 in the calculations.
				 
		Returns
		-------
		Altitude : float or array
				The altitude in degrees.
		Azimuth : float or array
				The azimuth in degrees (measured East from North).
		Hour angle : float or array
				The hour angle in degrees.
	"""	
	
	lon = 254.180000305
	lat = 32.7899987793
	alt = 2798.0000000000
	
	jd_vals = np.array(jd, ndmin=1)
	ra_vals = np.array(ra, ndmin=1)
	dec_vals = np.array(dec, ndmin=1)

	# Precess coordinates to current date
	equinox_now = (jd_vals - 2451545.0)/365.25 + 2000.0
	
	if doprecess:
		if B1950:
			for i in xrange(ra_vals.size):
				ra_vals[i], dec_vals[i] = precess(ra_vals[i], dec_vals[i], 1950.0, equinox_now[i])
		else:
			# Now B2000 is expected
			for i in range(ra_vals.size):
				ra_vals[i], dec_vals[i] = precess(ra_vals[i], dec_vals[i], 2000.0, equinox_now[i])
				
	# Calculate NUTATION and ABERRATION Corrections to Ra-Dec
	dra1, ddec1, eps, d_psi, dump = co_nutate(jd_vals, ra_vals, dec_vals, full_output=True)
	dra2, ddec2 = co_aberration(jd_vals, ra_vals, dec_vals)

	# Make nutation and aberration corrections
	if nutate:
		ra_vals += dra1
		dec_vals += ddec1
	if aberration:
		ra_vals += dra2
		dec_vals += ddec2

	# Calculate LOCAL MEAN SIDEREAL TIME
	lmst = ct2lst(jd_vals, np.repeat(lon, jd_vals.size))
	# Convert LMST to degrees (btw, this is the RA of the zenith)
	lmst *= 15.0	 
	
	# Calculate local APPARENT sidereal time
	# add correction in degrees
	last = lmst + d_psi * np.cos(eps*np.pi/180.)

	# Find hour angle (in DEGREES)
	ha = last - ra_vals
	if ha.size == 1:
		if ha < 0: ha += 360.
	else:
		w = np.where(ha < 0)[0]
		if len(w) > 0: ha[w] += 360.
	
	ha = idlMod(ha, 360.)

	# Now do the spherical trig to get APPARENT alt,az.
	altaz = hadec2altaz(ha, dec_vals, np.ones(ha.size)*lat)

	# Make Correction for ATMOSPHERIC REFRACTION
	# (use this for visible and radio wavelengths; author is unsure about other wavelengths.
	#	See the comments in CO_REFRACT.pro for more details.)
	if refract:
		alts = np.repeat(alt, jd_vals.size)
		altitude = co_refract(altaz[0], observer_alt=alts, full_output=False, convert_to_observed=True)
	else:
		altitude = altaz[0]

	az = altaz[1]
	
	return altitude, az, ha

def sunpos(jd, end_jd=None, jd_steps=None, full_output=False):
	"""
		Compute right ascension and declination of the Sun at a given time.
		
		Parameters
		----------
		jd : float
				 The Julian date
		end_jd : float, optional
				 The end of the time period as Julian date. If given,
				 `sunpos` computes RA and DEC at `jd_steps` time points
				 between `jd` and ending at `end_jd`.
		jd_steps : integer, optional
				 The number of steps between `jd` and `end_jd`
				 for which RA and DEC are to be calculated.
		outfile : string, optional
				 If given, the output will be written to a file named according
				 to `outfile`.
		radian : boolean, optional
				 Results are returned in radian instead of in degrees.
				 Default is False.
		plot : boolean, optional
				 If True, the result is plotted.
		full_output: boolean, optional
				 If True, `sunpos`, additionally, returns the elongation and
				 obliquity of the Sun.

		Returns
		-------
		Time : array
				The JDs for which calculations where carried out.
		Ra : array
				Right ascension of the Sun.
		Dec : array
				Declination of the Sun.
		Elongation : array, optional
				Elongation of the Sun (only of `full_output`
				is set to True).
		Obliquity : array, optional
				Obliquity of the Sun (only of `full_output`
				is set to True).

		Notes
		-----
		
		.. note:: This function was ported from the IDL Astronomy User's Library.

		:IDL - Documentation:

		NAME:
					SUNPOS
		PURPOSE:
					To compute the RA and Dec of the Sun at a given date.
		
		CALLING SEQUENCE:
					SUNPOS, jd, ra, dec, [elong, obliquity, /RADIAN ]
		INPUTS:
					jd		- The Julian date of the day (and time), scalar or vector
									usually double precision
		OUTPUTS:
					ra		- The right ascension of the sun at that date in DEGREES
									double precision, same number of elements as jd
					dec	 - The declination of the sun at that date in DEGREES
		
		OPTIONAL OUTPUTS:
					elong - Ecliptic longitude of the sun at that date in DEGREES.
					obliquity - the obliquity of the ecliptic, in DEGREES
		
		OPTIONAL INPUT KEYWORD:
					/RADIAN - If this keyword is set and non-zero, then all output variables 
									are given in Radians rather than Degrees
		
		NOTES:
					Patrick Wallace (Rutherford Appleton Laboratory, UK) has tested the
					accuracy of a C adaptation of the sunpos.pro code and found the 
					following results.	 From 1900-2100 SUNPOS	gave 7.3 arcsec maximum 
					error, 2.6 arcsec RMS.	Over the shorter interval 1950-2050 the figures
					were 6.4 arcsec max, 2.2 arcsec RMS.	
		
					The returned RA and Dec are in the given date's equinox.
		
					Procedure was extensively revised in May 1996, and the new calling
					sequence is incompatible with the old one.
		METHOD:
					Uses a truncated version of Newcomb's Sun.		Adapted from the IDL
					routine SUN_POS by CD Pike, which was adapted from a FORTRAN routine
					by B. Emerson (RGO).
		EXAMPLE:
					(1) Find the apparent RA and Dec of the Sun on May 1, 1982
					
					IDL> jdcnv, 1982, 5, 1,0 ,jd			;Find Julian date jd = 2445090.5	 
					IDL> sunpos, jd, ra, dec
					IDL> print,adstring(ra,dec,2)
									 02 31 32.61	+14 54 34.9
		
					The Astronomical Almanac gives 02 31 32.58 +14 54 34.9 so the error
									in SUNPOS for this case is < 0.5".			
		
					(2) Find the apparent RA and Dec of the Sun for every day in 1997
		
					IDL> jdcnv, 1997,1,1,0, jd								;Julian date on Jan 1, 1997
					IDL> sunpos, jd+ dindgen(365), ra, dec		;RA and Dec for each day 
		
		MODIFICATION HISTORY:
					Written by Michael R. Greason, STX, 28 October 1988.
					Accept vector arguments, W. Landsman		 April,1989
					Eliminated negative right ascensions.	MRG, Hughes STX, 6 May 1992.
					Rewritten using the 1993 Almanac.	Keywords added.	MRG, HSTX, 
									10 February 1994.
					Major rewrite, improved accuracy, always return values in degrees
					W. Landsman	May, 1996 
					Added /RADIAN keyword,		W. Landsman			 August, 1997
					Converted to IDL V5.0	 W. Landsman	 September 1997
	"""
		
	if end_jd is None:
		# Form time in Julian centuries from 1900.0
		start_jd = (jd - 2415020.0)/36525.0
		# Zime array
		time = np.array([start_jd])
	else:
		# Form time in Julian centuries from 1900.0
		start_jd = (jd - 2415020.0)/36525.0
		end_jd = (end_jd - 2415020.0)/36525.0		
		# Time array
		timestep = (end_jd-start_jd)/float(jd_steps)
		time = np.arange(start_jd, end_jd, timestep)

	# Mean solar longitude
	sunlon = (279.696678 + idlMod( (36000.768925*time), 360.0) )*3600.0

	# Allow for ellipticity of the orbit (equation of center)
	# using the Earth's mean anomaly ME
	me = 358.475844 + idlMod( (35999.049750*time) , 360.0 )
	ellcor	= ( 6910.1 - 17.2*time ) * np.sin(me*np.pi/180.) + 72.3 * np.sin(2.0*me*np.pi/180.)
	sunlon += ellcor

	# Allow for the Venus perturbations using the mean anomaly of Venus MV
	mv = 212.603219 + idlMod( (58517.803875*time) , 360.0 )
	vencorr = 4.8 * np.cos( (299.1017 + mv - me)*np.pi/180. ) + \
						5.5 * np.cos( (148.3133 +	2.0 * mv	-	2.0 * me )*np.pi/180. ) + \
						2.5 * np.cos( (315.9433 +	2.0 * mv	-	3.0 * me )*np.pi/180. ) + \
						1.6 * np.cos( (345.2533 +	3.0 * mv	-	4.0 * me )*np.pi/180. ) + \
						1.0 * np.cos( (318.15	 +	3.0 * mv	-	5.0 * me )*np.pi/180. )
	sunlon += vencorr

	# Allow for the Mars perturbations using the mean anomaly of Mars MM
	mm = 319.529425	+ idlMod( (19139.858500*time)	, 360.0 )
	marscorr = 2.0 * np.cos( (343.8883 -	2.0 * mm	+	2.0 * me)*np.pi/180. ) + \
						1.8 * np.cos( (200.4017 -	2.0 * mm	+ me)*np.pi/180. )
	sunlon += marscorr

	# Allow for the Jupiter perturbations using the mean anomaly of Jupiter MJ
	mj = 225.328328	+ idlMod( (3034.6920239*time) , 360.0 )
	jupcorr = 7.2 * np.cos( (179.5317 - mj + me )*np.pi/180. ) + \
						2.6 * np.cos( (263.2167 -	mj )*np.pi/180. ) + \
						2.7 * np.cos( ( 87.1450 -	2.0 * mj	+	2.0 * me )*np.pi/180. ) + \
						1.6 * np.cos( (109.4933 -	2.0 * mj	+	me )*np.pi/180. )
	sunlon += jupcorr

	# Allow for the Moon's perturbations using the mean elongation of
	# the Moon from the Sun D
	d = 350.7376814 + idlMod( (445267.11422*time) , 360.0 )
	mooncorr	= 6.5*np.sin(d*np.pi/180.)
	sunlon += mooncorr

	# Allow for long period terms
	longterm	= 6.4*np.sin( (231.19 + 20.20*time)*np.pi/180. )
	sunlon += longterm
	sunlon = idlMod( ( sunlon + 2592000.0 ) , 1296000.0 )
	longmed = sunlon/3600.0

	# Allow for Aberration
	sunlon -=	20.5

	# Allow for Nutation using the longitude of the Moons mean node OMEGA
	omega = 259.183275 - idlMod( (1934.142008*time) , 360.0 )
	sunlon = sunlon - 17.2*np.sin(omega*np.pi/180.)

	# Calculate the True Obliquity
	oblt = 23.452294 - 0.0130125*time + ( 9.2*np.cos(omega*np.pi/180.) )/3600.0

	# Right Ascension and Declination
	sunlon /= 3600.0
	ra = np.arctan2( np.sin(sunlon*np.pi/180.) * np.cos(oblt*np.pi/180.), np.cos(sunlon*np.pi/180.) )

	neg = np.where(ra < 0.0)[0]
	nneg = len(neg)
	if nneg > 0: ra[neg] += 2.0*np.pi

	dec = np.arcsin( np.sin(sunlon*np.pi/180.) * np.sin(oblt*np.pi/180.) )

	ra /= (np.pi/180.)
	dec /= (np.pi/180.)

	jd = time*36525.0 + 2415020.0

	if full_output:
		return jd, ra, dec, longmed, oblt
	else:
		return jd, ra, dec
	
def moonpos(jd, radian=False):

	jd = np.array(jd, ndmin=1)
	time = (jd - 2451545.0)/36525.0
	d_lng = np.array([0,2,2,0,0,0,2,2,2,2,0,1,0,2,0,0,4,0,4,2,2,1,1,2,2,4,2,0,2,2,1,2,0,0, \
					 2,2,2,4,0,3,2,4,0,2,2,2,4,0,4,1,2,0,1,3,4,2,0,1,2,2])
	m_lng = np.array([0,0,0,0,1,0,0,-1,0,-1,1,0,1,0,0,0,0,0,0,1,1,0,1,-1,0,0,0,1,0,-1,0, \
					 -2,1,2,-2,0,0,-1,0,0,1,-1,2,2,1,-1,0,0,-1,0,1,0,1,0,0,-1,2,1,0,0])
	mp_lng = np.array([1,-1,0,2,0,0,-2,-1,1,0,-1,0,1,0,1,1,-1,3,-2,-1,0,-1,0,1,2,0,-3,-2, \
						-1,-2,1,0,2,0,-1,1,0,-1,2,-1,1,-2,-1,-1,-2,0,1,4,0,-2,0,2,1,-2,-3,2,1,-1,3,-1])
	f_lng = np.array([0,0,0,0,0,2,0,0,0,0,0,0,0,-2,2,-2,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0, \
					 0,0,0,-2,2,0,2,0,0,0,0,0,0,-2,0,0,0,0,-2,-2,0,0,0,0,0,0,0,-2])
	sin_lng = np.array([6288774,1274027,658314,213618,-185116,-114332,58793,57066,53322, \
						 45758,-40923,-34720,-30383,15327,-12528,10980,10675,10034,8548,-7888,-6766, \
						 -5163,4987,4036,3994,3861,3665,-2689,-2602,2390,-2348,2236,-2120,-2069,2048, \
						 -1773,-1595,1215,-1110,-892,-810,759,-713,-700,691,596,549,537,520,-487, \
						 -399,-381,351,-340,330,327,-323,299,294,0.0])
	cos_lng = np.array([-20905355,-3699111,-2955968,-569925,48888,-3149,246158,-152138, \
						 -170733,-204586,-129620,108743,104755,10321,0,79661,-34782,-23210,-21636, \
						 24208,30824,-8379,-16675,-12831,-10445,-11650,14403,-7003,0,10056,6322, \
						 -9884,5751,0,-4950,4130,0,-3958,0,3258,2616,-1897,-2117,2354,0,0,-1423, \
						 -1117,-1571,-1739,0,-4421,0,0,0,0,1165,0,0,8752.0])
	d_lat = np.array([0,0,0,2,2,2,2,0,2,0,2,2,2,2,2,2,2,0,4,0,0,0,1,0,0,0,1,0,4,4,0,4,2,2, \
										2,2,0,2,2,2,2,4,2,2,0,2,1,1,0,2,1,2,0,4,4,1,4,1,4,2])
	m_lat = np.array([0,0,0,0,0,0,0,0,0,0,-1,0,0,1,-1,-1,-1,1,0,1,0,1,0,1,1,1,0,0,0,0,0,0, \
										0,0,-1,0,0,0,0,1,1,0,-1,-2,0,1,1,1,1,1,0,-1,1,0,-1,0,0,0,-1,-2])
	mp_lat = np.array([0,1,1,0,-1,-1,0,2,1,2,0,-2,1,0,-1,0,-1,-1,-1,0,0,-1,0,1,1,0,0,3,0, \
										-1,1, -2,0,2,1,-2,3,2,-3,-1,0,0,1,0,1,1,0,0,-2,-1,1,-2,2,-2,-1,1,1,-1,0,0])
	f_lat = np.array([ 1,1,-1,-1,1,-1,1,1,-1,-1,-1,-1,1,-1,1,1,-1,-1,-1,1,3,1,1,1,-1,-1,-1, \
										 1,-1,1,-3,1,-3,-1,-1,1,-1,1,-1,1,1,1,1,-1,3,-1,-1,1,-1,-1,1,-1,1,-1,-1, \
										-1,-1,-1,-1,1])
	sin_lat = np.array([5128122,280602,277693,173237,55413,46271,32573,17198,9266,8822, \
											8216,4324,4200,-3359,2463,2211,2065,-1870,1828,-1794,-1749,-1565,-1491, \
											-1475,-1410,-1344,-1335,1107,1021,833,777,671,607,596,491,-451,439,422, \
											421,-366,-351,331,315,302,-283,-229,223,223,-220,-220,-185,181,-177,176, \
											166,-164,132,-119,115,107.0])

	# Mean longitude of the moon referred to mean equinox of the date
	coeff0 = [-1.0/6.5194e7, 1.0/538841.0, -0.0015786, 481267.88123421, 218.3164477]
	lprimed = np.polyval(coeff0, time)*np.pi/180.
	lprimed = cirrange(lprimed, radians=True)
	
	# Mean elongation of the Moon
	coeff1 = [-1.0/1.13065e8, 1.0/545868.0, -0.0018819, 445267.1114034, 297.8501921]
	d = np.polyval(coeff1, time)*np.pi/180.
	d = cirrange(d, radians=True)

	# Sun's mean anomaly
	coeff2 = [1.0/2.449e7, -0.0001536, 35999.0502909, 357.5291092]
	M = np.polyval(coeff2, time)*np.pi/180.
	M = cirrange(M, radians=True)
	
	# Moon's mean anomaly
	coeff3 = [-1.0/1.4712e7, 1.0/6.9699e4, 0.0087414, 477198.8675055, 134.9633964]
	Mprime = np.polyval(coeff3, time)*np.pi/180.
	Mprime = cirrange(Mprime, radians=True)

	# Moon's argument of latitude
	coeff4 = [1.0/8.6331e8, -1.0/3.526e7, -0.0036539, 483202.0175233, 93.2720950]
	F = np.polyval(coeff4, time)*np.pi/180.
	F = cirrange(F, radians=True)

	# Eccentricity of Earth's orbit around the Sun
	E = 1 - 0.002516*time - 7.4e-6*time**2
	E2 = E**2
	ecorr1 = np.where(np.abs(m_lng) == 1)[0]
	ecorr2 = np.where(np.abs(m_lat) == 1)[0]
	ecorr3 = np.where(np.abs(m_lng) == 2)[0]
	ecorr4 = np.where(np.abs(m_lat) == 2)[0]

	# Additional arguments
	A1 = (119.75 + 131.849*time) * np.pi/180.
	A2 = (53.09 + 479264.290*time) * np.pi/180.
	A3 = (313.45 + 481266.484*time) * np.pi/180.
	suml_add = 3958.*np.sin(A1) + 1962.*np.sin(lprimed - F) + 318.*np.sin(A2)
	sumb_add =	-2235.*np.sin(lprimed) + 382.*np.sin(A3) + 175.*np.sin(A1-F) + \
							175.*np.sin(A1 + F) + 127.*np.sin(lprimed - Mprime) - 115.*np.sin(lprimed + Mprime)

	# Sum the periodic terms 
	geolong = np.zeros(jd.size)
	geolat = np.zeros(jd.size)
	dis = np.zeros(jd.size)

	for i in xrange(jd.size):
		sinlng = sin_lng.copy()
		coslng = cos_lng.copy()
		sinlat = sin_lat.copy()

		sinlng[ecorr1] = E[i]*sinlng[ecorr1]
		coslng[ecorr1] = E[i]*coslng[ecorr1]
		sinlat[ecorr2] = E[i]*sinlat[ecorr2]
		sinlng[ecorr3] = E2[i]*sinlng[ecorr3]
		coslng[ecorr3] = E2[i]*coslng[ecorr3]
		sinlat[ecorr4] = E2[i]*sinlat[ecorr4]

		arg = d_lng*d[i] + m_lng*M[i] +mp_lng*Mprime[i] + f_lng*F[i]
		geolong[i] = lprimed[i]/(np.pi/180.) + ( np.sum( sinlng*np.sin(arg) ) + suml_add[i] )/1.0e6

		dis[i] = 385000.56 + np.sum( coslng*np.cos(arg) )/1.0e3

		arg = d_lat*d[i] + m_lat*M[i] +mp_lat*Mprime[i] + f_lat*F[i]
		geolat[i] = ( np.sum( sinlat*np.sin(arg) ) + sumb_add[i] )/1.0e6

	# Find the nutation in longitude
	nut = nutate(jd)
	nlong = nut[0]
	elong = nut[1]
	geolong += nlong
	geolong = geolong*np.pi/180.		
	geolong = cirrange(geolong, radians=True)		
	
	lamb = geolong.copy()
	beta = geolat*np.pi/180.
	geolong = geolong/(np.pi/180.)
	
	# Find mean obliquity and convert lambda,beta to RA, Dec 
	c = np.array([21.448,-4680.93,-1.55,1999.25,-51.38,-249.67,-39.05,7.12,27.87,5.79,2.45])
	c = c[::-1]	
	epsilon = 23. + 26./60. + np.polyval(c, time/1.0e2)/3600.0
	eps = ( epsilon + elong )*np.pi/180. # True obliquity in radians

	ra = np.arctan2( np.sin(lamb)*np.cos(eps) - np.tan(beta)*np.sin(eps), np.cos(lamb) )
	ra = cirrange(ra, radians=True) 
	dec = np.arcsin( np.sin(beta)*np.cos(eps) + np.cos(beta)*np.sin(eps)*np.sin(lamb) )

	if not radian:
		ra = ra/(np.pi/180.)
		dec = dec/(np.pi/180.)
	else:
		geolong = lamb
		geolat = beta

	return ra[0], dec[0], dis, geolong, geolat
	
def moonphase(jd):
  """
    Computes the illuminated fraction of the Moon at given Julian date(s).
    
    Parameters
    ----------
    jd : float or array
         The Julian date.
         
    Returns
    -------
    Fraction : float or array
        The illuminated fraction [0 - 1] of the Moon.
        Has the same size as `jd`.

    Notes
    -----
    
    .. note:: This function was ported from the IDL Astronomy User's Library.

    :IDL - Documentation:  
    
    NAME:
          MPHASE
    PURPOSE:
          Return the illuminated fraction of the Moon at given Julian date(s) 
    
    CALLING SEQUENCE:
          MPHASE, jd, k
    INPUT:
          JD - Julian date, scalar or vector, double precision recommended
    OUTPUT:
          k - illuminated fraction of Moon's disk (0.0 < k < 1.0), same number
              of elements as jd.   k = 0 indicates a new moon, while k = 1 for
              a full moon.
    EXAMPLE:
          Plot the illuminated fraction of the moon for every day in July 
          1996 at 0 TD (~Greenwich noon).
    
          IDL> jdcnv, 1996, 7, 1, 0, jd         ;Get Julian date of July 1
          IDL> mphase, jd+dindgen(31), k        ;Moon phase for all 31 days
          IDL> plot, indgen(31),k               ;Plot phase vs. July day number
  """

  jd = np.array(jd, ndmin=1)
  
  # Earth-Sun distance (1 AU)
  edist = 1.49598e8         
  
  mpos = moonpos(jd)
  ram = mpos[0]*np.pi/180.
  decm = mpos[1]*np.pi/180.
  dism = mpos[2]
  
  spos = sunpos(jd)
  ras = spos[1]*np.pi/180.
  decs = spos[2]*np.pi/180.

  phi = np.arccos( np.sin(decs)*np.sin(decm) + np.cos(decs)*np.cos(decm)*np.cos(ras-ram) )
  inc = np.arctan2( edist * np.sin(phi), dism - edist*np.cos(phi) )
  k = (1 + np.cos(inc))/2.
  
  return np.ravel(k)
