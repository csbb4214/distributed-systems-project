import base64
import json
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from torchvision import transforms

from model import FireSmokeNet

app = FastAPI()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load labels mapping
HERE = Path(__file__).resolve().parent
labels_path = HERE / "labels.json"
model_path = HERE / "model_state.pt"

if not labels_path.exists():
    raise RuntimeError(f"Missing labels.json. Run train.py first: {labels_path}")
if not model_path.exists():
    raise RuntimeError(f"Missing model_state.pt. Run train.py first: {model_path}")

class_to_idx = json.loads(labels_path.read_text(encoding="utf-8"))
idx_to_class = {v: k for k, v in class_to_idx.items()}
num_classes = len(idx_to_class)

model = FireSmokeNet(num_classes=num_classes).to(device)
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()

preprocess = transforms.Compose([
    transforms.ToTensor(),  # expects RGB HxWxC in [0..255] -> float [0..1]
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


class InferRequest(BaseModel):
    frame_jpeg_b64: str


@app.post("/infer")
def infer(req: InferRequest) -> Dict[str, Any]:
    # decode base64 jpeg -> numpy BGR (cv2)
    jpeg_bytes = base64.b64decode(req.frame_jpeg_b64)
    np_arr = np.frombuffer(jpeg_bytes, np.uint8)
    frame_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame_bgr is None:
        return {"error": "Could not decode JPEG"}

    # BGR -> RGB, resize to 224x224
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.resize(frame_rgb, (224, 224))

    x = preprocess(frame_rgb).unsqueeze(0).to(device)  # [1,3,224,224]

    with torch.no_grad():
        logits = model(x)  # [1,num_classes]
        probs = torch.softmax(logits, dim=1).squeeze(0)  # [num_classes]

    pred_idx = int(torch.argmax(probs).item())
    pred_class = idx_to_class[pred_idx]
    confidence = float(probs[pred_idx].item())

    # return all probs
    probs_dict = {idx_to_class[i]: float(probs[i].item()) for i in range(num_classes)}

    return {
        "predicted_class": pred_class,
        "confidence": confidence,
        "probs": probs_dict
    }
