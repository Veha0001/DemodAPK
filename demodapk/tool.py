"""
- https://github.com/textualize/rich/blob/master/examples/downloader.py
"""

import json
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from demodapk.utils import log

# === Rich progress setup ===
progress = Progress(
    TextColumn(
        "[bold blue]{task.fields[filename]}",
        justify="right",
    ),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)

done_event = Event()


def handle_sigint(signum, frame):
    done_event.set()
    _ = signum, frame


signal.signal(signal.SIGINT, handle_sigint)


# === File download function ===
def copy_url(task_id: TaskID, url: str, path: str) -> None:
    """Copy data from a url to a local file."""
    log.info("Requesting: %s", url)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as response:
        # Break if content length is missing
        total = response.info().get("Content-Length")
        total = int(total) if total is not None else 0

        progress.update(task_id, total=total)
        with open(path, "wb") as dest_file:
            progress.start_task(task_id)
            for data in iter(partial(response.read, 32768), b""):
                dest_file.write(data)
                progress.update(task_id, advance=len(data))
                if done_event.is_set():
                    return
    log.info("Downloaded: %s", path)


def download(urls, dest_dir="."):
    """Download multiple files to the given directory."""
    os.makedirs(dest_dir, exist_ok=True)
    with progress:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for url in urls:
                filename = url.split("/")[-1]
                dest_path = os.path.join(dest_dir, filename)
                task_id = progress.add_task("download", filename=filename, start=False)
                pool.submit(copy_url, task_id, url, dest_path)


def get_latest_version():
    """Get the latest version of APKEditor from GitHub API."""
    url = "https://api.github.com/repos/reandroid/apkeditor/releases/latest"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req) as resp:
            data = json.load(resp)
            tag_name = data.get("tag_name")
            if tag_name:
                # Remove leading 'V' if present
                return tag_name.lstrip("Vv")
    except (URLError, HTTPError) as e:
        log.error(e)
        sys.exit(1)
    return None


def download_apkeditor(dest_path):
    latest_version = get_latest_version()
    if latest_version:
        log.info("APKEditor latest version: %s", latest_version)
        jar_url = (
            "https://github.com/REAndroid/APKEditor/releases/download/"
            f"V{latest_version}/APKEditor-{latest_version}.jar"
        )
        download([jar_url], dest_path)
    else:
        log.critical("Could not determine the latest version.")
