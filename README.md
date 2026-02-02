# JFrog Artifact Fetcher

A Python script to fetch and download the latest artifacts from a JFrog Artifactory repository, supporting API key
authentication.

## Features

- Query JFrog Artifactory for recent artifacts using AQL
- Download artifacts matching file masks and path
- Exclude paths using wildcard patterns (e.g., `*dirty*`, `*temp*`)
- Mirror JFrog repo/path structure locally
- Configurable artifact age filter
- Global and folder-specific file retention policies
- Automatic cleanup of old files with empty directory removal
- SHA256 checksum verification
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
  "exclude_paths": ["*dirty*", "*temp*"],
  "file_masks": ["build_info.json", "*.tar.gz"],
  "max_artifact_age_days": 7,
  "download_dir": "artifact_cache",
  "keep_files_days": 30,
  "logs_dir": "logs",
  "folder_retention": [
    {"path": "your/path/debug", "keep_days": 7},
    {"path": "your/path/release", "keep_days": 60}
  ]
}
```

Configuration parameters:

- `artifactory_url`: Base URL of your JFrog Artifactory instance
- `repo`: Repository name in Artifactory
- `path`: Path within the repository to search for artifacts
- `exclude_paths`: (Optional) List of path patterns to exclude (e.g., `["*dirty*", "*temp*"]`)
- `file_masks`: List of file patterns to match when searching for artifacts
- `max_artifact_age_days`: Only fetch artifacts newer than this many days
- `download_dir`: Local directory where artifacts will be downloaded. Can be absolute or relative to the script location
- `logs_dir`: (Optional) Directory for log files. Can be absolute or relative to the script location. Defaults to the script directory if not specified
- `keep_files_days`: Global default retention period (days) for downloaded files
- `folder_retention`: (Optional) Override retention for specific folders and their subdirectories

## Usage

Run the script with your JFrog API key:

```bash
python jfrog_download.py --api-key YOUR_API_KEY
```

Artifacts will be downloaded to the directory specified in `config.json`.

**File Retention:**
- Files are kept for the number of days specified in `keep_files_days` (global default)
- Use `folder_retention` to set different retention periods for specific folders
- Subdirectories automatically inherit their parent folder's retention policy
- **Nested rules**: More specific paths override parent paths
- Empty directories are automatically removed after file cleanup

## License

MIT License.
