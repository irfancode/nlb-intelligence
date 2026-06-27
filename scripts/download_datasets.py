#!/usr/bin/env python3
"""Download NLB datasets from data.gov.sg."""

import json
import csv
import io
from pathlib import Path
from urllib.request import urlopen

DATASETS = {
    "digitised_books_magazines": {
        "id": "d_837344f69211296ed8c03b7c2553a34f",
        "description": "Digitised Books and Magazines 2024",
    },
    "digitised_documents": {
        "id": "d_4982d51eb70e64dbd0f4a3f524015480",
        "description": "Digitised Documents and Manuscripts 2024",
    },
    "archived_websites": {
        "id": "d_ec5e08ce1e8bfe7a2f016ecc250d085a",
        "description": "Archived Websites 2024",
    },
    "online_articles": {
        "id": "d_2c0eb3e7e92a449ce0de635d3aa43d83",
        "description": "Online Articles 2024",
    },
    "digitised_av": {
        "id": "d_7cb942a9fdbcb374fd8eac241081dbe4",
        "description": "Digitised Sound and Video Recordings 2024",
    },
    "digitised_images": {
        "id": "d_d269162117ff494b2832723e18b10e88",
        "description": "Digitised Images",
    },
    "digitised_maps": {
        "id": "d_5d624e3d2f8c0ba248ad14fac6181642",
        "description": "Digitised Maps 2024",
    },
}

DATA_DIR = Path(__file__).parent.parent / "datasets"


def download_dataset(dataset_id: str, output_path: Path) -> bool:
    """Download a dataset from data.gov.sg using the poll-download API."""
    url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
    print(f"  Fetching download URL from {url}...")
    try:
        resp = urlopen(url)
        data = json.loads(resp.read().decode())
        if data.get("code") != 0:
            print(f"  Error: {data.get('errMsg', 'Unknown error')}")
            return False
        download_url = data.get("data", {}).get("url")
        if not download_url:
            print(f"  No download URL returned")
            return False
        print(f"  Downloading from {download_url}...")
        resp = urlopen(download_url)
        content = resp.read()
        output_path.write_bytes(content)
        file_size_mb = len(content) / (1024 * 1024)
        print(f"  Saved to {output_path.name} ({file_size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading NLB datasets to {DATA_DIR}/ ...\n")

    for name, info in DATASETS.items():
        print(f"[{name}] {info['description']}")
        ext = ".csv"
        output = DATA_DIR / f"{name}{ext}"
        if output.exists():
            print(f"  Already exists, skipping. Delete {output} to re-download.\n")
            continue
        download_dataset(info["id"], output)
        print()


if __name__ == "__main__":
    main()
