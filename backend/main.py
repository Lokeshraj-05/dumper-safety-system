from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from ultralytics import YOLO
import os
from pathlib import Path
import shutil

# Fix for PyTorch 2.6+ checkpoint restrictions
import torch
from ultralytics.nn.tasks import DetectionModel
import torch.nn.modules.container as container
from ultralytics.nn.modules.conv import Conv
from torch.nn.modules.conv import Conv2d
from torch.nn.modules.batchnorm import BatchNorm2d
import torch.nn.modules.activation as activation
from ultralytics.nn.modules.block import C2f
from torch.nn.modules.container import ModuleList
from ultralytics.nn.modules.block import Bottleneck
from ultralytics.nn.modules.block import SPPF
from torch.nn.modules.pooling import MaxPool2d
import torch.nn.modules.upsampling as upsampling
from ultralytics.nn.modules.conv import Concat
from ultralytics.nn.modules.head import Detect
from torch.nn.modules.dropout import Dropout
from torch.nn.modules.module import Module
from ultralytics.nn.modules.block import DFL

if hasattr(torch.serialization, "add_safe_globals"):
    torch.serialization.add_safe_globals([DetectionModel])
    torch.serialization.add_safe_globals([container.Sequential])
    torch.serialization.add_safe_globals([Conv])
    torch.serialization.add_safe_globals([Conv2d])
    torch.serialization.add_safe_globals([BatchNorm2d])
    torch.serialization.add_safe_globals([activation.SiLU])
    torch.serialization.add_safe_globals([C2f])
    torch.serialization.add_safe_globals([ModuleList])
    torch.serialization.add_safe_globals([Bottleneck])
    torch.serialization.add_safe_globals([SPPF])
    torch.serialization.add_safe_globals([MaxPool2d])
    torch.serialization.add_safe_globals([upsampling.Upsample])
    torch.serialization.add_safe_globals([Concat])
    torch.serialization.add_safe_globals([Detect])
    torch.serialization.add_safe_globals([Dropout])
    torch.serialization.add_safe_globals([Module])
    torch.serialization.add_safe_globals([DFL])

# Load model at startup
MODEL_PATH = "models/best.pt"
model = YOLO(MODEL_PATH)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("uploads")
if UPLOAD_DIR.exists():
    if not UPLOAD_DIR.is_dir():
        UPLOAD_DIR.unlink()
        UPLOAD_DIR.mkdir(exist_ok=True)
else:
    UPLOAD_DIR.mkdir(exist_ok=True)

def calculate_hazard_score(bbox, image_shape, class_name=None):
    """Calculate hazard score based on bounding box size and position, with optional class weighting."""
    x1, y1, x2, y2 = bbox
    bbox_width = x2 - x1
    bbox_height = y2 - y1
    bbox_area = bbox_width * bbox_height
    image_height, image_width = image_shape[:2]
    image_area = image_height * image_width
    size_ratio = bbox_area / image_area
    bottom_position = y2 / image_height

    # Class weightings (higher hazard for person, vehicle, etc.)
    class_weights = {
        "person": 1.0,
        "worker": 1.0,
        "car": 0.95,
        "truck": 0.98,
        "bus": 0.96,
        "motorcycle": 0.9,
        "bicycle": 0.8,
        "dog": 0.55,
        "cat": 0.35
        # Add more as needed
    }
    weight = class_weights.get(class_name.lower(), 0.7) if class_name else 0.7
    score = ((size_ratio * 700) + (bottom_position * 30)) * weight
    score = min(score, 100)

    if score >= 80:
        hazard_level = "CRITICAL"
        estimated_distance = "0-2m"
    elif score >= 60:
        hazard_level = "HIGH"
        estimated_distance = "2-5m"
    elif score >= 40:
        hazard_level = "MEDIUM"
        estimated_distance = "5-8m"
    else:
        hazard_level = "LOW"
        estimated_distance = "8m+"
    return {
        "score": round(score, 2),
        "level": hazard_level,
        "estimated_distance": estimated_distance
    }

@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        results = model.predict(image, conf=0.25)
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                bbox = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = model.names[cls]
                hazard = calculate_hazard_score(bbox, image.shape, class_name)
                detections.append({
                    "class": class_name,
                    "confidence": round(conf, 2),
                    "bbox": bbox.tolist(),
                    "hazard_score": hazard["score"],
                    "hazard_level": hazard["level"],
                    "estimated_distance": hazard["estimated_distance"]
                })
        classes_detected = list(set([d["class"] for d in detections]))
        max_hazard = max([d["hazard_score"] for d in detections]) if detections else 0
        return JSONResponse({
            "success": True,
            "detections": detections,
            "summary": {
                "total_objects": len(detections),
                "classes_detected": classes_detected,
                "max_hazard_score": round(max_hazard, 2)
            }
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):
    try:
        video_path = UPLOAD_DIR / file.filename
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        cap = cv2.VideoCapture(str(video_path))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        process_every = max(1, fps // 2)
        frame_results = []
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % process_every == 0:
                results = model.predict(frame, conf=0.30, iou=0.4)
                detections = []
                classes_in_frame = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        bbox = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        class_name = model.names[cls]
                        hazard = calculate_hazard_score(bbox, frame.shape, class_name)
                        detections.append({
                            "class": class_name,
                            "confidence": round(conf, 2),
                            "hazard_score": hazard["score"],
                            "hazard_level": hazard["level"],
                            "estimated_distance": hazard["estimated_distance"]
                        })
                        classes_in_frame.append(class_name)
                max_hazard = max([d["hazard_score"] for d in detections]) if detections else 0
                # Always append (even with no detections)
                frame_results.append({
                    "frame": frame_idx,
                    "timestamp": round(frame_idx / fps, 2),
                    "detections": len(detections),
                    "maxhazard": round(max_hazard, 2),
                    "details": {
                        "classes": list(set(classes_in_frame)),
                        "objects": detections
                    }
                })
            frame_idx += 1
        cap.release()
        video_path.unlink()
        return JSONResponse({
            "success": True,
            "videoinfo": {
                "totalframes": frame_count,
                "fps": fps,
                "processedframes": len(frame_results)
            },
            "frameresults": frame_results   # MATCH your frontend!
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/")
def root():
    return {"message": "Dumper Safety Detection API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
