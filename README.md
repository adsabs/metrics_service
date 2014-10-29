Start with

	python api.py
  
and do a request from the command line like so

	curl -H "Content-Type: application/json" -X POST -d '{"bibcodes":["1980ApJS...44..137K","1980ApJS...44..489B"]}' http://localhost:5000/metrics

and you should get back metrics data.
