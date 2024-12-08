import os
from openai import OpenAI
from PIL import Image
import base64

# Create necessary directories
os.makedirs('input_images', exist_ok=True)
os.makedirs('output_folders', exist_ok=True)
os.makedirs('logs', exist_ok=True)

INPUT_FOLDER = 'input_images'
OUTPUT_PARENT_FOLDER = 'output_folders'
# Configuration
OPENAI_API_KEY = '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'

OUTPUT_PARENT_FOLDER = 'output_folders'
LOG_FILE_PATH = os.path.join('logs', 'evaluation_log.txt')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def evaluate_image(image_path):
    """
    Sends the image to OpenAI API for evaluation.
    Returns a tuple of (score, reason, token_usage).
    """
    image_b64 = get_image_base64(image_path)
    
    # Prepare the prompt
    prompt = (
        "Analyze the following image and provide:\n"
        "1. Brief Description: Describe what's in the image\n"
        "2. Individual Scores (1-10 for each):\n"
        "   - Composition\n"
        "   - Color\n"
        "   - Lighting\n"
        "   - Subject\n"
        "   - Originality\n"
        "   - Technical Skill\n"
        "   - Emotion\n"
        "   - Storytelling\n"
        "   - Clarity\n"
        "   - Creativity\n"
        "3. Overall Score: Average of above scores (1-100)\n"
        "4. Final Reason: Brief explanation of the overall rating\n\n"
        "Format your response exactly as:\n"
        "Description: [brief description]\n"
        "Composition: [1-10]\n"
        "Color: [1-10]\n"
        "Lighting: [1-10]\n"
        "Subject: [1-10]\n"
        "Originality: [1-10]\n"
        "Technical Skill: [1-10]\n"
        "Emotion: [1-10]\n"
        "Storytelling: [1-10]\n"
        "Clarity: [1-10]\n"
        "Creativity: [1-10]\n"
        "Score: [1-100]\n"
        "Reason: [final explanation]"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Get token usage
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        # Extract the response text
        evaluation = response.choices[0].message.content.strip()
        
        # Remove markdown formatting (** bold markers)
        evaluation = evaluation.replace('**', '')
        
        # Parse the evaluation
        lines = evaluation.split('\n')
        # Skip empty lines and remove any remaining markdown
        lines = [line.strip() for line in lines if line.strip()]
        
        description_line = next((line for line in lines if line.lower().startswith('description:')), None)
        score_line = next((line for line in lines if line.lower().startswith('score:')), None)
        reason_line = next((line for line in lines if line.lower().startswith('reason:')), None)
        
        # Get individual characteristic scores
        characteristics = {}
        for char in ['composition', 'color', 'lighting', 'subject', 'originality', 
                    'technical skill', 'emotion', 'storytelling', 'clarity', 'creativity']:
            char_line = next((line for line in lines if line.lower().startswith(f'{char}:')), None)
            if char_line:
                try:
                    # Remove any non-numeric characters except digits
                    char_score = int(''.join(filter(str.isdigit, char_line.split(':')[1])))
                    characteristics[char] = char_score
                except (ValueError, IndexError):
                    characteristics[char] = 0
        
        if score_line and reason_line and description_line:
            try:
                # Extract just the number from the score line
                score_text = score_line.lower().replace('score:', '').strip()
                score = int(''.join(filter(str.isdigit, score_text)))
                
                # Validate score is in range 1-100
                if score < 1 or score > 100:
                    return None, f"Invalid score value: {score}", token_usage
                
                description = description_line.split(':', 1)[1].strip()
                reason = reason_line.split(':', 1)[1].strip()
                
                # Create detailed reason with all scores
                detailed_reason = f"Description: {description}\n"
                for char, char_score in characteristics.items():
                    detailed_reason += f"{char.title()}: {char_score}/10\n"
                detailed_reason += f"\nFinal Analysis: {reason}"
                
                return score, detailed_reason, token_usage
            except ValueError:
                return None, f"Could not parse score from: {score_line}", token_usage
        else:
            return None, f"Invalid response format: {evaluation}", token_usage
        
    except Exception as e:
        return None, f"Error during evaluation: {str(e)}", None

def determine_folder(score):
    """
    Determines the folder name based on the score, using 3-point intervals.
    """
    # Calculate the lower bound of the interval (rounds down to nearest multiple of 3)
    lower_bound = ((score - 1) // 3) * 3 + 1
    upper_bound = lower_bound + 2
    
    # Handle edge case for score of 100
    if upper_bound > 100:
        upper_bound = 100
        
    return f"{lower_bound}-{upper_bound}"

def log_evaluation(image_name, score, reason):
    """
    Appends the evaluation to the log file.
    """
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write(f"Image: {image_name}\n")
        log_file.write(f"Score: {score}\n")
        log_file.write(f"Reason: {reason}\n")
        log_file.write("-" * 40 + "\n")

def process_images():
    """
    Main function to process all images in real-time.
    """
    # Create necessary directories
    os.makedirs('input_images', exist_ok=True)
    os.makedirs('output_folders', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w') as log_file:
            log_file.write("Image Evaluation Log\n")
            log_file.write("=" * 40 + "\n\n")
    
    total_tokens = {
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0
    }
    
    total_images = len([f for f in os.listdir(INPUT_FOLDER) if os.path.isfile(os.path.join(INPUT_FOLDER, f))])
    processed_images = 0
    
    print(f"\nStarting to process {total_images} images...")
    print("=" * 50)
    
    # Process each image immediately
    for image_name in os.listdir(INPUT_FOLDER):
        image_path = os.path.join(INPUT_FOLDER, image_name)
        
        if os.path.isfile(image_path):
            processed_images += 1
            print(f"\nProcessing image {processed_images}/{total_images}: {image_name}")
            
            # Evaluate the image
            score, reason, token_usage = evaluate_image(image_path)
            
            if token_usage:
                # Update and display token usage
                for key in total_tokens:
                    total_tokens[key] += token_usage[key]
                print(f"Token usage for {image_name}:")
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
                destination_folder = os.path.join(OUTPUT_PARENT_FOLDER, folder_name)
                os.makedirs(destination_folder, exist_ok=True)
                
                # Move the file
                destination_path = os.path.join(destination_folder, image_name)
                os.rename(image_path, destination_path)
                
                # Log the evaluation
                log_evaluation(image_name, score, reason)
                print(f"Moved {image_name} to {folder_name}")
            else:
                # Log the error
                log_evaluation(image_name, "N/A", reason)
                print(f"Failed to evaluate {image_name}: {reason}")
    
    # Display final token usage summary
    print("\nFinal token usage summary:")
    print("=" * 50)
    print(f"Total images processed: {processed_images}")
    print(f"Total prompt tokens: {total_tokens['prompt_tokens']}")
    print(f"Total completion tokens: {total_tokens['completion_tokens']}")
    print(f"Total tokens used: {total_tokens['total_tokens']}")
    print(f"Average tokens per image: {total_tokens['total_tokens'] / processed_images:.2f}")

if __name__ == "__main__":
    process_images()
