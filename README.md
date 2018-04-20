# honeycomb
[![Build Status](https://travis-ci.org/agrc/honeycomb.svg?branch=master)](https://travis-ci.org/agrc/honeycomb)
[![codecov](https://codecov.io/gh/agrc/honeycomb/branch/master/graph/badge.svg)](https://codecov.io/gh/agrc/honeycomb)

A python CLI tool used to generate and publish AGRC base maps including:
- raster tile cache generation
- uploading raster tiles to GCP for use with discover.agrc.utah.gov
- vector tile cache generation
- uploading vector tiles to AGOL

This is an effort to polish/standardize/automate a mishmash of stand-alone python scripts currently used to update base maps.

# Installation
1. Install [`gcloud`](https://cloud.google.com/sdk/docs/)
    - Do *not* include the bundled python.
1. Install [`crcmode`](https://cloud.google.com/storage/docs/gsutil/addlhelp/CRC32CandInstallingcrcmod).
1. Clone repository to local folder.
1. From project folder base:
`pip install . --upgrade` (make sure that you install into the 32bit version of python (required for crcmode))
1. Add the following environmental variables:

| Name | Description | Example |
| --- | --- | --- |
| `HONEYCOMB_HNAS` | the DNS name for HNAS | some.dns.name |
| `HONEYCOMB_SMTP_SERVER` | your smtp server | send.yourdomain.com |
| `HONEYCOMB_SMTP_PORT` | your smtp port | 25 |
| `HONEYCOMB_AGS_SERVER` | your ArcGIS server url | http://localhost:6080/arcgis/admin |
| `HONEYCOMB_AGS_USERNAME` | your ArcGIS Server username | name |
| `HONEYCOMB_AGS_PASSWORD` | your ArcGIS Server password | password |
1. Run `honeycomb config open`. This will initialize your config with default values and open it in your text editor.

# Usage
Run `honeycomb -help` to see documentation for the various commands.

# Config file
Run `honeycomb config open` to open the config file.

| Property | Description |
| --- | --- |
| `basemaps` | Object defining the registered base maps. Use the cli to manage this list.
| `configuration` | Affects a few code paths for differences between production and development. Possible values: `prod` and `dev` (default).
| `notify` | A list of email addresses to whom honeycomb sends status updates.
| `sendEmails` | A boolean that determines whether emails are actually sent or not. Useful during development.
| `num_processes` | A number that indicates the maximum number of parallel processes to use when uploading files to GCP.

# Development
### Unit Tests & Linting
`arcpy` is mocked for the tests so this should all work without it.

Install test dependencies: `pip install ".[test]" --upgrade`

Running tests/linting: `pytest` or `ptw` to automatically run tests on file changes.

### Running Source Version
From `root` directory: `python -m honeycomb <...>`

# Changelog
#### v1.1.1 - 1/8/2018
- fix issue with vector_py3 trying to import py2 arcpy

#### v1.1.0 - 1/8/2018
- glob - iglob to help with memory usage
- new commands: publish, vector
- other minor bug fixes and clean up

#### v1.0.0 - 11/2/2017
Initial release
