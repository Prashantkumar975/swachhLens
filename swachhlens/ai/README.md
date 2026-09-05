# SwachhLens AI Training

Train the waste detection models used by the SwachhLens backend.

## Models

| Model | Architecture | Purpose | Output |
|-------|-------------|---------|--------|
| Waste Gate V2 | MobileNetV3-small (2-class) | Binary waste vs non-waste filter | `waste_gate_v2_best.pth` |
| YOLO Detector | YOLOv11n (11 classes) | Detect specific waste objects | `waste_types_best.pt` |

## Pipeline

```
Image → [Waste Gate V2 ≥ 40%] → [YOLO ≥ 50%] → Map to 4 types → Return
         ↓ NO                      ↓ NO
         NON-WASTE                 NON-WASTE
```

## Quick Start

### 1. Install dependencies

```bash
cd ai/
pip install -r requirements.txt
```

### 2. Prepare your dataset

#### Binary dataset (for Waste Gate)
```bash
python prepare_data.py --source ./raw_images --output ./data --mode binary
```

Expected structure after preparation:
```
data/
    waste/          # waste images
    non_waste/      # non-waste images
```

#### YOLO dataset (for waste detector)
```bash
python prepare_data.py --source ./raw_images --output ./data --mode yolo
```

Expected structure after preparation:
```
data/
    images/
        train/      # training images
        val/        # validation images
    labels/
        train/      # YOLO labels (.txt)
        val/        # YOLO labels (.txt)
    data.yaml       # dataset config
```

### 3. Train Waste Gate V2

```bash
python train_waste_gate.py --data_dir ./data --epochs 20 --augment
```

Options:
- `--epochs 30` — more epochs for better convergence
- `--augment` — heavy data augmentation (rotation, color jitter)
- `--lr 0.0005` — lower learning rate for fine-tuning
- `--batch_size 16` — smaller batch for limited GPU memory

### 4. Train YOLO Detector

```bash
python train_yolo.py --data ./data/data.yaml --epochs 50 --img_size 640
```

Options:
- `--epochs 100` — more epochs for production
- `--batch 32` — larger batch for multi-GPU
- `--patience 20` — early stopping patience
- `--device 0` — specific GPU

### 5. Check dataset statistics

```bash
python train_yolo.py --data ./data/data.yaml --stats_only
```

## Data Sources

### TACO (Trash Annotations in Context)
- https://github.com/wolterwit/taco
- 1500+ images, 60 waste categories

### WasteNet
- https://github.com/garythung/WasteNet
- Binary waste/non-waste classification

### Custom Data
- Organize images into `waste/` and `non_waste/` folders
- For YOLO: add `.txt` label files with bounding boxes

## Model Files

After training, models are saved to `ai/models/`:
- `waste_gate_v2_best.pth` — best Waste Gate checkpoint
- `waste_types_best.pt` — best YOLO checkpoint

These are loaded by `ai/inference/analyze_image.py` at runtime.

## Tips

- Start with 20 epochs, check val accuracy, then increase
- Use `--augment` for small datasets (<1000 images)
- YOLO trains fast on GPU (~10 min for 50 epochs on 1000 images)
- Monitor val_loss — if it increases while train_loss decreases, you're overfitting
