"""Waste Gate V2 — Binary Waste Classifier Training.

Trains a MobileNetV3-small model to classify images as waste (1) or non-waste (0).

Expected dataset structure:
    data/
        waste/          # images containing waste (bottles, bags, dumps, etc.)
        non_waste/      # images without waste (landscapes, buildings, animals, etc.)

Usage:
    python train_waste_gate.py --data_dir ./data --epochs 20 --lr 0.001
    python train_waste_gate.py --data_dir ./data --epochs 30 --batch_size 32 --augment
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.models import mobilenet_v3_small


# ── Defaults ──────────────────────────────────────────────────────────
DEFAULT_DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "models"
IMAGE_SIZE = 224
NUM_CLASSES = 2  # waste / non-waste


def get_transforms(augment: bool = False, train: bool = True) -> transforms.Compose:
    """Build image transforms. Training uses augmentation when enabled."""
    if train and augment:
        return transforms.Compose([
            transforms.Resize((IMAGE_SIZE + 32, IMAGE_SIZE + 32)),
            transforms.RandomCrop(IMAGE_SIZE),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    elif train:
        return transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


def load_dataset(data_dir: Path, augment: bool):
    """Load waste / non-waste images from directory structure."""
    dataset = ImageFolder(root=str(data_dir), transform=get_transforms(augment=True, train=True))

    # Verify class mapping
    assert len(dataset.classes) == NUM_CLASSES, (
        f"Expected {NUM_CLASSES} classes (waste, non_waste), found {len(dataset.classes)}: {dataset.classes}"
    )
    print(f"Dataset loaded: {len(dataset)} images across {dataset.classes}")

    return dataset


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch. Returns (loss, accuracy)."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total if total > 0 else 0
    epoch_acc = correct / total if total > 0 else 0
    return epoch_loss, epoch_acc


def evaluate(model, loader, criterion, device):
    """Evaluate on validation set. Returns (loss, accuracy)."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total if total > 0 else 0
    epoch_acc = correct / total if total > 0 else 0
    return epoch_loss, epoch_acc


def main():
    parser = argparse.ArgumentParser(description="Train Waste Gate V2 (binary waste classifier)")
    parser.add_argument("--data_dir", type=str, default=str(DEFAULT_DATA_DIR),
                        help="Root data dir with waste/ and non_waste/ subdirectories")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--val_split", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--augment", action="store_true", help="Enable heavy data augmentation")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR / "waste_gate_v2_best.pth"),
                        help="Output model path")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        print(f"Expected structure:\n  {data_dir}/waste/     # waste images\n  {data_dir}/non_waste/ # non-waste images")
        return

    # ── Device ────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # ── Dataset ───────────────────────────────────────────────────────
    full_dataset = load_dataset(data_dir, augment=args.augment)

    val_size = int(len(full_dataset) * args.val_split)
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    # Override transforms for train/val splits
    train_dataset.dataset = None  # clear reference
    train_dataset = torch.utils.data.Subset(
        ImageFolder(root=str(data_dir), transform=get_transforms(augment=args.augment, train=True)),
        train_dataset.indices,
    )
    val_dataset = torch.utils.data.Subset(
        ImageFolder(root=str(data_dir), transform=get_transforms(augment=False, train=False)),
        val_dataset.indices,
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    print(f"Train: {len(train_dataset)} images | Val: {len(val_dataset)} images")

    # ── Model ─────────────────────────────────────────────────────────
    model = mobilenet_v3_small(weights=None, num_classes=NUM_CLASSES)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=3, factor=0.5)

    # ── Training loop ─────────────────────────────────────────────────
    best_val_acc = 0.0
    history = []

    print(f"\nStarting training for {args.epochs} epochs...\n")
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        elapsed = time.time() - t0
        lr = optimizer.param_groups[0]["lr"]
        print(
            f"Epoch {epoch:3d}/{args.epochs} | "
            f"Train loss: {train_loss:.4f} acc: {train_acc:.4f} | "
            f"Val loss: {val_loss:.4f} acc: {val_acc:.4f} | "
            f"lr: {lr:.6f} | {elapsed:.1f}s"
        )

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "lr": lr,
        })

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "epoch": epoch,
                "num_classes": NUM_CLASSES,
                "image_size": IMAGE_SIZE,
            }, output_path)
            print(f"  → Saved best model (val_acc={val_acc:.4f})")

    # ── Save training history ─────────────────────────────────────────
    history_path = Path(args.output).with_suffix(".history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\nTraining complete. Best val_acc: {best_val_acc:.4f}")
    print(f"Model saved to: {args.output}")
    print(f"History saved to: {history_path}")


if __name__ == "__main__":
    main()
