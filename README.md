# honeycomb
A python CLI tool used to generate and publish AGRC base maps including:
- raster tile cache generation
- uploading raster tiles to GCP for use with discover.agrc.utah.gov
- vector tile cache generation
- uploading vector tiles to AGOL

This is an effort to polish/standardize/automate a mishmash of stand-alone python scripts currently used to update base maps.

# Installation
1. Clone repository to local folder.
1. Update `src/honeycomb/settings/__init__.py` with the secret values.
1. From project folder base:
`pip install . --upgrade`

# Usage
Run `honeycomb` to see the help for this tool.

# Development
### Linting
`flake8 src/honeycomb/ tests`

### Unit Tests
Test dependencies: `pip install nose nose-cov rednose mock`
`python -m nose --with-id --rednose --cov-config .coveragerc --with-coverage --cover-package honeycomb --cov-report term-missing --cover-erase`

### Running Source Version
From `src` directory: `python -m honeycomb <...>`
