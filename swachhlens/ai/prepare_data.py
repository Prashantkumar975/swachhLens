"""Data Preparation Utility for SwachhLens AI Training.

Converts raw image datasets into the formats needed by:
  1. train_waste_gate.py — binary waste/non-waste classification
  2. train_yolo.py — YOLO object detection

Supports common dataset sources:
  - TACO (Trash Annotations in Context)
  - WasteNet
  - Custom folders with images + annotations

Usage:
    # Prepare binary dataset for Waste Gate
    python prepare_data.py --source ./raw_data --output ./data --mode binary

    # Prepare YOLO dataset for waste detector
    python prepare_data.py --source ./raw_data --output ./data --mode yolo

    # Split existing dataset into train/val
    python prepare_data.py --source ./data --output ./data_split --mode split --val_ratio 0.2
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path


# ── Waste type mapping ────────────────────────────────────────────────
# Maps various dataset class names to our 4 app types
WASTE_TYPE_MAP = {
    # Plastic
    "plastic": "Plastic", "bottle": "Plastic", "bag": "Plastic",
    "packaging": "Plastic", "wrapper": "Plastic", "container": "Plastic",
    "cup": "Plastic", "straw": "Plastic", "cutlery": "Plastic",
    "recyclable": "Plastic", "nylon": "Plastic", "styrofoam": "Plastic",
    # Organic
    "organic": "Organic", "food": "Organic", "fruit": "Organic",
    "vegetable": "Organic", "compost": "Organic", "garden": "Organic",
    "biodegradable": "Organic", "wood": "Organic",
    # E-Waste
    "electronic": "E-Waste", "battery": "E-Waste", "cable": "E-Waste",
    "phone": "E-Waste", "computer": "E-Waste", "e-waste": "E-Waste",
    # Hazardous
    "hazardous": "Hazardous", "chemical": "Hazardous", "paint": "Hazardous",
    "medical": "Hazardous", "sharp": "Hazardous", "syringe": "Hazardous",
}


def is_waste_image(path: Path) -> bool:
    """Heuristic: does this filename suggest it's a waste image?"""
    name = path.stem.lower()
    return any(kw in name for kw in [
        "waste", "trash", "garbage", "litter", "dump", "recycle",
        "plastic", "bottle", "bag", "organic", "food", "e-waste",
        "hazardous", "medical", "chemical", "taco", "wasteNet",
    ])


def is_non_waste_image(path: Path) -> bool:
    """Heuristic: does this filename suggest it's NOT waste?"""
    name = path.stem.lower()
    return any(kw in name for kw in [
        "landscape", "nature", "building", "animal", "person",
        "street", "clean", "park", "garden", "city", "sky",
    ])


def prepare_binary(source_dir: Path, output_dir: Path):
    """Prepare binary waste/non-waste dataset for Waste Gate V2."""
    waste_dir = output_dir / "waste"
    non_waste_dir = output_dir / "non_waste"
    waste_dir.mkdir(parents=True, exist_ok=True)
    non_waste_dir.mkdir(parents=True, exist_ok=True)

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    waste_count = 0
    non_waste_count = 0

    print(f"Scanning {source_dir} for images...")

    for img_path in source_dir.rglob("*"):
        if img_path.suffix.lower() not in image_exts:
            continue

        if is_waste_image(img_path):
            dest = waste_dir / img_path.name
            shutil.copy2(img_path, dest)
            waste_count += 1
        elif is_non_waste_image(img_path):
            dest = non_waste_dir / img_path.name
            shutil.copy2(img_path, dest)
            non_waste_count += 1

    print(f"\nBinary dataset created at {output_dir}:")
    print(f"  waste/:     {waste_count} images")
    print(f"  non_waste/: {non_waste_count} images")
    print(f"  Total:      {waste_count + non_waste_count} images")

    if waste_count == 0 or non_waste_count == 0:
        print("\nWARNING: One class has no images. The Waste Gate needs both waste")
        print("and non-waste images to train. Add more images and re-run.")


def prepare_yolo(source_dir: Path, output_dir: Path):
    """Prepare YOLO-format dataset for waste detector."""
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"

    for split in ["train", "val"]:
        (images_dir / split).mkdir(parents=True, exist_ok=True)
        (labels_dir / split).mkdir(parents=True, exist_ok=True)

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = []

    print(f"Scanning {source_dir} for images + annotations...")

    # Collect all images
    for img_path in source_dir.rglob("*"):
        if img_path.suffix.lower() in image_exts:
            images.append(img_path)

    if not images:
        print(f"ERROR: No images found in {source_dir}")
        return

    # Shuffle and split 80/20
    random.seed(42)
    random.shuffle(images)
    split_idx = int(len(images) * 0.8)
    train_images = images[:split_idx]
    val_images = images[split_idx:]

    def copy_split(image_list, split_name):
        count = 0
        for img_path in image_list:
            # Copy image
            dest_img = images_dir / split_name / img_path.name
            shutil.copy2(img_path, dest_img)

            # Look for matching label file (.txt with same stem)
            label_path = img_path.with_suffix(".txt")
            if label_path.exists():
                dest_label = labels_dir / split_name / label_path.name
                shutil.copy2(label_path, dest_label)
                count += 1

        return count

    train_labels = copy_split(train_images, "train")
    val_labels = copy_split(val_images, "val")

    print(f"\nYOLO dataset created at {output_dir}:")
    print(f"  train/: {len(train_images)} images, {train_labels} with labels")
    print(f"  val/:   {len(val_images)} images, {val_labels} with labels")

    # Generate data.yaml
    nc = len(WASTE_TYPE_MAP)
    names_str = "\n".join(f"  {i}: {name}" for i, name in enumerate(WASTE_TYPE_MAP))
    yaml_content = f"""# SwachhLens Waste Detector — Auto-generated
train: {(images_dir / 'train').resolve()}
val: {(images_dir / 'val').resolve()}
nc: {nc}
names:
{names_str}
"""
    yaml_path = output_dir / "data.yaml"
    yaml_path.write_text(yaml_content)
    print(f"\nGenerated: {yaml_path}")


def split_dataset(source_dir: Path, output_dir: Path, val_ratio: float):
    """Split an existing dataset into train/val."""
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    images = [f for f in source_dir.iterdir() if f.suffix.lower() in image_exts]
    random.seed(42)
    random.shuffle(images)

    split_idx = int(len(images) * (1 - val_ratio))
    train_images = images[:split_idx]
    val_images = images[split_idx:]

    for split_name, image_list in [("train", train_images), ("val", val_images)]:
        split_dir = output_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        for img in image_list:
            shutil.copy2(img, split_dir / img.name)
            label = img.with_suffix(".txt")
            if label.exists():
                shutil.copy2(label, split_dir / label.name)

    print(f"Split complete:")
    print(f"  train/: {len(train_images)} images")
    print(f"  val/:   {len(val_images)} images")


def main():
    parser = argparse.ArgumentParser(description="Prepare data for SwachhLens AI training")
    parser.add_argument("--source", required=True, help="Source data directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--mode", choices=["binary", "yolo", "split"], required=True,
                        help="binary = waste/non-waste for Waste Gate, yolo = YOLO format, split = train/val split")
    parser.add_argument("--val_ratio", type=float, default=0.2, help="Validation split ratio (for split mode)")
    args = parser.parse_args()

    source = Path(args.source)
    output = Path(args.output)

    if not source.exists():
        print(f"ERROR: Source directory not found: {source}")
        return

    if args.mode == "binary":
        prepare_binary(source, output)
    elif args.mode == "yolo":
        prepare_yolo(source, output)
    elif args.mode == "split":
        split_dataset(source, output, args.val_ratio)


if __name__ == "__main__":
    main()
