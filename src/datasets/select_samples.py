"""Extract one sample image per dataset for fast iteration.

We pull one representative field of view per dataset, normalise to 8-bit
grayscale at 512x512, and write it to data/selected/ with the same name
as the dataset key (so downstream code can stay dataset-agnostic).

Public dataset sources (refer to README and project plan for citations):
  BBBC005  : https://bbbc.broadinstitute.org/BBBC005
  Fluo-N2DH-GOWT1 : https://celltrackingchallenge.net/2d-datasets/
  BBBC034  : https://bbbc.broadinstitute.org/BBBC034
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
GT_DIR = PROJECT_ROOT / "data" / "ground_truth"
SELECTED_DIR = PROJECT_ROOT / "data" / "selected"
SELECTED_DIR.mkdir(parents=True, exist_ok=True)


def _save_8bit(image: np.ndarray, out_path: Path) -> None:
    if image.dtype != np.uint8:
        if image.max() > 255 or image.min() < 0:
            p_lo, p_hi = np.percentile(image, [0.5, 99.5])
            image = np.clip((image - p_lo) / max(p_hi - p_lo, 1e-9) * 255.0, 0, 255)
        else:
            image = np.clip(image, 0, 255)
        image = image.astype(np.uint8)
    Image.fromarray(image).save(out_path)


def select_bbbc005_sample() -> Path | None:
    """Pick a moderate-size BBBC005 image (around the 25th percentile by size)
    and its matching foreground mask."""
    zip_path = RAW_DIR / "BBBC005_v1_images.zip"
    gt_zip_path = GT_DIR / "BBBC005_v1_ground_truth.zip"
    if not zip_path.exists():
        print(f"  [skip] missing {zip_path}")
        return None

    # BBBC005 ships images as BBBC005_v1_images/<name>.TIF (uppercase extension).
    # Pick from the intersection with GT (1200 images have masks).
    with zipfile.ZipFile(zip_path) as zif:
        img_names = {n.split("/")[-1]: n for n in zif.namelist() if n.upper().endswith(".TIF")}
    if gt_zip_path.exists():
        with zipfile.ZipFile(gt_zip_path) as zgf:
            gt_names = {n.split("/")[-1] for n in zgf.namelist() if n.upper().endswith(".TIF")}
        common = sorted(set(img_names) & gt_names)
    else:
        common = sorted(img_names)

    # Pick a moderate-size image with GT
    with zipfile.ZipFile(zip_path) as zf:
        sizes = [(zf.getinfo(img_names[name]).file_size, name) for name in common]
    sizes.sort()
    chosen_stem = sizes[len(sizes) // 4][1]  # 25th percentile
    chosen = img_names[chosen_stem]

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(chosen) as fh:
            img = tifffile.imread(fh)

    # BBBC005 SIMCEP images are 696x520 single-channel
    if img.ndim == 3:
        img = img[:, :, 0] if img.shape[-1] < img.shape[0] else img[0]

    out_img = SELECTED_DIR / "bbbc005_sample.png"
    _save_8bit(img, out_img)
    print(f"  -> {out_img}  (shape={img.shape}, dtype={img.dtype})")

    # Try to find the corresponding ground-truth mask
    out_mask = SELECTED_DIR / "bbbc005_mask.png"
    if gt_zip_path.exists():
        with zipfile.ZipFile(gt_zip_path) as gzf:
            gt_candidates = [n for n in gzf.namelist()
                              if n.upper().endswith(".TIF") and chosen_stem in n]
            if gt_candidates:
                with gzf.open(gt_candidates[0]) as mfh:
                    mask = tifffile.imread(mfh)
                if mask.ndim == 3:
                    mask = mask[:, :, 0]
                # BBBC005 GT is a binary mask (0 or 255); threshold to bool
                binary_mask = (mask > 127)
                Image.fromarray((binary_mask * 255).astype(np.uint8)).save(out_mask)
                print(f"  mask: {out_mask}  (foreground pixels: {binary_mask.sum():,})")
            else:
                print(f"  [warn] no matching GT for {chosen_stem}")
    return out_img


def select_fluo_gowt1_sample() -> Path | None:
    """Pick the first time point of Fluo-N2DH-GOWT1."""
    zip_path = RAW_DIR / "Fluo-N2DH-GOWT1.zip"
    if not zip_path.exists():
        print(f"  [skip] missing {zip_path}")
        return None
    with zipfile.ZipFile(zip_path) as zf:
        tif_names = [n for n in zf.namelist() if n.upper().endswith(".TIF")]
        tif_names.sort()
    chosen = tif_names[0]

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(chosen) as fh:
            img = tifffile.imread(fh)

    # CTC datasets store (T, H, W) or (1, H, W); squeeze the leading axis
    if img.ndim == 3:
        if img.shape[0] <= 4:
            img = img[0]
        else:
            img = img[:, :, 0]

    # Crop center 512x512 for tractability
    H, W = img.shape
    cy, cx = H // 2, W // 2
    half = 256
    crop = img[max(0, cy - half) : cy + half, max(0, cx - half) : cx + half]
    out = SELECTED_DIR / "fluo_gowt1_sample.png"
    _save_8bit(crop, out)
    print(f"  -> {out}  (shape={crop.shape})")
    return out


def select_bbbc034_sample() -> Path | None:
    """Pick a single plane from the BBBC034 hiPSC colony volume."""
    zip_path = RAW_DIR / "BBBC034_v1_dataset.zip"
    if not zip_path.exists():
        print(f"  [skip] missing {zip_path}")
        return None
    with zipfile.ZipFile(zip_path) as zf:
        # Skip macOS resource fork files (__MACOSX/._*)
        tif_names = sorted(
            n for n in zf.namelist()
            if n.lower().endswith(".tif")
            and not n.startswith("__MACOSX")
            and not n.split("/")[-1].startswith("._")
        )
    if not tif_names:
        return None
    print(f"  Found {len(tif_names)} TIF files: {tif_names[:3]}...")
    # Prefer the colony_center C=5 (Hoechst) nuclear channel of the first sample
    chosen = None
    for n in tif_names:
        if "colony_center" in n and "C=5" in n:
            chosen = n
            break
    if chosen is None:
        chosen = tif_names[len(tif_names) // 2]

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(chosen) as fh:
            img = tifffile.imread(fh)

    # BBBC034 stores (Z, H, W) for these volume files; pick middle Z
    if img.ndim == 3:
        # Could be (Z, H, W) - take middle z
        z_mid = img.shape[0] // 2
        img = img[z_mid]
    elif img.ndim == 4:
        img = img[0, 0]
    elif img.ndim == 2:
        pass  # already a 2D plane
    else:
        img = img.reshape(-1, img.shape[-2], img.shape[-1])[img.shape[0] // 2]

    H, W = img.shape
    cy, cx = H // 2, W // 2
    half = 256
    crop = img[max(0, cy - half) : cy + half, max(0, cx - half) : cx + half]
    out = SELECTED_DIR / "bbbc034_sample.png"
    _save_8bit(crop, out)
    print(f"  -> {out}  (shape={crop.shape})")
    return out


def main():
    print("Selecting BBBC005 sample...")
    select_bbbc005_sample()
    print("Selecting Fluo-N2DH-GOWT1 sample...")
    select_fluo_gowt1_sample()
    print("Selecting BBBC034 sample...")
    select_bbbc034_sample()
    print("\nAll selected images:")
    for f in sorted(SELECTED_DIR.iterdir()):
        print(f"  {f.name}: {f.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()