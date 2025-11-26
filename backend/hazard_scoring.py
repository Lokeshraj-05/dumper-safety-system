"""
Hazard scoring module for dumper truck safety system
Calculates risk scores based on object detection results
"""

def calculate_hazard_score(bbox, image_shape, class_name):
    """
    Calculate hazard score based on bounding box size, position, and object class.
    
    Args:
        bbox: [x1, y1, x2, y2] bounding box coordinates
        image_shape: (height, width, channels) of image
        class_name: detected object class name
    
    Returns:
        dict with score, level, estimated_distance, and priority
    """
    x1, y1, x2, y2 = bbox
    bbox_width = x2 - x1
    bbox_height = y2 - y1
    bbox_area = bbox_width * bbox_height
    
    image_height, image_width = image_shape[:2]
    image_area = image_height * image_width
    
    # Calculate size ratio (larger box = closer object)
    size_ratio = bbox_area / image_area
    
    # Bottom position ratio (closer to bottom = closer to vehicle)
    bottom_position = y2 / image_height
    
    # Base score calculation (0-100 scale)
    # Size contributes 70%, position contributes 30%
    base_score = (size_ratio * 700) + (bottom_position * 30)
    base_score = min(base_score, 100)
    
    # Class-based priority multiplier
    class_multipliers = {
        'person': 1.2,      # Highest priority
        'human': 1.2,
        'worker': 1.2,
        'pedestrian': 1.2,
        'child': 1.3,
        'animal': 1.1,      # High priority
        'dog': 1.1,
        'cat': 1.1,
        'vehicle': 0.9,     # Medium priority
        'car': 0.9,
        'truck': 0.9,
        'bicycle': 1.0,
        'motorcycle': 1.0,
    }
    
    # Apply class multiplier
    multiplier = class_multipliers.get(class_name.lower(), 1.0)
    final_score = min(base_score * multiplier, 100)
    
    # Determine hazard level and estimated distance
    if final_score >= 80:
        hazard_level = "CRITICAL"
        estimated_distance = "0-2m"
        color_code = "#FF0000"  # Red
        action = "STOP IMMEDIATELY"
    elif final_score >= 60:
        hazard_level = "HIGH"
        estimated_distance = "2-5m"
        color_code = "#FF6B00"  # Orange
        action = "PROCEED WITH CAUTION"
    elif final_score >= 40:
        hazard_level = "MEDIUM"
        estimated_distance = "5-8m"
        color_code = "#FFD700"  # Yellow
        action = "MONITOR CLOSELY"
    else:
        hazard_level = "LOW"
        estimated_distance = "8m+"
        color_code = "#00FF00"  # Green
        action = "SAFE TO PROCEED"
    
    return {
        "score": round(final_score, 2),
        "level": hazard_level,
        "estimated_distance": estimated_distance,
        "color_code": color_code,
        "recommended_action": action,
        "priority": multiplier
    }


def calculate_zone_risk(detections, image_shape):
    """
    Calculate overall zone risk based on all detections.
    Follows ISO 5006 inspired zones: 1m boundary (critical), 1-5m (high), 5-12m (medium)
    
    Args:
        detections: list of detection dicts with hazard scores
        image_shape: image dimensions
    
    Returns:
        dict with overall risk assessment
    """
    if not detections:
        return {
            "overall_risk": "SAFE",
            "max_hazard_score": 0,
            "critical_objects": 0,
            "high_priority_objects": 0,
            "recommendation": "No objects detected. Safe to proceed."
        }
    
    # Count objects by hazard level
    critical_count = sum(1 for d in detections if d["hazard_score"] >= 80)
    high_count = sum(1 for d in detections if 60 <= d["hazard_score"] < 80)
    medium_count = sum(1 for d in detections if 40 <= d["hazard_score"] < 60)
    
    # Get maximum hazard score
    max_hazard = max(d["hazard_score"] for d in detections)
    
    # Determine overall risk
    if critical_count > 0:
        overall_risk = "CRITICAL"
        recommendation = f"STOP! {critical_count} object(s) in critical zone (0-2m)"
    elif high_count > 0:
        overall_risk = "HIGH"
        recommendation = f"CAUTION: {high_count} object(s) in high-risk zone (2-5m)"
    elif medium_count > 0:
        overall_risk = "MEDIUM"
        recommendation = f"MONITOR: {medium_count} object(s) detected (5-8m)"
    else:
        overall_risk = "LOW"
        recommendation = "Objects detected at safe distance (8m+)"
    
    return {
        "overall_risk": overall_risk,
        "max_hazard_score": round(max_hazard, 2),
        "critical_objects": critical_count,
        "high_risk_objects": high_count,
        "medium_risk_objects": medium_count,
        "total_objects": len(detections),
        "recommendation": recommendation
    }


def generate_alert_message(zone_risk):
    """
    Generate human-readable alert message for driver display
    """
    risk_level = zone_risk["overall_risk"]
    
    alerts = {
        "CRITICAL": "⚠️ CRITICAL ALERT: Object detected in immediate vicinity! STOP DUMPING!",
        "HIGH": "⚠️ HIGH RISK: Object approaching danger zone. Proceed with extreme caution.",
        "MEDIUM": "⚡ CAUTION: Object detected nearby. Monitor before dumping.",
        "LOW": "✓ LOW RISK: Area monitored. Safe to proceed.",
        "SAFE": "✓ SAFE: No objects detected in monitoring zones."
    }
    
    return alerts.get(risk_level, "Status unknown")
