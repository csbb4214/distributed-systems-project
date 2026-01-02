import torch
import torch.nn as nn

class FireCNN(nn.Module):
    def __init__(self):
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, stride=2),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Linear(64, 1)

    def forward(self, x):
        x = self.net(x)
        x = x.view(x.size(0), -1)
        return torch.sigmoid(self.classifier(x))
