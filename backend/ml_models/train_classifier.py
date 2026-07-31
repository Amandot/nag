"""
ML Classifier Training Script

This script trains a machine learning classifier to categorize complaints
into predefined categories using TF-IDF vectorization and Naive Bayes.

Requirements: 4.1
"""

import pandas as pd
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_classifier(train_data_path='ml_models/training_data_train.csv',
                     test_data_path='ml_models/training_data_test.csv',
                     model_type='naive_bayes',
                     save_model=True):
    """
    Train a machine learning classifier for complaint categorization.
    
    Args:
        train_data_path: Path to training data CSV
        test_data_path: Path to test data CSV
        model_type: Type of classifier ('naive_bayes' or 'logistic_regression')
        save_model: Whether to save the trained model to disk
        
    Returns:
        Tuple of (trained_model, vectorizer, accuracy)
        
    Requirements: 4.1
    """
    logger.info("Loading training data...")
    train_df = pd.read_csv(train_data_path)
    test_df = pd.read_csv(test_data_path)
    
    X_train = train_df['description']
    y_train = train_df['category']
    X_test = test_df['description']
    y_test = test_df['category']
    
    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Test samples: {len(X_test)}")
    
    # Create TF-IDF vectorizer
    logger.info("Creating TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),  # Use unigrams and bigrams
        stop_words='english',
        min_df=2,  # Ignore terms that appear in less than 2 documents
        max_df=0.8  # Ignore terms that appear in more than 80% of documents
    )
    
    # Transform training data
    logger.info("Vectorizing training data...")
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    # Select and train classifier
    if model_type == 'naive_bayes':
        logger.info("Training Naive Bayes classifier...")
        classifier = MultinomialNB(alpha=1.0)
    elif model_type == 'logistic_regression':
        logger.info("Training Logistic Regression classifier...")
        classifier = LogisticRegression(
            max_iter=1000,
            random_state=42,
            multi_class='multinomial'
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Train the model
    classifier.fit(X_train_vectorized, y_train)
    
    # Evaluate on test set
    logger.info("Evaluating model on test set...")
    y_pred = classifier.predict(X_test_vectorized)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"\nModel Accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    logger.info("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Save model and vectorizer if requested
    if save_model:
        model_path = 'ml_models/classifier.pkl'
        vectorizer_path = 'ml_models/vectorizer.pkl'
        
        logger.info(f"Saving model to {model_path}...")
        with open(model_path, 'wb') as f:
            pickle.dump(classifier, f)
        
        logger.info(f"Saving vectorizer to {vectorizer_path}...")
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(vectorizer, f)
        
        logger.info("Model and vectorizer saved successfully!")
    
    return classifier, vectorizer, accuracy


def test_classifier_predictions(classifier, vectorizer):
    """
    Test the classifier with sample predictions.
    
    Args:
        classifier: Trained classifier model
        vectorizer: Fitted TF-IDF vectorizer
    """
    test_complaints = [
        "Water supply disrupted for 3 days",
        "Power outage in neighborhood",
        "Large pothole on highway",
        "Garbage not collected",
        "Hospital emergency closed",
        "Street crime increasing"
    ]
    
    logger.info("\nTesting classifier with sample complaints:")
    for complaint in test_complaints:
        vectorized = vectorizer.transform([complaint])
        prediction = classifier.predict(vectorized)[0]
        probabilities = classifier.predict_proba(vectorized)[0]
        confidence = max(probabilities)
        
        logger.info(f"\nComplaint: {complaint}")
        logger.info(f"Predicted Category: {prediction}")
        logger.info(f"Confidence: {confidence:.4f}")


if __name__ == '__main__':
    # Train the classifier
    classifier, vectorizer, accuracy = train_classifier(
        model_type='naive_bayes',
        save_model=True
    )
    
    # Test with sample predictions
    test_classifier_predictions(classifier, vectorizer)
    
    logger.info("\nTraining complete!")
