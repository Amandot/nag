"""
Script to prepare and split training data for ML classifier.

This script:
1. Loads the training data CSV
2. Splits it into training and test sets
3. Saves the splits for model training

Requirements: 4.1
"""

import pandas as pd
from sklearn.model_selection import train_test_split
import os

def prepare_training_data(data_path='ml_models/training_data.csv', 
                         test_size=0.2, 
                         random_state=42):
    """
    Load and split training data into train and test sets.
    
    Args:
        data_path: Path to the training data CSV file
        test_size: Proportion of data to use for testing (default 0.2)
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    # Load the data
    print(f"Loading training data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Remove any rows with missing values
    df = df.dropna()
    
    print(f"Loaded {len(df)} complaints")
    print(f"\nCategory distribution:")
    print(df['category'].value_counts())
    
    # Split features and labels
    X = df['description']
    y = df['category']
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y  # Maintain category distribution in both sets
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Save the splits
    train_df = pd.DataFrame({'description': X_train, 'category': y_train})
    test_df = pd.DataFrame({'description': X_test, 'category': y_test})
    
    train_path = data_path.replace('.csv', '_train.csv')
    test_path = data_path.replace('.csv', '_test.csv')
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"\nSaved training set to {train_path}")
    print(f"Saved test set to {test_path}")
    
    return X_train, X_test, y_train, y_test


if __name__ == '__main__':
    # Prepare the data
    X_train, X_test, y_train, y_test = prepare_training_data()
    print("\nData preparation complete!")
