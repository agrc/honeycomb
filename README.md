# honeycomb
A python CLI tool used to generate and publish AGRC base maps including:
- raster tile cache generation
- uploading raster tiles to GCP for use with discover.agrc.utah.gov
- vector tile cache generation
- uploading vector tiles to AGOL

# Usage
TODO

# Installation
From project folder base:
`pip install . --upgrade`

# Tests
### Linting
`flake8 src/honeycomb/ tests`

### Unit Tests
Test dependencies: `pip install nose nose-cov rednose mock`
`python -m nose --with-id --rednose --cov-config .coveragerc --with-coverage --cover-package honeycomb --cov-report term-missing --cover-erase`
