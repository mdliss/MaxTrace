"""
Enhanced YOLOv5 Training Script for Blueprint Architectural Elements Detection
Supports multiple architectural element classes and advanced configuration
"""
import torch
import yaml
import os
import argparse
from pathlib import Path
import json
from datetime import datetime

def setup_yolov5():
    """Clone and setup YOLOv5 repository"""
    if not os.path.exists('yolov5'):
        print("Cloning YOLOv5 repository...")
        os.system('git clone https://github.com/ultralytics/yolov5.git')
        os.system('pip install -r yolov5/requirements.txt')
    else:
        print("YOLOv5 repository already exists")

def validate_dataset(data_yaml):
    """Run dataset validation before training"""
    print("\n" + "="*60)
    print("VALIDATING DATASET")
    print("="*60)

    validation_script = Path('../data/prepare_dataset.py')
    if validation_script.exists():
        os.system(f'python {validation_script} --validate --data-yaml={data_yaml}')
    else:
        print("⚠️  Dataset validation script not found. Skipping validation.")

def train_model(
    data_yaml='../data/blueprint_dataset.yaml',
    epochs=100,
    img_size=640,
    batch_size=16,
    weights='yolov5m.pt',
    project='runs/train',
    name='blueprint_detector',
    device='0',
    cache=True,
    hyp='hyp.scratch-low.yaml',
    patience=20,
    save_period=10,
    workers=8
):
    """
    Train YOLOv5 model on blueprint architectural elements dataset

    Args:
        data_yaml: Path to dataset configuration YAML
        epochs: Number of training epochs
        img_size: Input image size
        batch_size: Training batch size
        weights: Pre-trained weights (yolov5s/m/l/x.pt)
        project: Project directory for results
        name: Experiment name
        device: CUDA device (0, 1, 2, or 'cpu')
        cache: Cache images for faster training
        hyp: Hyperparameters configuration file
        patience: Early stopping patience
        save_period: Save checkpoint every N epochs
        workers: Number of dataloader workers
    """

    setup_yolov5()

    # Validate dataset first
    if not os.path.exists(data_yaml):
        print(f"❌ Error: Dataset configuration not found at {data_yaml}")
        print("Please create the dataset configuration file first.")
        exit(1)

    validate_dataset(data_yaml)

    # Load dataset config to show class info
    with open(data_yaml, 'r') as f:
        config = yaml.safe_load(f)

    print("\n" + "="*60)
    print("TRAINING CONFIGURATION")
    print("="*60)
    print(f"Dataset: {data_yaml}")
    print(f"Classes ({config.get('nc', 'unknown')}): {config.get('names', [])}")
    print(f"Epochs: {epochs}")
    print(f"Image Size: {img_size}")
    print(f"Batch Size: {batch_size}")
    print(f"Base Weights: {weights}")
    print(f"Device: {device}")
    print(f"Project: {project}")
    print(f"Name: {name}")
    print("="*60 + "\n")

    # Check if GPU is available
    if device != 'cpu' and not torch.cuda.is_available():
        print("⚠️  GPU not available, falling back to CPU")
        device = 'cpu'

    # Build training command
    train_cmd = f"""python yolov5/train.py \
        --img {img_size} \
        --batch {batch_size} \
        --epochs {epochs} \
        --data {data_yaml} \
        --weights {weights} \
        --project {project} \
        --name {name} \
        --device {device} \
        --workers {workers} \
        --patience {patience} \
        --save-period {save_period}"""

    if cache:
        train_cmd += " --cache"

    print(f"Starting training...\n")
    print(f"Command: {train_cmd}\n")

    # Record start time
    start_time = datetime.now()

    # Run training
    result = os.system(train_cmd)

    # Record end time
    end_time = datetime.now()
    duration = end_time - start_time

    if result == 0:
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print(f"Duration: {duration}")
        print(f"Model saved to: {project}/{name}/weights/best.pt")
        print(f"Results: {project}/{name}/")
        print("\nNext steps:")
        print("1. Review training metrics in results directory")
        print("2. Test model with validation images")
        print("3. Deploy to SageMaker using deployment/deploy_sagemaker.py")
    else:
        print("\n❌ Training failed. Check logs for errors.")
        exit(1)

    return f"{project}/{name}/weights/best.pt"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train YOLOv5 for Blueprint Detection')

    # Dataset parameters
    parser.add_argument('--data', type=str, default='../data/blueprint_dataset.yaml',
                       help='Path to dataset YAML configuration')

    # Training parameters
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16,
                       help='Training batch size')
    parser.add_argument('--img-size', type=int, default=640,
                       help='Input image size')
    parser.add_argument('--weights', type=str, default='yolov5m.pt',
                       choices=['yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt'],
                       help='Pre-trained weights (s=small, m=medium, l=large, x=xlarge)')

    # Output parameters
    parser.add_argument('--project', type=str, default='runs/train',
                       help='Project directory for results')
    parser.add_argument('--name', type=str, default='blueprint_detector',
                       help='Experiment name')

    # Device parameters
    parser.add_argument('--device', type=str, default='0',
                       help='CUDA device (0, 1, 2, etc.) or cpu')
    parser.add_argument('--workers', type=int, default=8,
                       help='Number of dataloader workers')

    # Performance parameters
    parser.add_argument('--cache', action='store_true', default=True,
                       help='Cache images for faster training')
    parser.add_argument('--patience', type=int, default=20,
                       help='Early stopping patience (epochs)')
    parser.add_argument('--save-period', type=int, default=10,
                       help='Save checkpoint every N epochs')

    args = parser.parse_args()

    # Train model
    model_path = train_model(
        data_yaml=args.data,
        epochs=args.epochs,
        img_size=args.img_size,
        batch_size=args.batch_size,
        weights=args.weights,
        project=args.project,
        name=args.name,
        device=args.device,
        cache=args.cache,
        patience=args.patience,
        save_period=args.save_period,
        workers=args.workers
    )

    print(f"\n✅ Trained model: {model_path}")
