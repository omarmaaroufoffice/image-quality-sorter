"""
Handles all file operations including moving files and logging.
"""
import os
import shutil
from datetime import datetime

def determine_folder(score):
    """
    Determines the appropriate folder name based on the score.
    """
    # Calculate the lower bound of the interval (rounds down to nearest multiple of 3)
    lower_bound = ((score - 1) // 3) * 3 + 1
    upper_bound = lower_bound + 2
    
    # Handle edge case for score of 100
    if upper_bound > 100:
        upper_bound = 100
        
    return f"{lower_bound}-{upper_bound}"

def move_image(source_path, score, config):
    """
    Moves an image to its appropriate output folder.
    """
    folder_name = determine_folder(score)
    destination_folder = os.path.join(config['directories']['output'], folder_name)
    os.makedirs(destination_folder, exist_ok=True)
    
    filename = os.path.basename(source_path)
    destination_path = os.path.join(destination_folder, filename)
    shutil.move(source_path, destination_path)
    
    return destination_path

def log_evaluation(image_name, score, evaluation_data, config):
    """
    Appends the evaluation to the log file.
    """
    log_file_path = os.path.join(
        config['directories']['logs'],
        config['logging']['file']
    )
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Image: {image_name}\n")
        log_file.write(f"Score: {score}\n")
        
        # Write the detailed evaluation
        if isinstance(evaluation_data, dict):
            # Write description
            if 'description' in evaluation_data:
                log_file.write(f"Description: {evaluation_data['description']}\n")
            
            # Write individual scores
            characteristics = [
                'Composition', 'Color', 'Lighting', 'Subject', 'Originality',
                'Technical Skill', 'Emotion', 'Storytelling', 'Clarity', 'Creativity'
            ]
            for char in characteristics:
                if char.lower() in evaluation_data:
                    log_file.write(f"{char}: {evaluation_data[char.lower()]}/10\n")
            
            # Write final analysis
            if 'final_analysis' in evaluation_data:
                log_file.write(f"\nFinal Analysis: {evaluation_data['final_analysis']}\n")
        else:
            # If evaluation_data is just a string (e.g., error message)
            log_file.write(f"Reason: {evaluation_data}\n")
        
        log_file.write("-" * 40 + "\n")