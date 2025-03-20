import datetime
import json
import time
from pathlib import Path

import humanize
from tabulate import tabulate

from .config import config_folder
from .log import logger

stats_file = Path(config_folder) / "stats.json"

if not stats_file.exists():
    stats_file.touch()
    stats_file.write_text(json.dumps({"basemaps": {}}))


def get_basemap(basemap):
    stats = json.loads(stats_file.read_text())
    if basemap in stats["basemaps"]:
        return stats["basemaps"][basemap]
    return {"cache": {"start": 0, "runs": []}, "upload": {"start": 0, "runs": []}}


def save_basemap(basemap, data):
    stats = json.loads(stats_file.read_text())
    stats["basemaps"][basemap] = data
    stats_file.write_text(json.dumps(stats, indent=2))


def record_start(basemap, task):
    validate_task(task)

    basemap_stats = get_basemap(basemap)
    basemap_stats[task]["start"] = int(time.time())
    save_basemap(basemap, basemap_stats)


def validate_task(task):
    if task not in ["cache", "upload"]:
        raise ValueError(f"invalid task: {task}")


def record_finish(basemap, task):
    validate_task(task)

    basemap_stats = get_basemap(basemap)
    if basemap_stats[task]["start"] == 0:
        logger.warning(f"no start time has been recorded for task: {task}")
        return

    duration = int(time.time()) - basemap_stats[task]["start"]

    if duration > 60:
        basemap_stats[task]["runs"].append(
            {
                "duration": duration,
                "completionDate": datetime.datetime.now().isoformat(),
            }
        )
    basemap_stats[task]["start"] = 0

    save_basemap(basemap, basemap_stats)


def get_average_duration(runs):
    if len(runs) == 0:
        return "no runs have been recorded"

    total_duration = 0
    for run in runs:
        total_duration += run["duration"]
    return humanize.naturaldelta(total_duration / len(runs))


def print_stats():
    stats = json.loads(stats_file.read_text())
    table = []
    for basemap in stats["basemaps"]:
        row = [basemap]
        row.append(get_average_duration(stats["basemaps"][basemap]["cache"]["runs"]))
        row.append(get_average_duration(stats["basemaps"][basemap]["upload"]["runs"]))
        table.append(row)

    print("Average processing times:")
    print(tabulate(table, headers=["basemap", "cache", "upload"]))


if __name__ == "__main__":
    print_stats()
