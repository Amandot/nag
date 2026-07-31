"""
Test script for ML Classifier service.
"""

from services.ml_classifier import get_ml_classifier
import logging

logging.basicConfig(level=logging.INFO)

def test_ml_classifier():
    """Test the ML classifier with various complaints."""
    
    print("=" * 60)
    print("Testing ML Classifier Service")
    print("=" * 60)
    
    # Get the classifier instance
    classifier = get_ml_classifier()
    
    # Test complaints
    test_cases = [
        "Water supply has been disrupted for 3 days. No water in taps.",
        "Power outage in entire neighborhood. Electricity not working.",
        "Large pothole on highway causing accidents.",
        "Garbage not collected for 2 weeks. Piles of trash.",
        "Hospital emergency room closed. No doctors available.",
        "Street crime increasing. Need police patrol.",
        "Broken water pipe leaking on street.",
        "Electric shock from exposed wires.",
        "Road collapsed after rain.",
        "Sewage overflow in residential area.",
        "Ambulance not responding to calls.",
        "Fire in building need help.",
        "This is a very vague complaint about something."  # Low confidence test
    ]
    
    print("\nTesting classification with review flags:\n")
    
    for i, complaint in enumerate(test_cases, 1):
        print(f"\n{i}. Complaint: {complaint}")
        print("-" * 60)
        
        result = classifier.classify_with_review_flag(complaint)
        
        print(f"   Category: {result['category']}")
        print(f"   Confidence: {result['confidence']:.4f}")
        print(f"   Needs Review: {result['needs_review']}")
        if result['review_reason']:
            print(f"   Review Reason: {result['review_reason']}")
    
    # Test getting all categories
    print("\n" + "=" * 60)
    print("Available Categories:")
    print("=" * 60)
    categories = classifier.get_all_categories()
    for cat in categories:
        print(f"  - {cat}")
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_ml_classifier()
