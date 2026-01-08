import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms

from model import FireSmokeNet


def main():
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "src" / "ml" / "data"
    out_dir = Path(__file__).resolve().parent

    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset folder not found: {data_dir}")

    # Transforms
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    # Load dataset (expects subfolders = class names)
    full_ds = datasets.ImageFolder(root=str(data_dir), transform=train_tf)

    if len(full_ds) == 0:
        raise RuntimeError(f"No images found under {data_dir}")

    # Save label mapping for inference
    labels_path = out_dir / "labels.json"
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(full_ds.class_to_idx, f, indent=2)
    print("Saved labels mapping to:", labels_path)
    print("class_to_idx:", full_ds.class_to_idx)

    # Split
    val_ratio = 0.2
    val_size = max(1, int(len(full_ds) * val_ratio))
    train_size = len(full_ds) - val_size
    train_ds, val_ds = random_split(full_ds, [train_size, val_size])

    # Use val transforms on validation subset
    val_ds.dataset.transform = val_tf

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=16, shuffle=False, num_workers=0)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

    model = FireSmokeNet(num_classes=len(full_ds.classes)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    epochs = 5
    for epoch in range(1, epochs + 1):
        # Train
        model.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)

            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        # Validate
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                loss = criterion(logits, y)
                val_loss += loss.item()

                preds = logits.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        print(
            f"Epoch {epoch}/{epochs} | "
            f"train_loss={train_loss/len(train_loader):.4f} | "
            f"val_loss={val_loss/len(val_loader):.4f} | "
            f"val_acc={correct/total:.3f}"
        )

    # Save weights
    model_path = out_dir / "model_state.pt"
    torch.save(model.state_dict(), model_path)
    print("Saved model weights to:", model_path)


if __name__ == "__main__":
    main()
