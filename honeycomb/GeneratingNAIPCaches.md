# Generating NAIP Caches

## Notes

Using "c2-standard-16 (16 vCPUs, 64 GB Memory)" it took about ?? days to process and upload each layer.

5TB should be enough to hold the source raster mosaics and all of the intermediary data for this process.

Cache levels 0-18 for the entire project extent. A boundary can be obtained from one of the raster mosaics.

## Steps

1. Provision a new 5TB disk and attach it to the honeycomb instance. You will likely need to do this via a new template.
1. Create new buckets for the NAIP caches in the Utah Imagery project.
1. Upload the raster mosaics to a bucket in the honeycomb project.
1. Download the raster mosaics from the bucket to the newly attached disk.
1. Run "Analyze Mosaic Dataset" and fix any issues that are identified.
1. Open the "Maps.aprx" project and repoint the RGB and NRG maps to the new mosaics.
1. Within the Mosaic Layer ribbon, turn on DRA (Dynamic Range Adjustment), select custom stretch type, and then turn off DRA.
1. Update the `RGB` and `NRG` configs in `config.json` with the appropriate bucket and cache directory settings.
1. Run a test cache to ensure everything is working correctly using the something like the following command. We don't want to worry about creating test buckets so we use the `--test-extent` parameter to cache the test extent to the production bucket:

```bash
honeycomb RGB --skip-update --skip-test --levels=0-18 --cache-extent="C:\dev\honeycomb\honeycomb\data\Extents.geodatabase\main.test_extent"
```

1. Once you are happy with the results, cache the full extent using the following command:

```bash
honeycomb RGB --skip-update --skip-test --levels=0-18 --cache-extent="C:\Cache\MapData\NAIP_Extents.gdb\NAIP2024_Extent"
```
