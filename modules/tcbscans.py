import requests
from bs4 import BeautifulSoup
import os
import sys

# Adjust import path based on how the script is run
if __name__ == "__main__":
    # Add the parent directory to the path when running directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from track_data import open_json, save_json
else:
    # Normal import when used as a module
    from track_data import open_json, save_json

def get_newest_chapter_info(email_read=False):
    tracking_file = os.path.join(os.path.dirname(__file__), 'tcbscans.json')
    tracking_data = open_json(tracking_file)
    
    # Initialize if empty
    if not tracking_data:
        tracking_data = {
            "current_chapter": {},
            "seen_chapters": {}
        }
    
    # If email was read, update seen chapters
    if email_read and tracking_data.get("current_chapter"):
        tracking_data["seen_chapters"][tracking_data["current_chapter"]["title"]] = tracking_data["current_chapter"]
    
    # URL of the manga page (updated URL based on new structure)
    url = 'https://cupve.com'
    
    # Send a GET request
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the request failed
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all chapter entries using the new structure
        # Look for <a> tags with chapter links
        chapter_links = soup.find_all('a', href=lambda href: href and 'one-piece-chapter-' in href)
        
        # Extract the newest chapter (should be the first one)
        newest_chapter = chapter_links[0] if chapter_links else None
        
        if newest_chapter:
            chapter_title = newest_chapter.get_text(strip=True)
            chapter_url = newest_chapter['href']
            
            # There may not be a subtitle in the new structure
            # Extracting chapter number from the title or URL
            chapter_number = chapter_url.split('one-piece-chapter-')[1].strip('/')
            chapter_subtitle = f"Chapter {chapter_number}"
            
            current_info = {
                'title': chapter_title,
                'subtitle': chapter_subtitle,
                'url': chapter_url
            }
            
            # Update current chapter in tracking
            tracking_data["current_chapter"] = current_info
            
            # Check if chapter is new
            is_new = chapter_title not in tracking_data.get("seen_chapters", {})
            
            # Save updated tracking data
            save_json(tracking_file, tracking_data)
            
            if is_new:
                header = '<h3>Latest Chapter (New!)</h3>'
            else:
                header = '<h3>Latest Chapter</h3>'
            
            # Format the result as an HTML string with <tr><td class='content'>
            result = f'<tr><td class="content">{header}<a href="{chapter_url}">{chapter_title}</a><br>{chapter_subtitle}</td></tr>'
            return result
        else:
            return "<tr><td class='content'>No chapters found. The website structure may have changed.</td></tr>"
    
    except Exception as e:
        return f"<tr><td class='content'>Error fetching chapter information: {str(e)}</td></tr>"

# Run this code when the script is executed directly
if __name__ == "__main__":
    result = get_newest_chapter_info()
    print(result)
