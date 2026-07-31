"""
ML Classifier Service for complaint categorization.

This module provides functionality to:
- Load trained ML model and vectorizer
- Predict complaint category with confidence score
- Flag low-confidence predictions for manual review

Requirements: 4.1, 4.2, 4.3
"""

import pickle
import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class MLClassifier:
    """
    Machine Learning classifier for categorizing complaints.
    
    This classifier uses a trained model to predict the category of a complaint
    based on its text description. It also provides confidence scores and flags
    low-confidence predictions for manual review.
    
    Requirements: 4.1, 4.2, 4.3
    """
    
    # Confidence threshold below which predictions are flagged for manual review
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self, model_path='ml_models/classifier.pkl', 
                 vectorizer_path='ml_models/vectorizer.pkl'):
        """
        Initialize the ML Classifier by loading the trained model and vectorizer.
        
        Args:
            model_path: Path to the trained classifier model (pickle file)
            vectorizer_path: Path to the fitted TF-IDF vectorizer (pickle file)
        """
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.classifier = None
        self.vectorizer = None
        self._load_model()
    
    def _load_model(self):
        """
        Load the trained model and vectorizer from disk.
        
        Raises:
            FileNotFoundError: If model or vectorizer files don't exist
            Exception: If loading fails
        """
        try:
            # Check if files exist
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"Model file not found at {self.model_path}. "
                    "Please train the model first using train_classifier.py"
                )
            
            if not os.path.exists(self.vectorizer_path):
                raise FileNotFoundError(
                    f"Vectorizer file not found at {self.vectorizer_path}. "
                    "Please train the model first using train_classifier.py"
                )
            
            # Load the classifier
            logger.info(f"Loading classifier from {self.model_path}...")
            with open(self.model_path, 'rb') as f:
                self.classifier = pickle.load(f)
            
            # Load the vectorizer
            logger.info(f"Loading vectorizer from {self.vectorizer_path}...")
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            logger.info("ML Classifier loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load ML classifier: {e}")
            raise
    
    def classify(self, text: str, keywords: Optional[list] = None) -> Tuple[str, float]:
        """
        Classify a complaint into a category with confidence score.
        
        Args:
            text: Complaint description text (preprocessed)
            keywords: Optional list of extracted keywords (not currently used)
            
        Returns:
            Tuple of (category, confidence_score)
            - category: Predicted category name (e.g., "Water Supply")
            - confidence_score: Confidence of the prediction (0.0 to 1.0)
            
        Requirements: 4.1
        """
        if not text:
            logger.warning("Empty text provided for classification")
            return "Unknown", 0.0
        
        try:
            # Vectorize the input text
            text_vectorized = self.vectorizer.transform([text])
            
            # Predict category
            category = self.classifier.predict(text_vectorized)[0]
            
            # Get confidence score (probability of predicted class)
            probabilities = self.classifier.predict_proba(text_vectorized)[0]
            confidence = max(probabilities)
            
            logger.info(
                f"Classified complaint as '{category}' with confidence {confidence:.4f}"
            )
            
            return category, float(confidence)
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "Unknown", 0.0
    
    def get_confidence(self, text: str) -> float:
        """
        Get the confidence score for a classification without returning the category.
        
        Args:
            text: Complaint description text
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        _, confidence = self.classify(text)
        return confidence
    
    def should_flag_for_review(self, confidence: float) -> bool:
        """
        Determine if a prediction should be flagged for manual review.
        
        Predictions with confidence below the threshold should be reviewed
        by a human to ensure accuracy.
        
        Args:
            confidence: Confidence score from classification
            
        Returns:
            True if prediction should be flagged for manual review, False otherwise
            
        Requirements: 4.2
        """
        return confidence < self.CONFIDENCE_THRESHOLD
    
    def classify_with_review_flag(self, text: str, keywords: Optional[list] = None) -> dict:
        """
        Classify a complaint and determine if it needs manual review.
        
        This is the main method to use for complaint classification in the system.
        It returns all relevant information including the review flag.
        
        Args:
            text: Complaint description text (preprocessed)
            keywords: Optional list of extracted keywords
            
        Returns:
            Dictionary containing:
                - category: Predicted category
                - confidence: Confidence score (0.0 to 1.0)
                - needs_review: Boolean indicating if manual review is needed
                - review_reason: Explanation if review is needed
                
        Requirements: 4.1, 4.2, 4.3
        """
        category, confidence = self.classify(text, keywords)
        needs_review = self.should_flag_for_review(confidence)
        
        result = {
            'category': category,
            'confidence': confidence,
            'needs_review': needs_review,
            'review_reason': None
        }
        
        if needs_review:
            result['review_reason'] = (
                f"Low confidence score ({confidence:.2f}) below threshold "
                f"({self.CONFIDENCE_THRESHOLD}). Manual review recommended."
            )
            logger.warning(
                f"Classification flagged for review: {result['review_reason']}"
            )
        
        return result
    
    def get_all_categories(self) -> list:
        """
        Get list of all possible categories the classifier can predict.
        
        Returns:
            List of category names
        """
        if self.classifier is None:
            return []
        
        return list(self.classifier.classes_)


# Singleton instance
_ml_classifier = None


def get_ml_classifier() -> MLClassifier:
    """
    Get or create the singleton ML Classifier instance.
    
    Returns:
        MLClassifier instance
    """
    global _ml_classifier
    if _ml_classifier is None:
        from flask import current_app
        model_path = current_app.config.get('ML_MODEL_PATH', 'ml_models/classifier.pkl')
        vectorizer_path = current_app.config.get('VECTORIZER_PATH', 'ml_models/vectorizer.pkl')
        _ml_classifier = MLClassifier(model_path=model_path, vectorizer_path=vectorizer_path)
    return _ml_classifier
