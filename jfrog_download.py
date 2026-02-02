"""
Script to fetch the latest artifacts from a JFrog repository.
"""

import argparse
import json
import logging
import os

from jfrog_utils import find_artifacts, download_artifact

PATH_TO_LOG_FILE = r"C:\SW\log.log"
CONFIG_PATH = "config.json"


def load_config(path: str = CONFIG_PATH) -> dict:
    """Load configuration from a JSON file."""
    if not os.path.dirname(path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, path)
    with open(path, encoding="utf8") as f:
        config = json.load(f)
    logger.debug("Loaded config: %s", config)
    return config


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
            logger.info("File already exists, skipping: %s", local_file)
            continue

        # print(f"Would save to: {local_file}")
        # Continue?

        os.makedirs(local_dir, exist_ok=True)
        download_url = artifact["download_url"]
        temp_file = local_file + ".part"
        logger.info("Downloading %s to temporary file %s", download_url, temp_file)

        try:
            download_artifact(download_url, temp_file, api_key)
            os.replace(temp_file, local_file)
            logger.info("Renamed file to %s", local_file)
        except Exception as ex:
            logger.error("Failed to download or rename %s: %s", download_url, ex)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


# def cleanup_old_files(directory, keep=5):
#     """Keep only the latest `keep` files in the directory."""
#     files = sorted([os.path.join(directory, f) for f in os.listdir(directory)], key=os.path.getmtime, reverse=True)
#     for old_file in files[keep:]:
#         logger.info(f"Removing old file: {old_file}")
#         os.remove(old_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True, help="JFrog API key")
    args = parser.parse_args()

    config = load_config()
    required_keys = [
        "artifactory_url",
        "repo",
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
        username="",
        api_key=args.api_key,
        path=config["path"],
        file_masks=config["file_masks"],
        days_back=config["days_back"],
    )

    if not artifacts:
        logger.info("No artifacts found.")
    else:
        logger.info("Found %d artifacts.", len(artifacts))
        for artifact in artifacts:
            logger.debug(
                " * path: %s, name: %s, created: %s", artifact["path"], artifact["name"], artifact["created"])

        save_artifacts_with_structure(config["download_dir"], artifacts, args.api_key)

    # cleanup_old_files(config["download_dir"], keep=5)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    FORMATTER = "%(asctime)s [%(levelname)s] %(message)s"

    # File handler
    file_handler = logging.FileHandler(PATH_TO_LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
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
        logger.info("Script completed successfully.")
    except Exception as e:
        logger.exception("Script failed with error: %s", e)
