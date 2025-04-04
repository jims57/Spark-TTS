import replicate
import os
import re
import glob
import sys

def generate_sentences(total_sentences=10):
    # Prepare prompt with dynamic number of sentences
    prompt = f"""generate {total_sentences} random English sentences(less than 25 words) line by line, make the sentences use as many as possible words but common used in daily life, make sentences covers diff topics and fields, especially daily spoken languages, for we use these for asr model training as dataset, format like this(not blank line before them, just line by line). Sentences should not include any commas or other punctuation marks in the middle of the sentence:
    1. xxxx.
    2. yyyy.
    """
    
    input = {
        "prompt": prompt,
        "max_tokens": 35000
    }
    
    # Buffer to store the response
    response_buffer = ""
    
    # Stream the response
    for event in replicate.stream(
        "anthropic/claude-3.7-sonnet",
        input=input
    ):
        # Ensure event is a string before concatenating
        if isinstance(event, str):
            print(event, end="")
            response_buffer += event
        else:
            # Handle non-string events appropriately
            print(str(event), end="")
            response_buffer += str(event)
    
    # Once done, save to a file
    save_to_file(response_buffer)
    
def save_to_file(text):
    # Get the directory path
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_sentences")
    
    # Find the highest numbered text file
    existing_files = glob.glob(os.path.join(dir_path, "*.txt"))
    max_number = 0
    
    for file in existing_files:
        base_name = os.path.basename(file)
        # Extract number from filename (like "2.txt" -> 2)
        if base_name.endswith(".txt") and base_name[:-4].isdigit():
            max_number = max(max_number, int(base_name[:-4]))
    
    # Create new filename with incremented number
    new_file_name = f"{max_number + 1}.txt"
    new_file_path = os.path.join(dir_path, new_file_name)
    
    # Extract sentences with numbered format (1. xxx, 2. xxx, etc.)
    sentences = re.findall(r'\d+\.\s+[^\n]+', text)
    
    # Write to file
    with open(new_file_path, 'w', encoding='utf-8') as f:
        for sentence in sentences:
            f.write(sentence + '\n')
    
    print(f"\nGenerated sentences saved to {new_file_path}")

if __name__ == "__main__":
    # Get total_sentences from command line argument if provided
    if len(sys.argv) > 1:
        try:
            total_sentences = int(sys.argv[1])
            generate_sentences(total_sentences)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid number of sentences.")
            sys.exit(1)
    else:
        # Example: generate 10 sentences by default
        generate_sentences()
    
    # You can also specify a different number, e.g.:
    # generate_sentences(total_sentences=50) 