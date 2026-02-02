# JFrog Artifact Fetcher

A Python script to fetch and download the latest artifacts from a JFrog Artifactory repository, supporting API key
authentication.

## Features

- Query JFrog Artifactory for recent artifacts using AQL
- Download artifacts matching file masks and path
- Mirror JFrog repo/path structure locally
- Configurable retention period (`days_back`)
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
  "username": "",
  "repo": "your-repo",
  "path": "your/path",
  "file_masks": [
    "build_info.json",
    "*.tar.gz"
  ],
  "days_back": 7,
  "download_dir": "D:\\Artifacts"
}
```

## Usage

Run the script with your JFrog API key:

```bash
python jfrog_download.py --api-key YOUR_API_KEY
```

Artifacts will be downloaded to the directory specified in `config.json`.

## License

MIT License.
