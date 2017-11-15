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
