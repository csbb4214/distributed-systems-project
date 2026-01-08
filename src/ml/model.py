import torch
import torch.nn as nn
from torchvision import models


CLASS_NAMES = ["fire", "no_fire", "smoke"]


class FireSmokeNet(nn.Module):
    """
    Simple transfer learning model:
    ResNet18 backbone + 3-class classifier head (fire / no_fire / smoke).
    Output are logits for 3 classes (use softmax for probabilities).
    """
    def __init__(self, num_classes: int = 3):
        super().__init__()
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)
