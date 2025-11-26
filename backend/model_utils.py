"""
Model utility functions for YOLOv8 inference
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

class YOLODetector:
    """Wrapper class for YOLOv8 detection model"""
    
    def __init__(self, model_path="models/best.pt", conf_threshold=0.25):
        """
        Initialize YOLO detector
        
        Args:
            model_path: path to trained YOLOv8 model (.pt file)
            conf_threshold: confidence threshold for detections
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        self.model = YOLO(str(self.model_path))
        self.conf_threshold = conf_threshold
        print(f"✓ Model loaded from {model_path}")
        print(f"✓ Model classes: {self.model.names}")
    
    def detect_image(self, image):
        """
        Run detection on single image
        
        Args:
            image: numpy array (BGR format from cv2)
        
        Returns:
            list of detection dicts
        """
        results = self.model.predict(
            image, 
            conf=self.conf_threshold,
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                bbox = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = self.model.names[cls]
                
                detections.append({
                    "bbox": bbox.tolist(),
                    "confidence": round(conf, 3),
                    "class_id": cls,
                    "class_name": class_name
                })
        
        return detections
    
    def detect_video_frames(self, video_path, process_every_n_frames=15):
        """
        Run detection on video frames
        
        Args:
            video_path: path to video file
            process_every_n_frames: process every Nth frame to speed up
        
        Returns:
            list of frame results
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        frame_results = []
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every Nth frame
            if frame_idx % process_every_n_frames == 0:
                detections = self.detect_image(frame)
                
                if detections:
                    frame_results.append({
                        "frame_number": frame_idx,
                        "timestamp": round(frame_idx / fps, 2),
                        "detections": detections
                    })
            
            frame_idx += 1
        
        cap.release()
        
        return {
            "total_frames": frame_count,
            "fps": fps,
            "processed_frames": len(frame_results),
            "frame_results": frame_results
        }
    
    def draw_detections(self, image, detections, hazard_scores=None):
        """
        Draw bounding boxes and labels on image
        
        Args:
            image: numpy array
            detections: list of detection dicts
            hazard_scores: optional list of hazard score dicts
        
        Returns:
            annotated image
        """
        annotated = image.copy()
        
        for idx, det in enumerate(detections):
            x1, y1, x2, y2 = map(int, det["bbox"])
            class_name = det["class_name"]
            conf = det["confidence"]
            
            # Determine color based on hazard score
            if hazard_scores and idx < len(hazard_scores):
                hazard = hazard_scores[idx]
                if hazard["level"] == "CRITICAL":
                    color = (0, 0, 255)  # Red
                elif hazard["level"] == "HIGH":
                    color = (0, 165, 255)  # Orange
                elif hazard["level"] == "MEDIUM":
                    color = (0, 255, 255)  # Yellow
                else:
                    color = (0, 255, 0)  # Green
                
                label = f"{class_name} {conf:.2f} | Hazard: {hazard['score']}"
            else:
                color = (0, 255, 0)
                label = f"{class_name} {conf:.2f}"
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - 20), (x1 + w, y1), color, -1)
            
            # Draw label text
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated
