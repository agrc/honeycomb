# Generating NAIP Caches

## Notes
Used a compute optimized machine with 60 cores and 260 GB of ram. With these specs, it took about 24 hours to process and upload a layer.

5TB should be enough to hold the source raster mosaics and all of the intermediary data for this process.

Cache levels 0-18 for the entire project extent. A boundary can be obtained from one of the raster mosaics.

## Steps
1. `python cache_imagery.py`
1. Run the "Export Tile Cache" tool via the Pro UI. It has a bug that prevents us from using it via a script.
1. `python update_image_format.py`
1. `honeycomb upload RGB`
