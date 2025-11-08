"""
YOLOv5 Training Script for Blueprint Room Detection
"""
import torch
import yaml
import os
from pathlib import Path

# Clone YOLOv5 repo if not exists
def setup_yolov5():
    if not os.path.exists('yolov5'):
        os.system('git clone https://github.com/ultralytics/yolov5.git')
        os.system('pip install -r yolov5/requirements.txt')

def train_model(data_yaml, epochs=100, img_size=640, batch_size=16):
    """
    Train YOLOv5 model on blueprint dataset

    Args:
        data_yaml: Path to dataset configuration YAML
        epochs: Number of training epochs
        img_size: Input image size
        batch_size: Training batch size
    """
    setup_yolov5()

    # Training command
    train_cmd = f"""
    python yolov5/train.py \
        --img {img_size} \
        --batch {batch_size} \
        --epochs {epochs} \
        --data {data_yaml} \
        --weights yolov5m.pt \
        --project runs/train \
        --name blueprint_detector \
        --cache \
        --device 0
    """

    print(f"Starting training with command:\n{train_cmd}")
    os.system(train_cmd)

    print("Training complete! Model saved in runs/train/blueprint_detector/weights/best.pt")

if __name__ == '__main__':
    # Path to your dataset configuration
    data_yaml = '../data/blueprint_dataset.yaml'

    if not os.path.exists(data_yaml):
        print(f"Error: Dataset configuration not found at {data_yaml}")
        print("Please create the dataset configuration file first.")
        exit(1)

    train_model(
        data_yaml=data_yaml,
        epochs=100,
        img_size=640,
        batch_size=16
    )
