# Metrics stubdata and expected results creation (unittests)

This directory contains the following files

  - <bibcode>.json
  - expected_results
  - make_stubdata.py
  
The files "*<bibcode>.json*" contain the data to define the mock response for database requests to the metrics database. The file "*expected_results*" contains a JSON document that contains the metrics results that are supposed to be returned by the data contained in the files "<bibcode>.json". The script "*make_stubdata.py*" creates the formentioned files. In this script, the data contained in the section *DATA SECTION* is everything that is needed to create the subdata files and expected results. The script itself is amply documented and should be self-explanatory.
