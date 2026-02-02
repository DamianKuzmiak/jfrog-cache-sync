# JFrog Artifact Fetcher

A Python script to fetch and download the latest artifacts from a JFrog Artifactory repository, supporting API key
authentication.

## Features

- Query JFrog Artifactory for recent artifacts using AQL
- Download artifacts matching file masks and path
- Mirror JFrog repo/path structure locally
- Configurable artifact age filter
- Local file retention policy with automatic cleanup
- Logging to file and console

## Requirements

- Python 3.8+
- `requests` library

## Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Edit `config.json` to set your JFrog URL, repo, path, file masks, and download directory.

## Configuration

Example `config.json`:

```json
{
  "artifactory_url": "https://jfrog.example.com",
  "repo": "your-repo",
  "path": "your/path",
  "file_masks": [
    "build_info.json",
    "*.tar.gz"
  ],
  "max_artifact_age_days": 7,
  "download_dir": "D:\\Artifacts",
  "keep_files_days": 30
}
```

Configuration parameters:

- `artifactory_url`: Base URL of your JFrog Artifactory instance
- `repo`: Repository name in Artifactory
- `path`: Path within the repository to search for artifacts
- `file_masks`: List of file patterns to match when searching for artifacts
- `max_artifact_age_days`: Only fetch artifacts newer than this many days
- `download_dir`: Local directory where artifacts will be downloaded
- `keep_files_days`: Number of days to keep downloaded files before automatic deletion

## Usage

Run the script with your JFrog API key:

```bash
python jfrog_download.py --api-key YOUR_API_KEY
```

Artifacts will be downloaded to the directory specified in `config.json`.
Files older than `keep_files_days` will be automatically removed from the local directory.

## License

MIT License.
