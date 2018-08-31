
### 1.0.32
 
* Recovered missing requirement

### 1.0.31
 
* Removed unnecessary requirements

### 1.0.30
 
* Updated adsmutils requirement

### 1.0.29
 
* Enabled JSON stdout logging and HTTP connection pool

### 1.0.28

* Execute SQL query in models now uses fetchall(), more efficient and less prone 
  to database connection errors than building an array with an inner loop (which
  may use fetchone() many times)

### 1.0.27

* Minor code cleanup / profiler fix

### 1.0.26

* requirements.txt update: version specification for adsmutils

### 1.0.25

* Bug fix: calculation of h and g in time series

### 1.0.24

* maintenance update

### 1.0.23

* ADS microservice normalization: implementation adsmutils, py.test

### 1.0.22

* alembic fix (env.py) and default values for some db columns

### 1.0.21

* Alembic update and db model unittest fix

### 1.0.20

* requirements.txt update and some cleanup

### 1.0.19

* include list of self-citations in output

### 1.0.18

* timeout decorator is not threadsafe 

### 1.0.17

* force timeout on tori

### 1.0.16

* SQLALCHEMY_COMMIT_ON_TEARDOWN = True (in config)

### 1.0.15

* bug fix in time series

### 1.0.14

* add profiling command to manage.py

### 1.0.13

* removed Consul dependencies

### 1.0.12

* update of database connection handling (Github issue 96)

### 1.0.11

* now log a warning when skipped bibcodes are found

### 1.0.10

* update of logfile name, making use of ENVIRONMENT variable

### 1.0.9

* bug fix (Github issue 91, wrong time normalization riq)

### 1.0.8

* update for "simple" metrics

### 1.0.7

* allow larger input sets for simple metrics

### 1.0.6

* cleanup of and comments in config module

### 1.0.5

* fixed POST output for single bibcode (metrics_service Github issue 81)

### 1.0.4

* fixed anomalies when all papers are from the future (next year)

### 1.0.3

* fixed calculation of READ10 indicator (metrics_service Github issue 76)

### 1.0.2

* add logging

### 1.0.1

* Add AUTHOR.md, CONTRIBUTING.md, CHANGES.md
* Fix Github issue 548 (Bumblebee repo): all citation histograms have same year range

### 1.0.0

* Operational release as of July 2015
