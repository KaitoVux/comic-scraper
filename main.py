#!/usr/bin/env python3
import argparse
import os
import sys
from wikidich_scraper import scrape_wikidich_novel, save_to_json, save_to_csv
from chapter_scraper import scrape_all_chapters

def main():
    parser = argparse.ArgumentParser(description='Scrape novels from wikidich.vn')
    parser.add_argument('--info-only', action='store_true', help='Only scrape novel info and chapter list without downloading content')
    parser.add_argument('--max-pages', type=int, default=19, help='Maximum number of pages to scrape')
    parser.add_argument('--chapters', type=int, default=3, help='Number of chapters to download content (use -1 for all chapters)')
    args = parser.parse_args()
    
    url = "https://wikidich.vn/muc-than-ky-convert"
    
    print(f"Scraping novel from: {url}")
    novel_data = scrape_wikidich_novel(url, follow_pagination=True, max_pages=args.max_pages)
    
    if novel_data:
        # Create output directory if it doesn't exist
        if not os.path.exists('output'):
            os.makedirs('output')
            
        # Save the data
        title = novel_data.get('title', 'unknown').replace(' ', '_').lower()
        save_to_json(novel_data, f"output/{title}_info.json")
        save_to_csv(novel_data, f"output/{title}_chapters.csv")
        
        # If not info-only, download chapter content
        if not args.info_only and args.chapters != 0:
            chapters_to_download = []
            if args.chapters > 0:
                print(f"\nDownloading content for {args.chapters} chapters...")
                chapters_to_download = novel_data['chapters'][:args.chapters]
            else:
                print(f"\nDownloading content for ALL chapters...")
                chapters_to_download = novel_data['chapters']
            
            # Scrape chapter content
            updated_chapters = scrape_all_chapters(
                novel_data,
                specific_chapters=chapters_to_download,
                output_dir='output',
                delay=1.0  # 1 second delay between requests
            )
            
            # Update the novel data with chapter content
            novel_data['chapters'] = updated_chapters
            
            # Save the complete data with content
            save_to_json(novel_data, f"output/{title}_complete.json")
            print(f"Complete data with chapter content saved to: output/{title}_complete.json")
        
        print("\nScraping completed successfully!")
        print(f"Novel information saved to: output")
    else:
        print("Failed to scrape data.")

if __name__ == "__main__":
    main() 