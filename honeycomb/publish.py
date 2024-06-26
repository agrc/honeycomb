#!/usr/bin/env python
# * coding: utf8 *
"""
publish.py

A module that contains code for publishing mxd's to ArcGIS Server for raster caches.
"""

from os import mkdir, remove
from os.path import exists, join

import arcpy

from . import config
from .log import logger


def publish(basemap):
    mxd_path = join(config.get_config_value("mxdFolder"), basemap + ".mxd")
    drafts_folder = join(config.config_folder, "sddrafts")
    sddraft_path = join(drafts_folder, basemap + ".sddraft")

    if not exists(drafts_folder):
        mkdir(drafts_folder)

    logger.info("creating .sddraft")
    arcpy.mapping.CreateMapSDDraft(mxd_path, sddraft_path, basemap, connection_file_path=config.ags_connection_file)

    logger.info("analyzing")
    analysis = arcpy.mapping.AnalyzeForSD(sddraft_path)
    logger.info("The following information was returned during analysis of the MXD:")
    for key in ("messages", "warnings", "errors"):
        items = analysis[key]
        if len(items) > 0:
            logger.info(key.upper())
            for (message, code), layerlist in items.items():
                logger.info("{} (CODE {})".format(message, code))

                if len(layerlist) > 0:
                    logger.info("applies to:")
                    for layer in layerlist:
                        logger.info(layer.name + "\n")

    if analysis["errors"] == {}:
        logger.info("updating sddraft values")

        with open(sddraft_path, "r") as sddraft_file:
            txt = sddraft_file.read()

            txt = txt.replace(
                "<{0}>{1}</{0}>".format("KeepExistingMapCache", "false"),
                "<{0}>{1}</{0}>".format("KeepExistingMapCache", "true"),
            )
            is_cached = "<Key>isCached</Key><Value xsi:type='xs:string'>false</Value>"
            txt = txt.replace(is_cached, is_cached.replace("false", "true"))
            min_instances = "<Key>MinInstances</Key><Value xsi:type='xs:string'>1</Value>"
            txt = txt.replace(min_instances, min_instances.replace("1", "0"))
            anti_aliasing = "<Key>antialiasingMode</Key><Value xsi:type='xs:string'>None</Value>"
            txt = txt.replace(anti_aliasing, anti_aliasing.replace("None", "Fast"))
            storage_format = "<StorageFormat>esriMapCacheStorageModeCompactV2</StorageFormat>"
            txt = txt.replace(
                storage_format,
                storage_format.replace("esriMapCacheStorageModeCompactV2", "esriMapCacheStorageModeExploded"),
            )

        with open(sddraft_path, "w") as sddraft_file:
            sddraft_file.write(txt)

        logger.info("staging")
        sd_path = sddraft_path.replace(".sddraft", ".sd")
        if exists(sd_path):
            remove(sd_path)
        arcpy.server.StageService(sddraft_path, sd_path)

        logger.info("uploading")
        arcpy.server.UploadServiceDefinition(sd_path, config.ags_connection_file)

        logger.info("service published successfully!")
    else:
        logger.error(
            "Service could not be published because of errors found during analysis. Please fix them and republish."
        )
