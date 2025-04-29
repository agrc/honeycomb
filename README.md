# honeycomb

[![Build Status](https://travis-ci.org/agrc/honeycomb.svg?branch=master)](https://travis-ci.org/agrc/honeycomb)
[![codecov](https://codecov.io/gh/agrc/honeycomb/branch/master/graph/badge.svg)](https://codecov.io/gh/agrc/honeycomb)

A python CLI tool used to generate and publish AGRC base maps including:

- raster tile cache generation
- uploading raster tiles to GCP for use with discover.agrc.utah.gov
- vector tile cache generation
- uploading vector tiles to AGOL

This is an effort to polish/standardize/automate a mishmash of stand-alone python scripts currently used to update base maps.

## Installation

\*_not required for data-update command only installation_

1. Install ArcGIS Pro (Standard license level or higher)
1. Create new python conda environment and activate
1. `conda create --name honeycomb python=3.11`
1. `conda activate honeycomb`
1. `conda install arcpy -c esri`
1. Clone repository to local folder.
1. From project folder base:
   `pip install -e . --upgrade`
1. From forklift folder (`C:\dev\forklift`):
   `pip install . --upgrade`
1. Add the following environmental variables:

| Name                                     | Description                                                    | Example                                                                                                                                  |
| ---------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `HONEYCOMB_SHARE`                        | the to the share folder used to share mxd's and data with Zach | \\999.99.99.99\agrc\caching                                                                                                              |
| `HONEYCOMB_SENDGRID_API_KEY`             | your sendgrid api key                                          | SG.1234567890                                                                                                                            |
| `HONEYCOMB_GIZA_USERNAME`\*              | your Giza (discover) username                                  | name                                                                                                                                     |
| `HONEYCOMB_GIZA_PASSWORD`\*              | your Giza (discover) password                                  | password                                                                                                                                 |
| `HONEYCOMB_AGOL_USERNAME`\*              | your AGOL username                                             | name                                                                                                                                     |
| `HONEYCOMB_AGOL_PASSWORD`\*              | your AGOL password                                             | password                                                                                                                                 |
| `HONEYCOMB_INTERNAL_CONNECTION_STRING`\* | the connection string to the internal database                 | DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=<host>,1433;DATABASE=<database>;UID=<username>;PWD=<password>;TrustServerCertificate=yes |

1. Run `honeycomb config open`. This will initialize your config with default values and open it in your text editor.
1. Set map services to be dedicated instances with a min of 0 to prevent schema locks when updating the data.

## Usage

Run `honeycomb -help` to see documentation for the various commands.

## Config file

Run `honeycomb config open` to open the config file.

| Property        | Description                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `basemaps`      | Object defining the registered base maps. Use the cli to manage this list.                                                |
| `configuration` | Affects a few code paths for differences between production and development. Possible values: `prod` and `dev` (default). |
| `notify`        | A list of email addresses to whom honeycomb sends status updates.                                                         |
| `sendEmails`    | A boolean that determines whether emails are actually sent or not. Useful during development.                             |

## Adding a New Layer

1. Add the new layer to your local file geodatabase (`C:\Cache\MapData\SGID10_WGS.gdb`).
1. Add the new layer to the appropriate map in the pro project on the share.
1. The next time that honeycomb runs, it will pull the new layer to the caching machine.

## Development

### Unit Tests & Linting

`arcpy` is mocked for the tests so this should all work without it.

Install test dependencies: `pip install ".[test]" --upgrade`

Running tests/linting: `pytest` or `ptw` to automatically run tests on file changes.

### Running Source Version

From `root` directory: `python -m honeycomb <...>`

## Compute Instance Group

This project is run via a spot VM within a compute engine instance group. Any time there are updates made to the OS or applications, use [this script](scripts/update_compute_group_template.sh) to update the instance template.
