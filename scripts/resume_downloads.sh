#!/usr/bin/env bash
# Resume downloads for the larger incomplete datasets (BBBC005 images 1.8GB, BBBC034 545MB).
set -uo pipefail
RAW_DIR="data/raw"

download() {
    local url="$1"
    local dest="$2"
    if [[ -f "$dest" ]] && [[ $(stat -f%z "$dest") -gt 1000000 ]]; then
        echo "[skip] $dest already exists ($(du -h "$dest" | cut -f1))"
        return 0
    fi
    echo "[get ] $url -> $dest"
    curl -L --fail --retry 5 --retry-delay 5 -o "$dest" "$url"
}

download "https://data.broadinstitute.org/bbbc/BBBC005/BBBC005_v1_images.zip" "$RAW_DIR/BBBC005_v1_images.zip"
download "https://data.broadinstitute.org/bbbc/BBBC034/BBBC034_v1_dataset.zip" "$RAW_DIR/BBBC034_v1_dataset.zip"