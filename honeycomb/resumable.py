from .config import config_folder
from pathlib import Path
import json
import os

file_path = Path(config_folder) / "current_job.json"


def cache_job_status(job):
    with open(file_path, "w") as file:
        json.dump(job, file, indent=2)


def get_current_job():
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return None


def start_new_job(basemap, missing_only, skip_update, skip_test, spot, levels):
    job = {
        "cache_args": [basemap, missing_only, skip_update, skip_test, spot, levels],
        "data_updated": False,
        "test_cache_complete": False,
        "cache_extents_completed": [],
        "restart_times": [],
    }

    cache_job_status(job)


def update_job(prop, value):
    job = get_current_job()

    if job is None:
        raise Exception("No job has been created!")

    try:
        job[prop].append(value)
    except AttributeError:
        job[prop] = value

    cache_job_status(job)


def get_job_status(prop):
    job = get_current_job()

    if job is None:
        raise Exception("No job has been created!")

    return job[prop]


def finish_job():
    os.remove(file_path)
