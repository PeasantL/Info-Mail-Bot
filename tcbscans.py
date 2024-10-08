import requests
from bs4 import BeautifulSoup
from track_data import open_json, save_json

def get_newest_chapter_info():
    
    tracking_file = 'tcbscans.json'
    
    # URL of the manga page
    url = 'https://tcbscans.me/mangas/5/one-piece'
    
    # Send a GET request
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request failed
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all chapter entries using the class 'block'
    chapters = soup.find_all('a', class_='block')
    
    # Extract chapter titles and URLs
    newest_chapter = chapters[0] if chapters else None
    
    if newest_chapter:
        chapter_title = newest_chapter.find('div', class_='text-lg font-bold').get_text(strip=True)
        chapter_subtitle = newest_chapter.find('div', class_='text-gray-500').get_text(strip=True)
        chapter_url = 'https://tcbscans.me' + newest_chapter['href']
        
        current_info = {
            'title': chapter_title,
            'subtitle': chapter_subtitle,
            'url': chapter_url
        }
        
        saved_info = open_json(tracking_file)
        
        # Compare with saved chapter info
        if saved_info and saved_info['title'] == chapter_title:
            header = '<h3>Latest Chapter</h3>'
        else:
            header = '<h3>Latest Chapter (New!)</h3>'
            save_json(tracking_file, current_info)
        
        # Format the result as an HTML string with <tr><td class='content'>
        result = f'<tr><td class="content">{header}<a href="{chapter_url}">{chapter_title}</a><br>{chapter_subtitle}</td></tr>'
        return result
    else:
        return "<tr><td class='content'>No chapters found.</td></tr>"