##### SDSS-IV AUTOSCHEDULER #####




### Running the Autoscheduler (for simulations)

[1] Before you run the autoscheduler, set the run parameters in the set_params.pro program. Here you will find the option to change filenames for input files such as the schedule file and plate lists.

[2a] Once the parameters are set, you may run the scheduler by calling the IDL routine from the command line:
		idl -e s4scheduler

[2b] The scheduler is also able to run in "LST mode", where it will determine the LST distribution for the current schedule without simulating picking + observing plates. You can run the scheduler in this mode by passing it an argument:
		idl -e s4scheduler -args lst
		







### Output Files
The autoscheduler will output many files to summarize its run (which all live in the output folder), but currently there are no header rows. Below are the descriptions of all columns in the output files.

"timedata.txt"
	Top section shows break-up of time:
		Assigned = amount of hours for each survey summing up from the input schedule
		On-Sky = amount of hours for each survey after blocking out the night within the scheduler
		Weather = amount of hours for each survey that is lost to weather
	Bottom section shows how many 15-minute slots are lost due to cart limitations for MaNGA
	
"carts.txt"
	Count of nights where certain numbers of carts are staged by specific surveys (or combinations of surveys)

"LSThrs.txt"
	[LST]   [Planned APOGEE-II hours]   [Planned MaNGA hours]   [Planned eBOSS hours]   [Missed APOGEE-II hours]   [Missed MaNGA hours]  [Missed eBOSS hours]
	--- Here "missed" means blocks of the night that are missed due to not having a plate available. eBOSS's hours are pre-scaled by weather, APOGEE-II and MaNGA's are not.
	
"apogee.txt"
	[Field Name]  [RA]  [Dec]  [PlateID]  [Version Number]  [Drilled HA]  [Manual Priority]  [# Visits Needed]  [# Visits Completed]  [S/N]  [Minimum HA]  [Maximum HA]  [Internal Priority]  [Observation History]
	
"manga.txt"
	[PlateID]  [RA]  [Dec]  [Drilled HA]  [Manual Priority]  [# Dither Sets Completed]  [# Visits Completed]  [Blue Chip S/N]  [Red Chip S/N]  [Minimum HA]  [Maximum HA]  [Internal Priority]  [# Times Unplugged]  [Observation History]
	--- Observation history shows the MJD of the observation, and the # of completed dithers on that night
	
"eboss.txt"
	[PlateID]  [RA]  [Dec]  [Drilled HA]  [Manual Priority]  [# Visits Completed]  [Blue Chip S/N]  [Red Chip S/N]  [Minimum HA]  [Maximum HA]  [Internal Priority]  [# Times Unplugged]  [Observation History]
	

