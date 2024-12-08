import os
import sys
from pathlib import Path

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'src'))

from image_evaluator import ImageEvaluator

def validate_path(path_str):
    """Validate if the path exists and is an image file or directory."""
    path = Path(path_str)
    if not path.exists():
        return None
    
    if path.is_file():
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if path.suffix.lower() not in valid_extensions:
            return None
    return path

def main():
    while True:
        input_path = input("\nEnter the path to an image or directory: ").strip()
        path = validate_path(input_path)
        
        if path is None:
            print("Invalid path. Please enter a valid path to an image file or directory.")
            continue
        
        recursive = input("Process directories recursively? (y/n): ").lower().startswith('y')

        # Initialize the evaluator
        evaluator = ImageEvaluator()

        # Process single file or directory
        if path.is_file():
            print(f"\nProcessing single file: {path}")
            evaluator.process_single_image(path)
        else:
            print(f"\nProcessing directory: {path}")
            evaluator.process_directory(path, recursive=recursive)
        break

if __name__ == "__main__":
    main() 