"""
Script to help acquire sample blueprint datasets for training
Provides guidance and tools for dataset acquisition
"""
import os
import sys
from pathlib import Path

def print_dataset_sources():
    """Print information about available blueprint dataset sources"""

    print("\n" + "="*70)
    print("BLUEPRINT DATASET ACQUISITION GUIDE")
    print("="*70)

    print("\n📁 OPTION 1: Public Datasets")
    print("-" * 70)
    print("""
1. CubiCasa5K Dataset (Recommended)
   - Source: https://github.com/CubiCasa/CubiCasa5k
   - Content: 5000 floorplans with room labels
   - Format: Needs conversion to YOLO format
   - License: Research use

2. RPLAN Dataset
   - Source: http://staff.ustc.edu.cn/~fuxm/projects/DeepLayout/index.html
   - Content: 80,000+ residential floorplans
   - Format: Needs conversion to YOLO format

3. Kaggle Floorplan Datasets
   - Search: https://www.kaggle.com/search?q=floorplan
   - Various datasets with different formats
   - Check licenses before use
    """)

    print("\n🎨 OPTION 2: Create Your Own Dataset")
    print("-" * 70)
    print("""
1. Collect Blueprint Images
   - Scan physical blueprints
   - Download from architecture websites
   - Use CAD software to generate samples
   - Target: 100+ images minimum

2. Annotation Tools
   - LabelImg: https://github.com/heartexlabs/labelImg
     * Free, open-source
     * Easy to use GUI
     * Direct YOLO export

   - Roboflow: https://roboflow.com
     * Web-based
     * Auto-augmentation
     * Free tier available
     * YOLO export included

   - CVAT: https://github.com/opencv/cvat
     * Advanced features
     * Team collaboration
     * Self-hosted or cloud

3. Annotation Process
   - Draw bounding boxes around elements
   - Label each element (wall, door, window, etc.)
   - Export in YOLO format
   - Split into train/val sets (80/20)
    """)

    print("\n🤖 OPTION 3: Use Synthetic Data (For Testing)")
    print("-" * 70)
    print("""
Generate simple synthetic blueprints for initial testing:
   - Use this script: python download_sample_data.py --generate-synthetic
   - Creates basic floorplan-like images
   - Good for testing pipeline, not for production
   - Should be replaced with real data for final model
    """)

    print("\n📝 RECOMMENDED WORKFLOW")
    print("-" * 70)
    print("""
For MaxTrace Production Model:

1. START: Generate synthetic data for pipeline testing
   → python download_sample_data.py --generate-synthetic
   → Test training and deployment pipeline

2. INTERMEDIATE: Use public dataset (CubiCasa5K)
   → Download and convert to YOLO format
   → Train baseline model
   → Evaluate performance

3. PRODUCTION: Create custom annotated dataset
   → Collect 200+ blueprint images relevant to your use case
   → Annotate using Roboflow or LabelImg
   → Include diverse architectural styles
   → Fine-tune model for your specific needs
    """)

    print("\n" + "="*70)

def generate_synthetic_data(output_dir='./blueprints', num_images=50):
    """
    Generate synthetic blueprint-like images for testing

    Args:
        output_dir: Output directory for generated dataset
        num_images: Number of synthetic images to generate
    """
    try:
        from PIL import Image, ImageDraw
        import random
    except ImportError:
        print("❌ Error: PIL (Pillow) not installed")
        print("Install with: pip install pillow")
        return

    output_path = Path(output_dir)

    # Create directory structure
    for split in ['train', 'val']:
        (output_path / f'images/{split}').mkdir(parents=True, exist_ok=True)
        (output_path / f'labels/{split}').mkdir(parents=True, exist_ok=True)

    print(f"\n🎨 Generating {num_images} synthetic blueprint images...")

    train_count = int(num_images * 0.8)
    val_count = num_images - train_count

    for i in range(num_images):
        split = 'train' if i < train_count else 'val'

        # Create blank image (white background)
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)

        annotations = []

        # Draw room boundary (large rectangle)
        room_x1 = random.randint(50, 150)
        room_y1 = random.randint(50, 100)
        room_x2 = random.randint(650, 750)
        room_y2 = random.randint(500, 550)

        # Draw walls (thick black lines)
        wall_width = 5
        draw.rectangle([room_x1, room_y1, room_x2, room_y1 + wall_width], fill='black')
        draw.rectangle([room_x1, room_y2 - wall_width, room_x2, room_y2], fill='black')
        draw.rectangle([room_x1, room_y1, room_x1 + wall_width, room_y2], fill='black')
        draw.rectangle([room_x2 - wall_width, room_y1, room_x2, room_y2], fill='black')

        # Add doors (gaps in walls with arc)
        num_doors = random.randint(1, 3)
        for _ in range(num_doors):
            wall = random.choice(['top', 'bottom', 'left', 'right'])
            if wall == 'bottom':
                door_x = random.randint(room_x1 + 100, room_x2 - 100)
                door_w = 60
                draw.rectangle([door_x, room_y2 - wall_width, door_x + door_w, room_y2], fill='white')
                draw.arc([door_x, room_y2 - 60, door_x + door_w, room_y2], 0, 180, fill='black', width=2)

                # YOLO annotation: class 1 (door), normalized coordinates
                x_center = (door_x + door_w/2) / 800
                y_center = room_y2 / 600
                width = door_w / 800
                height = 60 / 600
                annotations.append(f"1 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        # Add windows
        num_windows = random.randint(1, 4)
        for _ in range(num_windows):
            wall = random.choice(['top', 'left', 'right'])
            if wall == 'top':
                win_x = random.randint(room_x1 + 100, room_x2 - 150)
                win_w = 50
                draw.rectangle([win_x, room_y1, win_x + win_w, room_y1 + wall_width], fill='gray')
                draw.line([win_x + win_w//2, room_y1, win_x + win_w//2, room_y1 + wall_width], fill='black', width=1)

                # YOLO annotation: class 2 (window)
                x_center = (win_x + win_w/2) / 800
                y_center = (room_y1 + wall_width/2) / 600
                width = win_w / 800
                height = wall_width / 600
                annotations.append(f"2 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        # Save image
        img_path = output_path / f'images/{split}/blueprint_{i:04d}.png'
        img.save(img_path)

        # Save annotations
        label_path = output_path / f'labels/{split}/blueprint_{i:04d}.txt'
        with open(label_path, 'w') as f:
            f.write('\n'.join(annotations))

        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_images} images...")

    print(f"\n✅ Synthetic dataset generated!")
    print(f"📁 Location: {output_path}")
    print(f"📊 Train: {train_count} images, Val: {val_count} images")
    print(f"\nNext steps:")
    print(f"1. Review generated images in {output_path}/images/")
    print(f"2. Update blueprint_dataset.yaml with path: {output_path}")
    print(f"3. Run training with: python training/train_enhanced.py")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Blueprint Dataset Acquisition Helper')
    parser.add_argument('--generate-synthetic', action='store_true',
                       help='Generate synthetic blueprint images for testing')
    parser.add_argument('--num-images', type=int, default=50,
                       help='Number of synthetic images to generate')
    parser.add_argument('--output-dir', type=str, default='./blueprints',
                       help='Output directory for synthetic dataset')

    args = parser.parse_args()

    if args.generate_synthetic:
        generate_synthetic_data(args.output_dir, args.num_images)
    else:
        # Show dataset acquisition guide
        print_dataset_sources()

        print("\n💡 QUICK START")
        print("-" * 70)
        print("To generate synthetic data for testing:")
        print("  python download_sample_data.py --generate-synthetic --num-images=50")
        print("\nTo see this guide again:")
        print("  python download_sample_data.py")
        print("="*70 + "\n")
