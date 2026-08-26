import os
import shutil
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_severity_dataset():
    base_dir = r"C:\Users\AMAN\.cache\kagglehub\datasets\idanbaru\annotated-potholes-with-severity-levels\versions\1"
    annotations_dir = os.path.join(base_dir, "annotations")
    images_dir = os.path.join(base_dir, "images")
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "processed", "severity"))
    
    if not os.path.exists(annotations_dir) or not os.path.exists(images_dir):
        logger.error("Dataset not found at expected location.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each XML file
    count = 0
    for xml_file in os.listdir(annotations_dir):
        if not xml_file.endswith(".xml"):
            continue
            
        xml_path = os.path.join(annotations_dir, xml_file)
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find the filename
            filename_elem = root.find("filename")
            if filename_elem is None:
                continue
            filename = filename_elem.text
            
            # Find the severity class (from first object)
            obj_elem = root.find("object")
            if obj_elem is None:
                continue
            
            name_elem = obj_elem.find("name")
            if name_elem is None:
                continue
            severity_class = name_elem.text.strip().replace(" ", "_")
            
            # Define source and destination
            src_image = os.path.join(images_dir, filename)
            
            # If the filename listed in XML doesn't exist, we might have a mismatch. Let's fallback to replacing xml extension
            if not os.path.exists(src_image):
                fallback_filename = xml_file.replace(".xml", ".jpg")
                src_image_fallback = os.path.join(images_dir, fallback_filename)
                if os.path.exists(src_image_fallback):
                    src_image = src_image_fallback
                else:
                    logger.warning(f"Image not found for {xml_file} (tried {filename} and {fallback_filename})")
                    continue
            
            dest_dir = os.path.join(output_dir, severity_class)
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_image = os.path.join(dest_dir, os.path.basename(src_image))
            
            # Copy image
            shutil.copy2(src_image, dest_image)
            count += 1
            
        except Exception as e:
            logger.error(f"Error processing {xml_file}: {e}")
            
    logger.info(f"Successfully processed {count} images and organized into severity classes at {output_dir}")

if __name__ == "__main__":
    prepare_severity_dataset()
