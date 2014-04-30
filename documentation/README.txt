==== HOW TO RUN ====
The autoscheduler can be run in two ways: on the command line, or through a web API interface.

---- Command Line
To run the autoscheduler from the command line, you'll have to run the following commands within python:

	import s4as
	s4as.run_scheduler()
	
The scheduler will return a dict having the specifications listed in 'autoscheduler diagram.pdf'


---- Web API
To start the autoscheduler flask application, run the following from the command line:

	python run_scheduler_web.py --debug -r
	
This wil start the API on port 16100.

