# honeycomb
A python CLI tool used to generate and publish AGRC base maps including:
- raster tile cache generation
- uploading raster tiles to GCP for use with discover.agrc.utah.gov
- vector tile cache generation
- uploading vector tiles to AGOL

# Usage
TODO

# Installation
TODO

# Tests
### Linting
`flake8 src/honeycomb/ tests`

### Unit Tests
`nosetests --with-id --rednose --cov-config .coveragerc --with-coverage --cover-package honeycomb --cov-report term-missing --cover-erase`
