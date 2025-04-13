import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs

def scrape_wikidich_novel(url, follow_pagination=True, max_pages=20):
    """
    Scrape novel information and chapters from wikidich.vn
    
    Args:
        url (str): URL of the novel page
        follow_pagination (bool): Whether to follow pagination links to get all chapters
        max_pages (int): Maximum number of pages to scrape
        
    Returns:
        dict: Novel information and chapters
    """
    # Send request to the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # For debugging
        print(f"Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract novel information
    novel_info = {}
    
    # Title - looking for the title which could be in h1 or h2
    title_element = soup.find('h1', class_='post-title') or soup.find('h1') or soup.find('h2')
    if title_element and 'Mục Thần Ký' in title_element.text:
        novel_info['title'] = title_element.text.strip()
    else:
        # Try to find it directly from the content based on the example
        title_match = soup.find(string=lambda text: text and 'Mục Thần Ký' in text)
        if title_match:
            novel_info['title'] = 'Mục Thần Ký'
        else:
            novel_info['title'] = "Unknown"
    
    # Author, genre, status, chapters, views - adjust selector based on content
    info_text = soup.get_text()
    
    # Extract info based on patterns from the provided content
    if 'Tác giả:' in info_text:
        author_section = info_text.split('Tác giả:')[1].split('\n')[0].strip()
        novel_info['author'] = author_section
    
    if 'Thể loại:' in info_text:
        genre_section = info_text.split('Thể loại:')[1].split('\n')[0].strip()
        novel_info['genres'] = [genre.strip() for genre in genre_section.split(',')]
    
    if 'Số chương:' in info_text:
        chapter_count_section = info_text.split('Số chương:')[1].split('\n')[0].strip()
        novel_info['chapter_count'] = chapter_count_section
    
    if 'Lượt xem:' in info_text:
        views_section = info_text.split('Lượt xem:')[1].split('\n')[0].strip()
        novel_info['views'] = views_section
    
    if 'Trạng thái:' in info_text:
        status_section = info_text.split('Trạng thái:')[1].split('\n')[0].strip()
        novel_info['status'] = status_section
    
    # Get novel ID from the first page's next button
    next_button = soup.find('a', attrs={'onclick': re.compile(r'page\(\d+,\d+\)')})
    novel_id = None
    if next_button:
        onclick = next_button.get('onclick', '')
        match = re.search(r'page\((\d+),\d+\)', onclick)
        if match:
            novel_id = match.group(1)
            print(f"Found novel ID: {novel_id}")
    
    # Start with the chapters from the first page (using HTML parsing)
    chapters = get_chapters_from_page(soup)
    print(f"Found {len(chapters)} chapters on page 1 (HTML parsing)")
    
    if novel_id and follow_pagination:
        # Use the direct API endpoint to get chapters from remaining pages
        for current_page in range(2, max_pages + 1):
            print(f"Fetching chapter list from API for page {current_page}")
            
            # Construct the API URL
            api_url = f"https://wikidich.vn/get/listchap/{novel_id}?page={current_page}"
            
            # Add a delay to avoid rate limiting
            time.sleep(1)
            
            try:
                # Fetch the data from the API
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                
                # Parse the JSON response
                json_data = response.json()
                print(f"JSON parsed successfully for page {current_page}")
                
                if 'data' in json_data:
                    # Extract the HTML content from the JSON response
                    # The JSON already contains valid HTML with properly escaped characters
                    html_content = json_data['data']
                    
                    # Parse the HTML string directly
                    page_soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract chapter links - look specifically for links in the list items
                    chapter_links = page_soup.find_all('a', href=True)
                    page_chapters = []
                    
                    for link in chapter_links:
                        if link.text and 'Chương' in link.text:
                            page_chapters.append({
                                'title': link.text.strip(),
                                'url': link['href']
                            })
                    
                    print(f"Found {len(chapter_links)} links, {len(page_chapters)} chapter links")
                    
                    if page_chapters:
                        chapters.extend(page_chapters)
                        print(f"Added {len(page_chapters)} chapters from page {current_page}")
                    else:
                        print(f"No chapters found on page {current_page}, stopping pagination")
                        break
                    
                    # Check if this is the last page by looking for pagination links
                    paging_div = page_soup.find('div', class_='paging')
                    if paging_div:
                        last_page_link = paging_div.find('a', string='Cuối')
                        if last_page_link and 'onclick' in last_page_link.attrs:
                            match = re.search(r'page\(\d+,(\d+)\)', last_page_link['onclick'])
                            if match:
                                total_pages = int(match.group(1))
                                print(f"Total pages: {total_pages}")
                                if current_page >= total_pages:
                                    print("Reached the last page")
                                    break
                else:
                    print(f"No data field in API response for page {current_page}")
                    print(f"Response keys: {list(json_data.keys())}")
                    break
            except Exception as e:
                print(f"Error fetching chapter list from API for page {current_page}: {e}")
                print(f"Response content: {response.text[:200]}")
                break
    
    # Remove any duplicates by URL
    unique_chapters = []
    seen_urls = set()
    for chapter in chapters:
        if chapter['url'] not in seen_urls and not chapter['url'].startswith('javascript'):
            unique_chapters.append(chapter)
            seen_urls.add(chapter['url'])
    
    novel_info['chapters'] = unique_chapters
    
    # Print debug info
    print(f"Found title: {novel_info['title']}")
    print(f"Found {len(unique_chapters)} chapters total")
    
    return novel_info

def get_chapters_from_page(soup):
    """Extract chapter links from a page"""
    chapters = []
    
    # Look specifically for the element with ID "chapter-list"
    chapter_list = soup.find(id='chapter-list')
    
    if chapter_list:
        print("Found #chapter-list container!")
        # Extract all links in the chapter list
        chapter_links = chapter_list.find_all('a', href=True)
        for link in chapter_links:
            if link.text and len(link.text.strip()) > 0:
                chapters.append({
                    'title': link.text.strip(),
                    'url': link['href']
                })
    else:
        print("No #chapter-list container found, trying alternative methods...")
        
        # Try to find chapter links in potential chapter list containers
        chapter_containers = soup.find_all(['ul', 'div'], class_=lambda c: c and ('list-chapter' in c or 'chapter' in c or 'list' in c))
        
        if not chapter_containers:
            # If specific containers not found, look for chapters by pattern matching
            # Based on the content, chapters follow the pattern "Chương X: Title"
            chapter_links = soup.find_all('a', string=lambda s: s and s.strip().startswith('Chương '))
            
            if not chapter_links:
                # Try other variations
                chapter_links = soup.find_all('a', href=True)
                for link in chapter_links:
                    if link.text and any(marker in link.text for marker in ['Chương', 'chương', 'Chapter']):
                        chapters.append({
                            'title': link.text.strip(),
                            'url': link['href']
                        })
            else:
                for link in chapter_links:
                    chapters.append({
                        'title': link.text.strip(),
                        'url': link['href']
                    })
        else:
            # Try each container
            for container in chapter_containers:
                links = container.find_all('a', href=True)
                for link in links:
                    # Check if it's likely a chapter link
                    if link.text and len(link.text.strip()) > 0 and 'Chương' in link.text:
                        chapters.append({
                            'title': link.text.strip(),
                            'url': link['href']
                        })
        
        # If we found no chapters using container approach, try direct list items
        if not chapters:
            # Based on the provided content, try specifically with pattern matching
            for li in soup.find_all('li'):
                text = li.text.strip()
                if text.startswith(('Chương', 'chương')):
                    link = li.find('a', href=True)
                    if link:
                        chapters.append({
                            'title': text,
                            'url': link['href']
                        })
    
    # Filter out pagination links that might have been included
    return [ch for ch in chapters if ch['title'].strip().startswith(('Chương', 'chương', 'Chapter')) 
            and not ch['url'].startswith('javascript')]

def save_to_json(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")

def save_to_csv(data, filename):
    """Save chapters to CSV file"""
    if not data or 'chapters' not in data:
        print("No chapter data to save")
        return
        
    df = pd.DataFrame(data['chapters'])
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Chapters saved to {filename}")

if __name__ == "__main__":
    url = "https://wikidich.vn/muc-than-ky-convert"
    
    print(f"Scraping novel information from {url}...")
    novel_data = scrape_wikidich_novel(url, follow_pagination=True, max_pages=20)
    
    if novel_data:
        # Create output directory if it doesn't exist
        if not os.path.exists('output'):
            os.makedirs('output')
            
        # Save the data
        title = novel_data.get('title', 'unknown').replace(' ', '_').lower()
        save_to_json(novel_data, f"output/{title}_info.json")
        save_to_csv(novel_data, f"output/{title}_chapters.csv")
    else:
        print("Failed to scrape data.") 