import json
import os
import re

def extract_chapter_number(filename):
    match = re.search(r'chapter_(\d+)\.txt', filename)
    if match:
        return int(match.group(1))
    return None

# Read the info JSON file
try:
    with open('output/mục_thần_ký_info.json', 'r', encoding='utf-8') as f:
        info = json.load(f)
except Exception as e:
    print(f"Error reading info.json: {e}")
    exit(1)

# Create a dictionary mapping chapter numbers to titles
chapter_titles = {}
for chapter in info['chapters']:
    match = re.search(r'Chương (\d+):', chapter['title'])
    if match:
        chapter_num = int(match.group(1))
        chapter_titles[chapter_num] = chapter['title']

# Process each chapter file in the output directory
txt_dir = 'output/mục_thần_ký_txt'
for filename in os.listdir(txt_dir):
    if not filename.startswith('chapter_') or not filename.endswith('.txt'):
        continue
    
    chapter_num = extract_chapter_number(filename)
    if chapter_num is None:
        continue
    
    filepath = os.path.join(txt_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the file already has a chapter title
        if not re.search(r'^#.*Chương \d+:', content, re.MULTILINE):
            if chapter_num in chapter_titles:
                # Replace the generic title with the actual chapter title
                new_content = content.replace('# Mục Thần Ký', f"# {chapter_titles[chapter_num]}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Added title to chapter {chapter_num}")
    except Exception as e:
        print(f"Error processing {filename}: {e}") 