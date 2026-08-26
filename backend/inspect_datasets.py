import os
import kagglehub
import json

def inspect_dataset(path, name):
    print(f"\n--- Inspecting {name} ---")
    print(f"Path: {path}")
    
    total_images = 0
    extensions = set()
    directories = {}
    
    for root, dirs, files in os.walk(path):
        image_count = 0
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                extensions.add(ext)
                image_count += 1
                total_images += 1
            elif file.endswith('.json') or file.endswith('.csv') or file.endswith('.xml') or file.endswith('.txt'):
                print(f"Found annotation/metadata file: {os.path.join(root, file)}")
                
        if image_count > 0:
            rel_path = os.path.relpath(root, path)
            directories[rel_path] = image_count
            
    print(f"Total images: {total_images}")
    print(f"Extensions found: {extensions}")
    print("Class/Directory breakdown:")
    for d, count in directories.items():
        print(f"  - {d}: {count} images")
        
    return {
        "path": path,
        "total_images": total_images,
        "classes": directories
    }

def main():
    try:
        print("Downloading akinduhiman/urban-issues-dataset...")
        path1 = kagglehub.dataset_download("akinduhiman/urban-issues-dataset")
        inspect_dataset(path1, "Urban Issues Dataset")
    except Exception as e:
        print(f"Failed to download Urban Issues Dataset: {e}")
        
    try:
        print("\nDownloading idanbaru/annotated-potholes-with-severity-levels...")
        path2 = kagglehub.dataset_download("idanbaru/annotated-potholes-with-severity-levels")
        inspect_dataset(path2, "Annotated Potholes with Severity Levels")
    except Exception as e:
        print(f"Failed to download Potholes Dataset: {e}")

if __name__ == "__main__":
    main()
