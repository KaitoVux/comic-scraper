import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from urllib.parse import urljoin

def scrape_chapter_content(url, base_url="https://wikidich.vn"):
    """
    Scrape content from a chapter page
    
    Args:
        url (str): URL of the chapter page
        base_url (str): Base URL of the website
        
    Returns:
        dict: Chapter information and content
    """
    if not url.startswith('http'):
        url = urljoin(base_url, url)
    
    print(f"Scraping chapter: {url}")
    
    # Random delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching chapter: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract chapter data
    chapter_data = {}
    
    # Title - try different possibilities
    title_candidates = [
        soup.find('h1', class_='chapter-title'),
        soup.find('h1'),
        soup.find('h2', class_='chapter-title'),
        soup.find('h2')
    ]
    
    for title_element in title_candidates:
        if title_element and title_element.text.strip():
            chapter_data['title'] = title_element.text.strip()
            break
    else:
        chapter_data['title'] = "Unknown Chapter"
    
    # Content - try different content containers
    content_candidates = [
        soup.find('div', class_='chapter-content'),
        soup.find('div', class_='entry-content'),
        soup.find('div', class_='content'),
        soup.find('div', class_='truyen'),
        soup.find('article'),
        soup.find('main')
    ]
    
    content_element = None
    for candidate in content_candidates:
        if candidate and len(candidate.get_text(strip=True)) > 100:  # Must have significant text
            content_element = candidate
            break
    
    if content_element:
        # Clean up the content, removing unnecessary elements
        for element in content_element.find_all(['script', 'style', 'ins', 'iframe', 'ads']):
            element.decompose()
            
        # Get content as HTML and text
        chapter_data['content_html'] = content_element.prettify()
        chapter_data['content_text'] = content_element.get_text(separator='\n\n', strip=True)
        
        # Print a preview
        content_preview = chapter_data['content_text'][:150] + "..." if len(chapter_data['content_text']) > 150 else chapter_data['content_text']
        print(f"Content preview: {content_preview}")
    else:
        # Fallback: if no content container found, try getting the main text of the page
        main_text = soup.get_text(separator='\n\n', strip=True)
        
        # Remove headers, footers, and navigation text by focusing on the middle portion
        lines = main_text.split('\n')
        if len(lines) > 20:  # If there's enough text
            main_content = '\n'.join(lines[int(len(lines)*0.2):int(len(lines)*0.8)])  # Middle 60%
            chapter_data['content_html'] = f"<div>{main_content}</div>"
            chapter_data['content_text'] = main_content
            print(f"Using fallback content extraction method")
        else:
            chapter_data['content_html'] = ""
            chapter_data['content_text'] = ""
            print(f"Could not extract content")
    
    return chapter_data

def scrape_all_chapters(novel_data, specific_chapters=None, output_dir="output", delay=2.0):
    """
    Scrape content for chapters in a novel
    
    Args:
        novel_data (dict): Novel information with chapters
        specific_chapters (list): Specific chapters to scrape (if None, uses novel_data['chapters'])
        output_dir (str): Directory to save chapter content
        delay (float): Delay between chapter requests
        
    Returns:
        list: Updated chapters with content
    """
    if not novel_data or 'chapters' not in novel_data:
        print("No chapters to scrape")
        return []
    
    # Use specific chapters if provided, otherwise use all chapters
    chapters_to_scrape = specific_chapters if specific_chapters is not None else novel_data['chapters']
    
    if not chapters_to_scrape:
        print("No chapters to scrape")
        return novel_data['chapters']
    
    # Create chapters directory
    novel_title = novel_data.get('title', 'unknown').replace(' ', '_').lower()
    chapters_dir = os.path.join(output_dir, f"{novel_title}_chapters")
    
    if not os.path.exists(chapters_dir):
        os.makedirs(chapters_dir)
    
    total_chapters = len(chapters_to_scrape)
    print(f"Preparing to scrape {total_chapters} chapters")
    
    # Map the specific chapters back to their indices in the full chapters list
    chapter_indices = {}
    if specific_chapters is not None:
        for chapter in specific_chapters:
            for i, full_chapter in enumerate(novel_data['chapters']):
                if chapter['url'] == full_chapter['url']:
                    chapter_indices[chapter['url']] = i
                    break
    
    # Scrape each chapter
    for i, chapter in enumerate(chapters_to_scrape):
        print(f"Scraping chapter {i+1}/{total_chapters}: {chapter['title']}")
        
        # Check if chapter JSON already exists
        chapter_index = chapter_indices.get(chapter['url'], i)
        chapter_filename = f"chapter_{chapter_index+1:04d}.json"
        chapter_path = os.path.join(chapters_dir, chapter_filename)
        
        if os.path.exists(chapter_path):
            print(f"  Chapter already exists: {chapter_filename}, skipping...")
            
            # Load existing chapter data
            with open(chapter_path, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)
                
            # Update the corresponding chapter in novel_data
            if chapter['url'] in chapter_indices:
                novel_data['chapters'][chapter_indices[chapter['url']]].update(chapter_data)
            
            continue
        
        # Add a delay between requests to avoid rate limiting
        if i > 0:
            time.sleep(delay)
        
        # Scrape chapter content
        chapter_data = scrape_chapter_content(chapter['url'])
        
        if chapter_data:
            # Create full chapter data by combining the original chapter data with the content
            full_chapter_data = {**chapter, **chapter_data}
            
            # Save to file
            with open(chapter_path, 'w', encoding='utf-8') as f:
                json.dump(full_chapter_data, f, ensure_ascii=False, indent=4)
            
            print(f"  Saved to {chapter_filename}")
            
            # Update the corresponding chapter in novel_data
            if chapter['url'] in chapter_indices:
                novel_data['chapters'][chapter_indices[chapter['url']]].update(chapter_data)
        else:
            print(f"  Failed to scrape chapter")
    
    return novel_data['chapters']

if __name__ == "__main__":
    # Load novel data from the previously created JSON file
    output_dir = "output"
    
    try:
        novel_title = "mục_thần_ký"  # This should match the title from wikidich_scraper.py
        novel_file = os.path.join(output_dir, f"{novel_title}_info.json")
        
        with open(novel_file, 'r', encoding='utf-8') as f:
            novel_data = json.load(f)
            
        print(f"Loaded novel data: {novel_data['title']}")
        
        # Scrape chapter content (limit to 5 chapters for testing)
        chapters_to_scrape = novel_data['chapters'][:5]
        updated_chapters = scrape_all_chapters(novel_data, specific_chapters=chapters_to_scrape, output_dir=output_dir)
        
        # Update the novel data with chapter content
        novel_data['chapters'] = updated_chapters
        
        # Save updated novel data
        with open(os.path.join(output_dir, f"{novel_title}_with_content.json"), 'w', encoding='utf-8') as f:
            json.dump(novel_data, f, ensure_ascii=False, indent=4)
            
        print("Chapter scraping complete!")
        
    except FileNotFoundError:
        print(f"Novel data file not found. Please run wikidich_scraper.py first.")
    except Exception as e:
        print(f"Error: {e}") 