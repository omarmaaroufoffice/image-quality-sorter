"""
Core module for evaluating image quality using OpenAI's Vision API.
"""
import os
from pathlib import Path
import yaml
from openai import OpenAI
from utils import get_image_base64, setup_logging
from file_handler import determine_folder, move_image, log_evaluation

class ImageEvaluator:
    def __init__(self, config_path='config/config.yaml'):
        """Initialize the ImageEvaluator with configuration and logging."""
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Setup OpenAI client
            self.client = OpenAI(api_key=self.config['openai']['api_key'])
            
            # Setup logging
            self.logger = setup_logging()
            
            # Ensure required directories exist
            for dir_name in self.config['directories'].values():
                os.makedirs(dir_name, exist_ok=True)
            
        except Exception as e:
            print(f"Error initializing ImageEvaluator: {str(e)}")
            raise

    def evaluate_image(self, image_path):
        """
        Evaluates an image using OpenAI's Vision API.
        Returns tuple of (score, evaluation_data, token_usage).
        """
        try:
            # Convert image to base64
            base64_image = get_image_base64(image_path)
            
            # Call the Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": self.config['prompts']['evaluation_prompt']
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.config['openai']['max_tokens']
            )
            
            # Get token usage
            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            # Extract and parse the response
            response_text = response.choices[0].message.content.strip()
            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            
            # Parse all components
            evaluation_data = {}
            
            # Get description
            description_line = next((line for line in lines if line.lower().startswith('description:')), None)
            if description_line:
                evaluation_data['description'] = description_line.split(':', 1)[1].strip()
            
            # Get individual scores
            characteristics = [
                'composition', 'color', 'lighting', 'subject', 'originality',
                'technical skill', 'emotion', 'storytelling', 'clarity', 'creativity'
            ]
            
            scores = []
            for char in characteristics:
                char_line = next((line for line in lines if line.lower().startswith(f'{char}:')), None)
                if char_line:
                    try:
                        score = int(''.join(filter(str.isdigit, char_line.split(':', 1)[1])))
                        evaluation_data[char] = score
                        scores.append(score)
                    except ValueError:
                        evaluation_data[char] = 0
            
            # Get final analysis
            reason_line = next((line for line in lines if line.lower().startswith('reason:')), None)
            if reason_line:
                evaluation_data['final_analysis'] = reason_line.split(':', 1)[1].strip()
            
            if scores:
                # Calculate final score (1-100)
                final_score = (sum(scores) * 10) // len(scores)
                final_score = max(1, min(100, final_score))
                return final_score, evaluation_data, token_usage
            
            raise ValueError("Could not parse scores from response")
            
        except Exception as e:
            self.logger.error(f"Error evaluating image {image_path}: {str(e)}")
            return None, str(e), None

    def process_directory(self, directory_path, recursive=False):
        """
        Process all images in a directory.
        """
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        created_folders = set()
        
        total_tokens = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }
        
        def is_valid_image(path):
            return path.is_file() and path.suffix.lower() in valid_extensions

        # Count total images
        total_images = 0
        if recursive:
            for root, _, files in os.walk(directory_path):
                total_images += sum(1 for f in files if is_valid_image(Path(root) / f))
        else:
            total_images = sum(1 for item in Path(directory_path).iterdir() if is_valid_image(item))

        processed_images = 0
        print(f"\nStarting to process {total_images} images...")
        print("=" * 50)

        def process_image(file_path):
            nonlocal processed_images, total_tokens
            processed_images += 1
            print(f"\nProcessing image {processed_images}/{total_images}: {file_path.name}")
            
            score, reason, token_usage = self.evaluate_image(file_path)
            
            if token_usage:
                # Update and display token usage
                for key in total_tokens:
                    total_tokens[key] += token_usage[key]
                print(f"Token usage for {file_path.name}:")
                print(f"  Prompt tokens: {token_usage['prompt_tokens']}")
                print(f"  Completion tokens: {token_usage['completion_tokens']}")
                print(f"  Total tokens: {token_usage['total_tokens']}")
                print(f"\nRunning totals after {processed_images} images:")
                print(f"  Total prompt tokens: {total_tokens['prompt_tokens']}")
                print(f"  Total completion tokens: {total_tokens['completion_tokens']}")
                print(f"  Accumulated total tokens: {total_tokens['total_tokens']}")
                print("-" * 50)
            
            if score:
                # Create folder and move file immediately
                folder_name = determine_folder(score)
                created_folders.add(folder_name)
                destination_folder = os.path.join(self.config['directories']['output'], folder_name)
                os.makedirs(destination_folder, exist_ok=True)
                
                # Move the file
                destination_path = os.path.join(destination_folder, file_path.name)
                os.rename(file_path, destination_path)
                
                # Log the evaluation
                log_evaluation(file_path.name, score, reason, self.config)
                print(f"Evaluated {file_path.name} with score {score}")
                print(f"Moved {file_path.name} to {folder_name}")
            else:
                log_evaluation(file_path.name, "N/A", reason, self.config)
                print(f"Failed to evaluate {file_path.name}: {reason}")

        # Process images
        if recursive:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = Path(root) / file
                    if is_valid_image(file_path):
                        process_image(file_path)
        else:
            for item in Path(directory_path).iterdir():
                if is_valid_image(item):
                    process_image(item)

        # Display final summary
        print("\nFinal token usage summary:")
        print("=" * 50)
        print(f"Total images processed: {processed_images}")
        print(f"Total prompt tokens: {total_tokens['prompt_tokens']}")
        print(f"Total completion tokens: {total_tokens['completion_tokens']}")
        print(f"Total tokens used: {total_tokens['total_tokens']}")
        if processed_images > 0:
            print(f"Average tokens per image: {total_tokens['total_tokens'] / processed_images:.2f}")
        print("\nCreated folders:", sorted(created_folders)) 