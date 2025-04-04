#!/usr/bin/env python
# * coding: utf8 *
"""
honeycomb 🐝  # NOQA

Usage:
    honeycomb config init
    honeycomb config set --key <key> --value <value>
    honeycomb config basemaps --add <basemap> [<bucket-name>] [--loop]
    honeycomb config basemaps --remove <basemap>
    honeycomb config open
    honeycomb cleanup
    honeycomb update-data [--static-only] [--sgid-only] [--external-only] [--dont-wait]
    honeycomb loop
    honeycomb upload <basemap>
    honeycomb stats
    honeycomb resume
    honeycomb vector <basemap> [--skip-update]
    honeycomb vector-all [--skip-update]
    honeycomb <basemap> [--missing-only] [--skip-update] [--skip-test] [--spot <path>] [--levels <levels>] [--dont-wait]

Arguments:
    -h --help               Show this screen.
    basemap                 The name of a registered base map (e.g. Terrain).
    bucket-name             The name of the GCP bucket were you want the tiles to be pushed to.
    --loop                  Include the base map in the loop command.
    --missing-only          Only missing tiles are generated.
    --skip-update           Skip update vector data from SGID.
    --skip-test             Skip running a test cache.
    --spot <path>           Cache only a specific extent. <path> is a path to a polygon feature class.
    --levels <levels>       Cache only specific levels
    --static-only           Copy static data from the SHARE to your local machine.
    --sgid-only             Copy vector data from the SGID to your local machine.
    --dont-wait             Don't wait until evening to get updated data from internal.

Examples:
    honeycomb config init                                       Create a default config file.
    honeycomb config set --key sendEmails --value True          Write a value for a specific key to the config file.
    honeycomb config basemaps --add Terrain                     Adds "Terrain" to the "basemaps" array in the config file.
    honeycomb config basemaps --remove Terrain                  Removes "Terrain" from the "basemaps" array in the config file.
    honeycomb config open                                       Opens the config file in your default editor.
    honeycomb update-data                                       Refreshes the data on your computer from SGID and the static data on the share.
    honeycomb update-data --static-only                         Refreshes the data on your computer from the static data on the share only.
    honeycomb loop                                              Kicks off the honeycomb process and loops through all of the base maps.
    honeycomb upload Terrain                                    ETLs and uploads the tiles for the Terrain cache to GCP.
    honeycomb Terrain                                           Builds a single base map and pushes to GCP.
    honeycomb Terrain --skip-update                             Builds a single base map (skipping data update) and pushes to GCP.
    honeycomb Terrain --skip-test --spot C:\\\\test.gdb\\extent Builds a single base map (skipping test and for a specific extent) and pushes to GCP.
    honeycomb Terrain --levels 5-7                              Builds a single base map for levels 5, 6 & 7 and pushes to GCP.
    honeycomb vector UtahAddressPoints                          Builds a new vector tile package and uploads to AGOL.
    honeycomb vector-all                                        Builds all of the vector tile packages in the config and uploads to AGOL.
    honeycomb resume                                            Resume a previously started cache job.
    honeycomb cleanup                                           Deletes all of the local tiles for all of the basemaps.
"""

import json
import sys
from datetime import datetime
from os import startfile

from docopt import docopt

from . import cleanup, config, stats, update_data, vector
from .log import logger
from .messaging import send_email
from .resumable import (
    finish_job,
    get_current_job,
    get_job_status,
    start_new_job,
    update_job,
)
from .swarm import swarm
from .worker_bee import WorkerBee


def main():
    args = docopt(__doc__, version="1.1.1")

    def cache(
        basemap,
        missing_only=False,
        skip_update=False,
        skip_test=False,
        spot=False,
        levels=False,
        is_resumed_job=False,
        dont_wait=False,
    ):
        if not is_resumed_job:
            start_new_job(basemap, missing_only, skip_update, skip_test, spot, levels)
            stats.record_start(basemap, "cache")

        if not is_resumed_job or get_job_status("caching_complete") is False:
            if is_resumed_job:
                missing_only = True
            WorkerBee(
                basemap, missing_only, skip_update, skip_test, spot, levels, dont_wait
            )
            stats.record_finish(basemap, "cache")
            update_job("caching_complete", True)

        upload(basemap)

        finish_job()

    def upload(basemap):
        basemap_info = config.get_basemap(basemap)
        stats.record_start(basemap, "upload")
        swarm(basemap, basemap_info["bucket"], basemap_info["imageType"])
        stats.record_finish(basemap, "upload")

    if args["config"]:
        if args["init"]:
            logger.info("config file: {}".format(config.create_default_config()))
        elif args["set"] and args["<key>"] and args["<value>"]:
            logger.info(config.set_config_prop(args["<key>"], args["<value>"]))
        elif args["basemaps"] and args["<basemap>"]:
            if args["--add"]:
                logger.info(
                    config.add_basemap(
                        args["<basemap>"], args["<bucket-name>"], args["--loop"]
                    )
                )
            elif args["--remove"]:
                logger.info(config.remove_basemap(args["<basemap>"]))
        elif args["open"]:
            startfile(config.config_location)
    elif args["update-data"]:
        update_data.main(
            args["--static-only"],
            args["--sgid-only"],
            args["--external-only"],
            args["--dont-wait"],
        )
    elif args["upload"] and args["<basemap>"]:
        upload(args["<basemap>"])
    elif args["loop"]:
        stop = False
        basemaps = config.get_config_value("basemaps")
        while not stop:
            for basemap in [
                key for key in list(basemaps.keys()) if basemaps[key]["loop"]
            ]:
                action = input(
                    "cache {} (C), skip to the next base map (S) or exit (E)? ".format(
                        basemap
                    )
                )
                if action == "C":
                    cache(basemap)
                elif action == "S":
                    continue
                else:
                    stop = True
                    break
    elif args["vector"]:
        basemap = args["<basemap>"]
        vector_basemaps = config.get_config_value("vectorBaseMaps")

        if not args["--skip-update"]:
            vector.update_data()

        stats.record_start(basemap, "cache")
        vector.main(basemap, vector_basemaps[basemap])
        stats.record_finish(basemap, "cache")
    elif args["vector-all"]:
        vector_basemaps = config.get_config_value("vectorBaseMaps")

        if not args["--skip-update"]:
            vector.update_data()

        for basemap in [key for key in list(vector_basemaps.keys())]:
            stats.record_start(basemap, "cache")
            vector.main(basemap, vector_basemaps[basemap])
            stats.record_finish(basemap, "cache")
    elif args["cleanup"]:
        cleanup.main()
    elif args["<basemap>"]:
        cache(
            args["<basemap>"],
            args["--missing-only"],
            args["--skip-update"],
            args["--skip-test"],
            args["--spot"],
            args["--levels"],
            dont_wait=args["--dont-wait"],
        )
    elif args["stats"]:
        stats.print_stats()
    elif args["resume"]:
        job = get_current_job()

        if job is None:
            logger.warning("no current job found!")
        else:
            cache_name = job["cache_args"][0]
            logger.info(f"resuming {cache_name}")
            send_email(f"Cache Job Resumed: {cache_name}", json.dumps(job, indent=2))
            update_job("restart_times", str(datetime.now()))
            cache(*job["cache_args"], is_resumed_job=True)


if __name__ == "__main__":
    sys.exit(main())
