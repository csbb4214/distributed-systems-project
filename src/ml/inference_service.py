import base64
import cv2
import numpy as np
import torch
from fastapi import FastAPI
from model import FireCNN

app = FastAPI()

model = FireCNN()
model.load_state_dict(torch.load("fire_model.pt", map_location="cpu"))
model.eval()

@app.post("/infer")
def infer(payload: dict):
    img_bytes = base64.b64decode(payload["frame"])
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    img = cv2.resize(img, (224, 224))
    img = torch.tensor(img).permute(2, 0, 1).float() / 255.0
    img = img.unsqueeze(0)

    with torch.no_grad():
        prob = model(img).item()

    return {
        "fire": prob > 0.5,
        "confidence": prob
    }
