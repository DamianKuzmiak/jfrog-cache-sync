from datetime import datetime, timedelta, timezone
from typing import List, Dict

import requests


def find_artifacts(
        url: str, repo: str, api_key: str, username: str, path: str, file_masks: List[str], max_age_days: int = 7
) -> List[Dict]:
    """
    Query JFrog Artifactory for recently added artifacts matching given file masks.

    :param url: Base URL of the Artifactory instance
    :param repo: Repository name
    :param api_key: API key or password for authentication
    :param username: Username for authentication
    :param path: Path prefix to search under
    :param file_masks: List of file name patterns (wildcards supported)
    :param max_age_days: Maximum age (in days) of artifacts to include
    :return: List of dictionaries with artifact info (download URL, created time, etc.)
    """
    date_threshold = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    name_conditions = ",\n".join([f'{{"name": {{"$match": "{mask}"}}}}' for mask in file_masks])
    aql_query = f"""items.find({{
        "$and": [
            {{"repo": "{repo}"}},
            {{"path": {{"$match": "{path}*"}}}},
            {{"created": {{"$gt": "{date_threshold}"}}}},
            {{"$or": [
                {name_conditions}
            ]}}
        ]
    }}).include("name", "repo", "path", "created", "sha256")
    """

    with requests.Session() as session:
        response = session.post(
            f"{url}/artifactory/api/search/aql",
            data=aql_query,
            auth=(username, api_key),
            headers={"Content-Type": "text/plain"},
        )

        if response.status_code != 200:
            raise Exception(f"Artifactory query failed: {response.status_code} - {response.text}")

        try:
            results = response.json().get("results", [])
        except Exception as e:
            raise Exception(f"Failed to parse JSON response: {e}")

        if not results:
            return []

        return [
            {
                "download_url": f"{url}/artifactory/{item['repo']}/{item['path']}/{item['name']}",
                "created": item["created"],
                "name": item["name"],
                "repo": item["repo"],
                "path": item["path"],
                "sha256": item.get("sha256", ""),
            }
            for item in results
        ]


def download_artifact(url: str, dest_path: str, api_key: str) -> None:
    """
    Download an artifact from the given Jfrog artifactory URL and save it to the destination path.

    :param url: The URL of the artifact to download.
    :param dest_path: The full path (including filename) to save the artifact.
    :param api_key: API key for authentication
    """
    headers = {"X-JFrog-Art-Api": api_key}
    response = requests.get(url, stream=True, headers=headers, timeout=60)
    response.raise_for_status()  # Raise an error for HTTP issues
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
