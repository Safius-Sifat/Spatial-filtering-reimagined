#!/usr/bin/env bash
# Download all three fluorescence microscopy datasets in parallel.
# BBBC005  : synthetic HCS fluorescent cell populations + ground-truth masks
# Fluo-N2DH-GOWT1 (Cell Tracking Challenge) : GFP-GOWT1 mouse embryonic stem cells
# BBBC034  : hiPSC colony volumes (CellMask/GFP/DNA channels)
#
# Run from project root with uv-managed environment available.

set -euo pipefail

RAW_DIR="data/raw"
GT_DIR="data/ground_truth"
mkdir -p "$RAW_DIR" "$GT_DIR"

# Dataset URLs (verified accessible as of 2026-07)
URL_BBBC005_IMAGES="https://data.broadinstitute.org/bbbc/BBBC005/BBBC005_v1_images.zip"
URL_BBBC005_GT="https://data.broadinstitute.org/bbbc/BBBC005/BBBC005_v1_ground_truth.zip"
URL_FLUO_GOWT1="https://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-GOWT1.zip"
URL_BBBC034="https://data.broadinstitute.org/bbbc/BBBC034/BBBC034_v1_dataset.zip"

download() {
    local url="$1"
    local dest="$2"
    if [[ -f "$dest" ]]; then
        echo "[skip] already exists: $dest ($(du -h "$dest" | cut -f1))"
        return 0
    fi
    echo "[get ] $url -> $dest"
    curl -L --fail --retry 3 --retry-delay 5 -o "$dest" "$url"
}

# Launch downloads in parallel
download "$URL_BBBC005_IMAGES" "$RAW_DIR/BBBC005_v1_images.zip" &
PID_BBBC005_IMG=$!

download "$URL_BBBC005_GT" "$GT_DIR/BBBC005_v1_ground_truth.zip" &
PID_BBBC005_GT=$!

download "$URL_FLUO_GOWT1" "$RAW_DIR/Fluo-N2DH-GOWT1.zip" &
PID_FLUO=$!

download "$URL_BBBC034" "$RAW_DIR/BBBC034_v1_dataset.zip" &
PID_BBBC034=$!

# Wait and report
for pid in "$PID_BBBC005_IMG" "$PID_BBBC005_GT" "$PID_FLUO" "$PID_BBBC034"; do
    wait "$pid" && echo "[done] pid=$pid" || echo "[FAIL] pid=$pid"
done

echo
echo "=== Download summary ==="
ls -lh "$RAW_DIR" "$GT_DIR"