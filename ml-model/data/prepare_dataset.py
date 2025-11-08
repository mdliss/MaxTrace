"""
Dataset Preparation and Validation Script for Blueprint Detection
Validates YOLO format dataset and provides dataset statistics
"""
import os
import yaml
from pathlib import Path
from collections import defaultdict
import random
import shutil

def validate_dataset(data_yaml_path):
    """
    Validate YOLO dataset structure and format

    Args:
        data_yaml_path: Path to dataset YAML configuration

    Returns:
        dict: Validation results and statistics
    """
    print("=" * 60)
    print("BLUEPRINT DATASET VALIDATION")
    print("=" * 60)

    # Load dataset config
    with open(data_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    dataset_path = Path(config['path'])
    stats = {
        'train': defaultdict(int),
        'val': defaultdict(int),
        'test': defaultdict(int),
        'errors': [],
        'warnings': []
    }

    # Validate directory structure
    required_dirs = ['images/train', 'images/val', 'labels/train', 'labels/val']
    for dir_path in required_dirs:
        full_path = dataset_path / dir_path
        if not full_path.exists():
            stats['errors'].append(f"Missing directory: {full_path}")
            print(f"❌ Missing: {full_path}")
        else:
            print(f"✅ Found: {full_path}")

    if stats['errors']:
        print(f"\n⚠️  {len(stats['errors'])} errors found. Please fix before training.")
        return stats

    # Validate images and labels
    for split in ['train', 'val', 'test']:
        img_dir = dataset_path / f'images/{split}'
        label_dir = dataset_path / f'labels/{split}'

        if not img_dir.exists():
            continue

        images = list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.png'))
        stats[split]['total_images'] = len(images)

        print(f"\n{split.upper()} SET:")
        print(f"  Images: {len(images)}")

        # Check each image has corresponding label
        missing_labels = 0
        class_counts = defaultdict(int)

        for img_path in images:
            label_path = label_dir / f"{img_path.stem}.txt"

            if not label_path.exists():
                missing_labels += 1
                stats['warnings'].append(f"Missing label for {img_path.name}")
            else:
                # Parse label file
                with open(label_path, 'r') as f:
                    lines = f.readlines()
                    stats[split]['total_annotations'] += len(lines)

                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) == 5:
                            class_id = int(parts[0])
                            class_counts[class_id] += 1
                        else:
                            stats['errors'].append(f"Invalid annotation in {label_path.name}")

        stats[split]['missing_labels'] = missing_labels
        stats[split]['class_distribution'] = dict(class_counts)

        if missing_labels > 0:
            print(f"  ⚠️  Missing labels: {missing_labels}")

        # Print class distribution
        print(f"  Annotations: {stats[split]['total_annotations']}")
        if class_counts:
            print(f"  Class Distribution:")
            class_names = config.get('names', [])
            for class_id, count in sorted(class_counts.items()):
                class_name = class_names[class_id] if class_id < len(class_names) else f"Class {class_id}"
                print(f"    {class_name}: {count}")

    # Validation summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    train_images = stats['train']['total_images']
    val_images = stats['val']['total_images']

    if train_images < 50:
        stats['warnings'].append(f"Training set is small ({train_images} images). Recommend 100+ for good results.")
        print(f"⚠️  Small training set: {train_images} images (recommend 100+)")
    else:
        print(f"✅ Training set size: {train_images} images")

    if val_images < 10:
        stats['warnings'].append(f"Validation set is small ({val_images} images). Recommend 20+.")
        print(f"⚠️  Small validation set: {val_images} images (recommend 20+)")
    else:
        print(f"✅ Validation set size: {val_images} images")

    if stats['errors']:
        print(f"\n❌ {len(stats['errors'])} ERRORS found")
    else:
        print(f"\n✅ Dataset is valid and ready for training!")

    if stats['warnings']:
        print(f"⚠️  {len(stats['warnings'])} warnings (review recommended)")

    return stats


def create_sample_structure(output_dir='./data/blueprints'):
    """
    Create sample dataset directory structure

    Args:
        output_dir: Output directory path
    """
    output_path = Path(output_dir)

    dirs = [
        'images/train',
        'images/val',
        'images/test',
        'labels/train',
        'labels/val',
        'labels/test'
    ]

    print(f"\nCreating dataset structure at: {output_path}")

    for dir_name in dirs:
        dir_path = output_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")

    # Create README
    readme_content = """# Blueprint Dataset

## Directory Structure

images/
├── train/    - Training images (PNG/JPG)
├── val/      - Validation images
└── test/     - Test images (optional)

labels/
├── train/    - Training annotations (.txt)
├── val/      - Validation annotations
└── test/     - Test annotations (optional)

## Annotation Format

Each image should have a corresponding .txt file with the same name.

Format per line: <class_id> <x_center> <y_center> <width> <height>

All values normalized to 0-1 range.

Example annotation (door at center of image):
1 0.5 0.5 0.1 0.15

## Classes

0: wall
1: door
2: window
3: room
4: stair
5: furniture
6: fixture

## Recommended Tools

- LabelImg: https://github.com/heartexlabs/labelImg
- Roboflow: https://roboflow.com
- CVAT: https://github.com/opencv/cvat

## Dataset Requirements

- Minimum 100 training images recommended
- Minimum 20 validation images recommended
- Images should be clear blueprint/floorplan images
- Annotations should be accurate bounding boxes around elements
"""

    readme_path = output_path / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"\n✅ Dataset structure created!")
    print(f"📝 README created: {readme_path}")
    print(f"\nNext steps:")
    print(f"1. Add blueprint images to images/train/ and images/val/")
    print(f"2. Annotate images using LabelImg or similar tool")
    print(f"3. Export annotations in YOLO format to labels/ directories")
    print(f"4. Run validation: python prepare_dataset.py --validate")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Blueprint Dataset Preparation')
    parser.add_argument('--validate', action='store_true',
                       help='Validate existing dataset')
    parser.add_argument('--create-structure', action='store_true',
                       help='Create sample dataset directory structure')
    parser.add_argument('--data-yaml', type=str,
                       default='blueprint_dataset.yaml',
                       help='Path to dataset YAML configuration')
    parser.add_argument('--output-dir', type=str,
                       default='./data/blueprints',
                       help='Output directory for dataset structure')

    args = parser.parse_args()

    if args.create_structure:
        create_sample_structure(args.output_dir)

    if args.validate:
        stats = validate_dataset(args.data_yaml)

        # Exit with error code if validation failed
        if stats['errors']:
            exit(1)
