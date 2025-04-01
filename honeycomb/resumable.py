import json
import os
from pathlib import Path
from typing import List, Literal, Optional, TypedDict, Union

from .config import config_folder

file_path = Path(config_folder) / "current_job.json"
Properties = Literal[
    "data_updated",
    "test_cache_complete",
    "cache_extents_completed",
    "caching_complete",
    "exploding_complete",
    "restart_times",
]


class Job(TypedDict):
    cache_args: List[Union[str, bool, List[int]]]
    data_updated: bool
    test_cache_complete: bool
    cache_extents_completed: List[str]
    caching_complete: bool
    exploding_complete: bool
    restart_times: List[str]


def cache_job_status(job: Job) -> None:
    with open(file_path, "w") as file:
        json.dump(job, file, indent=2)


def get_current_job() -> Optional[Job]:
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return None


def start_new_job(
    basemap: str,
    missing_only: bool,
    skip_update: bool,
    skip_test: bool,
    spot: str,
    levels: List[int],
) -> None:
    job: Job = {
        "cache_args": [basemap, missing_only, skip_update, skip_test, spot, levels],
        "data_updated": False,
        "test_cache_complete": False,
        "cache_extents_completed": [],
        "caching_complete": False,
        "exploding_complete": False,
        "restart_times": [],
    }

    cache_job_status(job)


def update_job(
    prop: Properties,
    value: Union[str, bool],
) -> None:
    job: Optional[Job] = get_current_job()

    if job is None:
        raise Exception("No job has been created!")

    try:
        #: if the property is a list, append the value to it
        job[prop].append(value)
    except AttributeError:
        job[prop] = value

    cache_job_status(job)


def get_job_status(prop: Properties) -> Union[str, bool, List[str]]:
    job = get_current_job()

    if job is None:
        raise Exception("No job has been created!")

    return job[prop]


def finish_job() -> None:
    os.remove(file_path)
