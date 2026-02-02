"""
Script to fetch the latest artifacts from a JFrog repository.
"""

import json
import logging
import os

import requests
from jfrog_utils import find_artifacts

CONFIG_PATH = "config.json"


def load_config(path: str = CONFIG_PATH) -> dict:
    """Load configuration from a JSON file."""
    with open(path, "r", encoding="utf8") as f:
        config = json.load(f)
    logger.debug("Loaded config: %s", config)
    return config


def download_artifact(url: str, dest_path: str, api_key: str) -> None:
    """
    Download an artifact from the given Jfrog artifactory URL and save it to the destination path.

    :param url: The URL of the artifact to download.
    :param dest_path: The full path (including filename) to save the artifact.
    :param api_key: API key for authentication
    """
    headers = {"X-JFrog-Art-Api": api_key}
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an error for HTTP issues
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info("Downloaded artifact to: %s", dest_path)
    except requests.RequestException as ex:
        logging.error("Failed to download %s: %s", url, ex)


def save_artifacts_with_structure(base_dir: str, artifacts: list[dict], api_key: str) -> None:
    """
    Save artifacts in local folders matching JFrog repo/path structure.

    :param artifacts: List of artifact dicts from find_artifacts
    :param base_dir: Local base directory to mirror JFrog structure
    :param api_key: API key for authentication
    """
    for artifact in artifacts:
        local_dir = os.path.join(base_dir, artifact["repo"], artifact["path"])
        local_file = os.path.join(local_dir, artifact["name"])
        if os.path.exists(local_file):
            logging.info("File already exists, skipping: %s", local_file)
            continue

        # print(f"Would save to: {local_file}")
        # Continue?

        os.makedirs(local_dir, exist_ok=True)
        download_url = artifact["download_url"]
        temp_file = local_file + ".part"
        logging.info("Downloading %s to temporary file %s", download_url, temp_file)
        try:
            download_artifact(download_url, temp_file, api_key)
            os.replace(temp_file, local_file)
            logging.info("Renamed %s to %s", temp_file, local_file)
        except Exception as ex:
            logging.error("Failed to download or rename %s: %s", download_url, ex)
            if os.path.exists(temp_file):
                os.remove(temp_file)


# def cleanup_old_files(directory, keep=5):
#     """Keep only the latest `keep` files in the directory."""
#     files = sorted([os.path.join(directory, f) for f in os.listdir(directory)], key=os.path.getmtime, reverse=True)
#     for old_file in files[keep:]:
#         logging.info(f"Removing old file: {old_file}")
#         os.remove(old_file)


def main():
    config = load_config()
    required_keys = [
        "artifactory_url",
        "repo",
        "username",
        "api_key",
        "path",
        "file_masks",
        "days_back",
        "download_dir",
    ]
    for key in required_keys:
        if key not in config:
            logger.error("Missing config key: %s", key)
            return

    artifacts = find_artifacts(
        url=config["artifactory_url"],
        repo=config["repo"],
        username=config["username"],
        api_key=config["api_key"],
        path=config["path"],
        file_masks=config["file_masks"],
        days_back=config["days_back"],
    )

    if artifacts:
        logger.info("Found %d artifacts.", len(artifacts))
        for artifact in artifacts:
            name = artifact["name"]
            path = artifact["path"]
            created = artifact["created"]
            logger.debug("Artifact name: %s, Path: %s, Created: %s", name, path, created)

        save_artifacts_with_structure(config.get("download_dir"), artifacts, config.get("api_key"))
    else:
        logger.info("No artifacts found.")

    # cleanup_old_files(config["download_dir"], keep=5)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler("artifact_fetcher.log")
    file_handler.setLevel(logging.DEBUG)
    FORMATTER = "%(asctime)s [%(levelname)s] %(message)s"
    file_formatter = logging.Formatter(FORMATTER)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(FORMATTER)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Script started.")

    try:
        main()
        logging.info("Script completed successfully.")
    except Exception as e:
        logging.exception("Script failed with error: %s", e)
