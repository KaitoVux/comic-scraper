import os
import json
import re

def clean_text(text):
    """Clean up text content by removing redundant information and formatting"""
    # Remove navigation elements and website headers
    text = re.sub(r'Wikidich.*?Chương \d+:', '', text, flags=re.DOTALL)
    text = re.sub(r'《 Chương trước.*?Chương tiếp 》', '', text, flags=re.DOTALL)
    
    # Remove navigation at the end
    text = re.sub(r'《 Chương trước.*$', '', text, flags=re.DOTALL)
    
    # Remove recommended novels section
    text = re.sub(r'Truyện Hot Mới.*$', '', text, flags=re.DOTALL)
    
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def export_chapters_to_txt(novel_title, chapters_dir, output_dir):
    """Export chapter content to individual txt files"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get all chapter files
    chapter_files = sorted([f for f in os.listdir(chapters_dir) if f.startswith('chapter_') and f.endswith('.json')])
    
    for chapter_file in chapter_files:
        with open(os.path.join(chapters_dir, chapter_file), 'r', encoding='utf-8') as f:
            chapter_data = json.load(f)
        
        # Create clean chapter text
        chapter_text = f"# {chapter_data.get('title', 'Unknown Chapter')}\n\n"
        chapter_text += clean_text(chapter_data.get('content_text', ''))
        
        # Save to txt file
        output_file = os.path.join(output_dir, f"{chapter_file.replace('.json', '.txt')}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chapter_text)
        
        print(f"Exported: {output_file}")
    
    print(f"Exported {len(chapter_files)} chapters to {output_dir}")

def export_novel_to_single_file(novel_title, chapters_dir, output_dir):
    """Export all chapters to a single text file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get all chapter files
    chapter_files = sorted([f for f in os.listdir(chapters_dir) if f.startswith('chapter_') and f.endswith('.json')])
    
    # Create file for the whole novel
    output_file = os.path.join(output_dir, f"{novel_title}_full.txt")
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # Write novel title
        out_f.write(f"# {novel_title}\n\n")
        
        for chapter_file in chapter_files:
            with open(os.path.join(chapters_dir, chapter_file), 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)
            
            # Create clean chapter text
            chapter_text = f"## {chapter_data.get('title', 'Unknown Chapter')}\n\n"
            chapter_text += clean_text(chapter_data.get('content_text', ''))
            chapter_text += "\n\n" + "-" * 50 + "\n\n"
            
            # Write to the output file
            out_f.write(chapter_text)
    
    print(f"Exported all chapters to: {output_file}")

if __name__ == "__main__":
    # Set up paths
    novel_title = "mục_thần_ký"
    base_dir = "output"
    chapters_dir = os.path.join(base_dir, f"{novel_title}_chapters")
    txt_output_dir = os.path.join(base_dir, f"{novel_title}_txt")
    
    # Export to individual files
    export_chapters_to_txt(novel_title, chapters_dir, txt_output_dir)
    
    # Export to a single file
    export_novel_to_single_file(novel_title, chapters_dir, txt_output_dir) 