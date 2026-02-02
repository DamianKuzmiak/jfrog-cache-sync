"""
Script to fetch the latest artifacts from a JFrog repository.
"""

import argparse
import hashlib
import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler

from urllib3.exceptions import NameResolutionError

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


def append_to_checksums_file(checksums_path: str, filename: str, sha256: str) -> None:
    """Append a file's checksum to checksums.json file."""
    checksums_data = {"sha256": {}}

    if os.path.exists(checksums_path):
        try:
            with open(checksums_path, "r", encoding="utf8") as f:
                checksums_data = json.load(f)
                if "sha256" not in checksums_data:
                    checksums_data["sha256"] = {}
        except json.JSONDecodeError:
            logger.warning("Could not parse existing checksums.json, creating fresh")
            checksums_data = {"sha256": {}}

    checksums_data["sha256"][filename] = sha256
    with open(checksums_path, "w", encoding="utf8") as f:
        json.dump(checksums_data, f, indent=2, ensure_ascii=False)

    # logger.debug("Appended checksum for %s to %s", filename, checksums_path)


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_artifacts_with_structure(base_dir: str, artifacts: list[dict], api_key: str) -> None:
    """
    Save artifacts in local folders matching JFrog repo/path structure.

    :param artifacts: List of artifact dicts from find_artifacts
    :param base_dir: Local base directory to mirror JFrog structure
    :param api_key: API key for authentication
    """
    for idx, artifact in enumerate(artifacts, start=1):
        logger.info(
            "File %03d: path=%s/%s, created=%s, sha256=%s",
            idx,
            artifact["path"],
            artifact["name"],
            artifact["created"],
            artifact["sha256"],
        )

        local_dir = os.path.join(base_dir, artifact["repo"], artifact["path"])
        local_file = os.path.join(local_dir, artifact["name"])

        if os.path.exists(local_file):
            # logger.debug("File already exists, skipping.")
            continue

        logger.debug("Local file not found: %s", local_file)

        # Path to checksums file in the same directory as the downloaded file
        checksums_file = os.path.join(local_dir, "checksums.json")

        os.makedirs(local_dir, exist_ok=True)
        download_url = artifact["download_url"]
        temp_file = local_file + ".part"
        logger.info("Downloading %s...", download_url)

        try:
            download_artifact(download_url, temp_file, api_key)
        except NameResolutionError as ex:
            logger.error("DNS resolution failed: %s", ex)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            continue
        except Exception as ex:
            logger.error("Failed to download %s: %s", download_url, ex)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            continue

        calculated_sha256 = calculate_sha256(temp_file)
        logger.info("Calculated sha256: %s", calculated_sha256)

        if calculated_sha256 != artifact["sha256"]:
            logger.error(
                "SHA256 mismatch for %s: expected %s, got %s",
                temp_file,
                artifact["sha256"],
                calculated_sha256,
            )
            file_size = os.path.getsize(temp_file)
            logger.debug("Removing file %s (size: %d bytes)", temp_file, file_size)

            os.remove(temp_file)  # Remove the file if checksum doesn't match
            continue

        try:
            os.replace(temp_file, local_file)
            # logger.info("SHA256 verification passed for %s", artifact["name"])
            append_to_checksums_file(checksums_file, artifact["name"], calculated_sha256)
        except Exception as ex:
            logger.error("Failed to rename file %s to %s: %s", temp_file, local_file, ex)


def cleanup_old_files(directory, keep_days=5):
    """
    Delete files older than 'keep_days' in the directory and its subdirectories.
    Also removes empty parent directories after file deletion.

    :param directory: Directory to clean up
    :param keep_days: Number of days to keep files for, files older than this will be deleted
    """
    current_time = time.time()
    max_age_seconds = keep_days * 24 * 3600

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_mtime = current_time - os.path.getmtime(file_path)
            if file_mtime > max_age_seconds:
                logger.info("Removing old file: %s (age: %.1f days)", file_path, file_mtime / 86400)
                os.remove(file_path)

                # Remove empty parent directories after file deletion
                parent_dir = os.path.dirname(file_path)
                try:
                    # Only attempt to remove if it's not the base directory
                    while parent_dir != directory and parent_dir:
                        if not os.listdir(parent_dir):  # Directory is empty
                            logger.info("Removing empty directory: %s", parent_dir)
                            os.rmdir(parent_dir)
                            parent_dir = os.path.dirname(parent_dir)
                        else:
                            break  # Directory is not empty, stop
                except OSError:
                    pass


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
        "max_artifact_age_days",
        "download_dir",
        "keep_files_days",
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
        max_age_days=config["max_artifact_age_days"],
        exclude_paths=config.get("exclude_paths"),
    )

    if artifacts:
        logger.info("Found %d artifacts.", len(artifacts))
        # for artifact in artifacts:
        #     logger.debug(
        #         " * path: %s, name: %s, created: %s, sha256: %s",
        #         artifact["path"],
        #         artifact["name"],
        #         artifact["created"],
        #         artifact["sha256"],
        #     )
        save_artifacts_with_structure(config["download_dir"], artifacts, args.api_key)
    else:
        logger.info("No artifacts found.")

    # Optional: Cleanup old files in the main repo directory
    repo_dir = os.path.join(config["download_dir"], config["repo"])
    logger.info("Cleaning up old files older than %d days", config["keep_files_days"])
    cleanup_old_files(repo_dir, keep_days=config["keep_files_days"])


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    FORMATTER = "%(asctime)s [%(levelname)s] %(message)s"

    MAX_LOG_SIZE = 2 * 1024 * 1024  # 2 MB
    BACKUP_COUNT = 5
    file_handler = RotatingFileHandler(PATH_TO_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
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

    logger.info("=" * 80)
    logger.info("Script started.")

    try:
        main()
        logger.info("Script completed successfully.")
    except Exception as e:
        logger.exception("Script failed with error: %s", e)
