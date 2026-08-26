import os
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

# Attempt to import tensorflow/keras gracefully
try:
    import tensorflow as tf
    import numpy as np
    from PIL import Image
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed. Image Analysis will be disabled.")

class ImageAnalysisService:
    def __init__(self):
        self.is_ready = False
        self.image_classifier = None
        self.severity_model = None
        self.class_mapping = {}
        self.severity_mapping = {}
        
        self.confidence_threshold = Config.IMAGE_CONFIDENCE_THRESHOLD
        
        self._load_models()
        
    def _load_models(self):
        if not TF_AVAILABLE:
            return
            
        try:
            # Load mappings
            if os.path.exists(Config.CLASS_MAPPING_PATH):
                with open(Config.CLASS_MAPPING_PATH, 'r') as f:
                    self.class_mapping = json.load(f)
            
            if os.path.exists(Config.SEVERITY_MAPPING_PATH):
                with open(Config.SEVERITY_MAPPING_PATH, 'r') as f:
                    self.severity_mapping = json.load(f)
                    
            # Load models gracefully (only if they exist)
            if os.path.exists(Config.IMAGE_CLASSIFIER_MODEL_PATH):
                self.image_classifier = tf.keras.models.load_model(Config.IMAGE_CLASSIFIER_MODEL_PATH)
                logger.info("Loaded CNN image classifier model.")
                
            if os.path.exists(Config.IMAGE_SEVERITY_MODEL_PATH):
                self.severity_model = tf.keras.models.load_model(Config.IMAGE_SEVERITY_MODEL_PATH)
                logger.info("Loaded CNN severity model.")
                
            # We are ready if we have the classifier at least
            if self.image_classifier is not None:
                self.is_ready = True
                
        except Exception as e:
            logger.error(f"Failed to load image analysis models: {e}")
            self.is_ready = False

    def _preprocess_image(self, image_path):
        """Preprocesses the image for the CNN (assumes 224x224x3)."""
        try:
            img = Image.open(image_path).convert('RGB')
            img = img.resize((224, 224))
            img_array = np.array(img)
            # Depending on model, it might need normalization. 
            # We assume the model expects pixel values between 0 and 255 if it's MobileNetV3/EfficientNet 
            # (they often have preprocessing layers built-in in keras).
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            return None

    def analyze_image(self, image_path):
        """
        Analyzes the image and returns category, severity, etc.
        """
        if not self.is_ready or not os.path.exists(image_path):
            return {
                "image_analysis": None,
                "image_analysis_error": "Model not ready or image missing" if not os.path.exists(image_path) else "Model not ready"
            }
            
        try:
            img_tensor = self._preprocess_image(image_path)
            if img_tensor is None:
                return {
                    "image_analysis": None,
                    "image_analysis_error": "Failed to read or preprocess image"
                }
                
            # Classify issue
            class_preds = self.image_classifier.predict(img_tensor, verbose=0)[0]
            class_idx = np.argmax(class_preds)
            confidence = float(class_preds[class_idx])
            
            if confidence < self.confidence_threshold:
                return {
                    "image_analysis": {
                        "category": "Unknown",
                        "issue": "Unknown",
                        "severity": "Unknown",
                        "severity_score": 0,
                        "confidence": confidence
                    }
                }
                
            # Map index to class name using class_mapping
            str_idx = str(class_idx)
            if str_idx not in self.class_mapping:
                issue_info = {"category": "Unknown", "issue": f"Class_{class_idx}", "has_severity": False}
            else:
                issue_info = self.class_mapping[str_idx]
                
            category = issue_info.get("category", "Unknown")
            issue_name = issue_info.get("issue", "Unknown")
            has_severity = issue_info.get("has_severity", False)
            
            # Predict severity if applicable
            severity_class = "Unknown"
            severity_score = 0
            
            if has_severity and self.severity_model is not None:
                sev_preds = self.severity_model.predict(img_tensor, verbose=0)[0]
                sev_idx = np.argmax(sev_preds)
                str_sev_idx = str(sev_idx)
                
                if str_sev_idx in self.severity_mapping:
                    sev_info = self.severity_mapping[str_sev_idx]
                    severity_class = sev_info.get("severity", "Unknown")
                    severity_score = sev_info.get("score", 0)
            
            return {
                "image_analysis": {
                    "category": category,
                    "issue": issue_name,
                    "severity": severity_class,
                    "severity_score": severity_score,
                    "confidence": confidence
                },
                "image_analysis_error": None
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                "image_analysis": None,
                "image_analysis_error": f"Prediction failed: {str(e)}"
            }

# Singleton instance
image_analysis_service = ImageAnalysisService()

def analyze_image(image_path):
    return image_analysis_service.analyze_image(image_path)
