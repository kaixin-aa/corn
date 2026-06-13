from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spectral.io.envi as envi
from skimage.segmentation import watershed


# Input HSI data. Only .hdr/.spe are required.
HDR_FILE = Path(r"D:\000_data\260603_corn\test.hdr")
SPE_FILE = Path(r"D:\000_data\260603_corn\test.spe")

# Segmentation parameters copied from the validated HSI-only workflow.
CORE_THRESHOLD = 90
LOOSE_THRESHOLD = 45
MIN_CORE_AREA = 500
MAX_CORE_AREA = 2500
MIN_CORE_WIDTH = 10
MAX_CORE_WIDTH = 80
MIN_CORE_HEIGHT = 10
MAX_CORE_HEIGHT = 80
EDGE_MARGIN = 20

SAVE_PIXEL_SPECTRA = True


def imwrite_unicode(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix or ".png"
    ok, encoded = cv2.imencode(ext, image)
    if not ok:
        raise IOError(f"Cannot encode image: {path}")
    encoded.tofile(str(path))


def robust_normalize_to_uint8(image: np.ndarray, p_low=1, p_high=99) -> np.ndarray:
    arr = np.asarray(image, dtype=np.float32)
    lo, hi = np.percentile(arr, (p_low, p_high))
    if hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)
    arr = np.clip((arr - lo) / (hi - lo), 0, 1)
    return (arr * 255).astype(np.uint8)


def get_default_band_indices(hsi, bands: int) -> list[int]:
    default_bands = hsi.metadata.get("default bands")
    if default_bands and len(default_bands) >= 3:
        return [max(0, min(bands - 1, int(item) - 1)) for item in default_bands[:3]]

    return [
        max(0, min(bands - 1, bands // 2)),
        max(0, min(bands - 1, bands // 3)),
        max(0, min(bands - 1, bands // 6)),
    ]


def build_hsi_pseudo_rgb(cube: np.ndarray, hsi, bands: int) -> np.ndarray:
    band_indices = get_default_band_indices(hsi, bands)
    channels = [
        robust_normalize_to_uint8(np.asarray(cube[:, :, band_idx], dtype=np.float32))
        for band_idx in band_indices
    ]
    return np.dstack(channels)


def detect_seed_labels(cube: np.ndarray, hsi, bands: int):
    pseudo_rgb = build_hsi_pseudo_rgb(cube, hsi, bands)
    hsv = cv2.cvtColor(pseudo_rgb, cv2.COLOR_RGB2HSV)
    value_image = hsv[:, :, 2]

    core_mask = (value_image > CORE_THRESHOLD).astype(np.uint8)
    num_labels, raw_labels, stats, centroids = cv2.connectedComponentsWithStats(core_mask, 8)

    marker_labels = np.zeros(core_mask.shape, dtype=np.int32)
    marker_id = 1
    core_records = []

    for old_id in range(1, num_labels):
        area = int(stats[old_id, cv2.CC_STAT_AREA])
        x = int(stats[old_id, cv2.CC_STAT_LEFT])
        y = int(stats[old_id, cv2.CC_STAT_TOP])
        w = int(stats[old_id, cv2.CC_STAT_WIDTH])
        h = int(stats[old_id, cv2.CC_STAT_HEIGHT])
        cx, cy = centroids[old_id]

        is_seed_core = (
            MIN_CORE_AREA <= area <= MAX_CORE_AREA
            and EDGE_MARGIN < x < pseudo_rgb.shape[1] - EDGE_MARGIN
            and EDGE_MARGIN < y < pseudo_rgb.shape[0] - EDGE_MARGIN
            and MIN_CORE_WIDTH <= w <= MAX_CORE_WIDTH
            and MIN_CORE_HEIGHT <= h <= MAX_CORE_HEIGHT
        )
        if not is_seed_core:
            continue

        marker_labels[raw_labels == old_id] = marker_id
        core_records.append(
            {
                "Marker_ID": marker_id,
                "Core_Area": area,
                "Core_BBox_X": x,
                "Core_BBox_Y": y,
                "Core_BBox_W": w,
                "Core_BBox_H": h,
                "Core_Center_Line": float(cy),
                "Core_Center_Sample": float(cx),
            }
        )
        marker_id += 1

    loose_mask = (value_image > LOOSE_THRESHOLD).astype(np.uint8)
    distance = cv2.distanceTransform(loose_mask, cv2.DIST_L2, 5)
    label_image = watershed(-distance, marker_labels, mask=loose_mask.astype(bool))
    binary_mask = label_image > 0

    print(f"Detected seed core count: {len(core_records)}")
    print(f"Seed mask pixel count: {int(np.sum(binary_mask))}")

    return label_image, binary_mask, pseudo_rgb, value_image, core_records


def estimate_row_gap_threshold(gaps: np.ndarray) -> float:
    valid_gaps = np.asarray([gap for gap in gaps if gap > 1e-6], dtype=float)
    if valid_gaps.size == 0:
        return np.inf

    unique_gaps = np.unique(valid_gaps)
    if unique_gaps.size == 1:
        return np.inf

    best_threshold = None
    best_loss = np.inf
    candidate_thresholds = (unique_gaps[:-1] + unique_gaps[1:]) / 2.0

    for threshold in candidate_thresholds:
        small_gaps = valid_gaps[valid_gaps <= threshold]
        large_gaps = valid_gaps[valid_gaps > threshold]
        if small_gaps.size == 0 or large_gaps.size == 0:
            continue

        loss = small_gaps.var() * small_gaps.size + large_gaps.var() * large_gaps.size
        if loss < best_loss:
            best_loss = loss
            best_threshold = threshold

    if best_threshold is None:
        return np.inf

    small_gaps = valid_gaps[valid_gaps <= best_threshold]
    large_gaps = valid_gaps[valid_gaps > best_threshold]
    if large_gaps.mean() < max(10.0, small_gaps.mean() * 2.0):
        return np.inf

    return float(best_threshold)


def sort_regions_top_down_left_right(region_records: list[dict]):
    if not region_records:
        return [], []

    sorted_by_y = sorted(region_records, key=lambda item: item["Centroid_Line"])
    if len(sorted_by_y) == 1:
        return sorted_by_y, [1]

    y_values = np.asarray([item["Centroid_Line"] for item in sorted_by_y], dtype=float)
    y_gaps = np.diff(y_values)
    row_gap_threshold = estimate_row_gap_threshold(y_gaps)

    rows = []
    current_row = [sorted_by_y[0]]
    for idx, gap in enumerate(y_gaps):
        if gap > row_gap_threshold:
            rows.append(current_row)
            current_row = []
        current_row.append(sorted_by_y[idx + 1])
    rows.append(current_row)

    rows = sorted(rows, key=lambda row: np.mean([item["Centroid_Line"] for item in row]))
    sorted_rows = [sorted(row, key=lambda item: item["Centroid_Sample"]) for row in rows]

    ordered = []
    for row in sorted_rows:
        ordered.extend(row)

    row_lengths = [len(row) for row in sorted_rows]
    return ordered, row_lengths


def renumber_labels(label_image: np.ndarray):
    region_records = []

    for region in regionprops_from_labels(label_image):
        region_records.append(
            {
                "Original_Label": int(region["label"]),
                "Centroid_Line": float(region["centroid_line"]),
                "Centroid_Sample": float(region["centroid_sample"]),
                "Pixel_Count": int(region["pixel_count"]),
                "BBox": region["bbox"],
            }
        )

    ordered_regions, row_lengths = sort_regions_top_down_left_right(region_records)
    print(f"Adaptive row grouping result: {row_lengths}")

    numbered_image = np.zeros_like(label_image, dtype=np.uint16)
    seed_map_rows = []

    for seed_id, record in enumerate(ordered_regions, start=1):
        original_label = record["Original_Label"]
        numbered_image[label_image == original_label] = seed_id
        min_row, min_col, max_row, max_col = record["BBox"]
        seed_map_rows.append(
            {
                "Seed_ID": seed_id,
                "Original_Label": original_label,
                "Centroid_Line": record["Centroid_Line"],
                "Centroid_Sample": record["Centroid_Sample"],
                "Pixel_Count": record["Pixel_Count"],
                "BBox_Min_Line": int(min_row),
                "BBox_Min_Sample": int(min_col),
                "BBox_Max_Line": int(max_row),
                "BBox_Max_Sample": int(max_col),
            }
        )

    return numbered_image, pd.DataFrame(seed_map_rows), ordered_regions


def regionprops_from_labels(label_image: np.ndarray):
    labels = [int(label) for label in np.unique(label_image) if label != 0]
    records = []

    for label in labels:
        coords = np.argwhere(label_image == label)
        if coords.size == 0:
            continue

        min_row, min_col = coords.min(axis=0)
        max_row, max_col = coords.max(axis=0) + 1
        centroid_line, centroid_sample = coords.mean(axis=0)
        records.append(
            {
                "label": label,
                "centroid_line": centroid_line,
                "centroid_sample": centroid_sample,
                "pixel_count": len(coords),
                "bbox": (min_row, min_col, max_row, max_col),
            }
        )

    return records


def format_wavelength(value) -> str:
    text = f"{float(value):.2f}"
    return text.rstrip("0").rstrip(".")


def build_band_columns(wavelengths) -> list[str]:
    return [
        f"Band_{idx + 1}_Wavelength_{format_wavelength(wavelengths[idx])}"
        for idx in range(len(wavelengths))
    ]


def save_spectra(cube: np.ndarray, numbered_image: np.ndarray, wavelengths, output_dir: Path, base_name: str):
    band_columns = build_band_columns(wavelengths)
    average_records = []
    pixel_dir = output_dir / f"{base_name}_pixel_spectra_by_seed"
    pixel_dir.mkdir(parents=True, exist_ok=True)

    seed_ids = [int(seed_id) for seed_id in np.unique(numbered_image) if seed_id != 0]

    for seed_id in seed_ids:
        coords = np.argwhere(numbered_image == seed_id)
        spectra = np.asarray(cube[coords[:, 0], coords[:, 1], :], dtype=np.float32)
        average = spectra.mean(axis=0)

        average_records.append(
            {
                "Seed_ID": seed_id,
                "Pixel_Count": int(len(coords)),
                **{band_columns[idx]: float(average[idx]) for idx in range(len(band_columns))},
            }
        )

        if SAVE_PIXEL_SPECTRA:
            pixel_df = pd.DataFrame(spectra, columns=band_columns)
            pixel_df.insert(0, "HSI_Sample", coords[:, 1])
            pixel_df.insert(0, "HSI_Line", coords[:, 0])
            pixel_df.insert(0, "Pixel_ID", np.arange(1, len(coords) + 1))
            pixel_df.insert(0, "Seed_ID", seed_id)
            pixel_df.to_csv(pixel_dir / f"seed_{seed_id:03d}_pixel_spectra.csv", index=False, float_format="%.8g")

        print(f"Saved seed {seed_id:03d}: {len(coords)} pixels")

    average_df = pd.DataFrame(average_records)
    average_file = output_dir / f"{base_name}_masked_spectra.csv"
    average_df.to_csv(average_file, index=False, float_format="%.8g")
    return average_df, average_file, pixel_dir


def save_overlay(pseudo_rgb: np.ndarray, numbered_image: np.ndarray, seed_map_df: pd.DataFrame, output_file: Path):
    overlay = cv2.cvtColor(pseudo_rgb, cv2.COLOR_RGB2BGR)

    for seed_id in seed_map_df["Seed_ID"]:
        mask = (numbered_image == int(seed_id)).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (0, 0, 255), 1)

    for _, row in seed_map_df.iterrows():
        cv2.putText(
            overlay,
            str(int(row["Seed_ID"])),
            (int(round(row["Centroid_Sample"])) + 3, int(round(row["Centroid_Line"])) - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    imwrite_unicode(output_file, overlay)


def save_analysis_plot(average_df: pd.DataFrame, wavelengths, output_file: Path):
    band_cols = [col for col in average_df.columns if col.startswith("Band_")]
    x = np.asarray(wavelengths, dtype=np.float64)

    plt.figure(figsize=(12, 7))
    for _, row in average_df.head(10).iterrows():
        plt.plot(x, row[band_cols].to_numpy(dtype=np.float64), label=f"Seed {int(row['Seed_ID'])}")

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title("Average Spectra of First 10 Seeds")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


def main():
    hsi = envi.open(str(HDR_FILE), str(SPE_FILE))
    cube = hsi.open_memmap(writable=False)
    lines, samples, bands = cube.shape
    wavelengths = hsi.bands.centers
    base_name = HDR_FILE.stem
    output_dir = Path(__file__).resolve().parent

    print(f"Loaded HSI data: {lines} lines x {samples} samples x {bands} bands")

    label_image, binary_mask, pseudo_rgb, value_image, core_records = detect_seed_labels(cube, hsi, bands)
    numbered_image, seed_map_df, _ = renumber_labels(label_image)

    seed_count = int(numbered_image.max())
    print(f"Detected and numbered {seed_count} seeds")

    imwrite_unicode(output_dir / f"{base_name}_hsi_pseudo_rgb.png", cv2.cvtColor(pseudo_rgb, cv2.COLOR_RGB2BGR))
    imwrite_unicode(output_dir / f"{base_name}_value_channel.png", value_image)
    imwrite_unicode(output_dir / f"{base_name}_seed_mask.png", (binary_mask.astype(np.uint8) * 255))
    imwrite_unicode(output_dir / f"{base_name}_numbered_labels.png", numbered_image)
    save_overlay(pseudo_rgb, numbered_image, seed_map_df, output_dir / f"{base_name}_masked_analysis.png")

    seed_map_df.to_csv(output_dir / f"{base_name}_seed_id_map.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(core_records).to_csv(output_dir / f"{base_name}_seed_core_candidates.csv", index=False, encoding="utf-8-sig")

    average_df, average_file, pixel_dir = save_spectra(cube, numbered_image, wavelengths, output_dir, base_name)
    save_analysis_plot(average_df, wavelengths, output_dir / f"{base_name}_average_spectra_preview.png")

    print(f"Average spectra saved to: {average_file}")
    if SAVE_PIXEL_SPECTRA:
        print(f"Pixel spectra saved to: {pixel_dir}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(f"File not found: {exc}")
    except Exception as exc:
        print(f"Error: {exc}")
