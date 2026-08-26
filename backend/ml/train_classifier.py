import os
import json
import logging
import argparse
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV3Small
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32

def build_model(num_classes):
    base_model = MobileNetV3Small(weights='imagenet', include_top=False, input_shape=(*IMG_SIZE, 3))
    
    # Freeze the base model for initial training
    for layer in base_model.layers:
        layer.trainable = False
        
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    model.compile(optimizer='adam', 
                  loss='categorical_crossentropy', 
                  metrics=['accuracy'])
    return model

def train(dataset_dir, model_save_path, mapping_save_path):
    if not os.path.exists(dataset_dir):
        logger.error(f"Dataset directory not found: {dataset_dir}")
        return
        
    logger.info(f"Training classifier on dataset: {dataset_dir}")
    
    train_dir = os.path.join(dataset_dir, 'train')
    val_dir = os.path.join(dataset_dir, 'validation')
    
    if not os.path.exists(train_dir):
        logger.warning(f"No explicit train/val split found in {dataset_dir}. Falling back to 80/20 validation split.")
        train_dir = dataset_dir
        val_dir = dataset_dir
        val_split = 0.2
    else:
        val_split = 0.0

    # Data Augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        validation_split=val_split
    )
    
    val_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=val_split
    )

    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training' if val_split > 0 else None
    )
    
    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation' if val_split > 0 else None
    )
    
    num_classes = len(train_generator.class_indices)
    logger.info(f"Found {num_classes} classes: {train_generator.class_indices}")
    
    # Save mapping
    mapping = {}
    for class_name, idx in train_generator.class_indices.items():
        mapping[str(idx)] = {
            "category": "Unknown",  # To be manually updated or mapped based on dataset logic
            "issue": class_name,
            "has_severity": class_name.lower() in ["potholes", "pothole"]
        }
    
    os.makedirs(os.path.dirname(mapping_save_path), exist_ok=True)
    with open(mapping_save_path, 'w') as f:
        json.dump(mapping, f, indent=4)
        
    logger.info(f"Saved class mapping to {mapping_save_path}")

    model = build_model(num_classes)
    
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
        ModelCheckpoint(model_save_path, monitor='val_loss', save_best_only=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)
    ]
    
    logger.info("Starting training...")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=1,
        steps_per_epoch=10,
        validation_steps=2,
        callbacks=callbacks
    )
    
    logger.info(f"Model saved to {model_save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, required=True, help="Path to raw dataset directory")
    parser.add_argument('--model_out', type=str, default='../ml_models/image_classifier.keras')
    parser.add_argument('--mapping_out', type=str, default='../ml_models/class_mapping.json')
    args = parser.parse_args()
    
    train(args.dataset, args.model_out, args.mapping_out)
