import requests
from bs4 import BeautifulSoup
import os
import datetime
from track_data import open_json, save_json

def fetch_steam_wishlist():
    url = "https://store.steampowered.com/search/?filter=popularwishlist"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    games = []
    for game in soup.find_all('a', class_='search_result_row')[:10]:
        title = game.find('span', class_='title').text
        link = game['href']
        games.append({'title': title, 'link': link})
    
    return games

def track_games(current_games, email_read):
    """Track games while maintaining history"""
    json_file_path = os.path.join(os.path.dirname(__file__), 'steam_wishlist.json')
    data = open_json(json_file_path)
    
    # Initialize with proper structure if empty
    if not data:
        data = {
            'current_top_games': [],
            'seen_games': {}
        }
    
    # If email was read, mark all games in the current list as seen
    if email_read:
        for game in data['current_top_games']:
            data['seen_games'][game['title']] = {
                'first_seen': data['seen_games'].get(game['title'], {}).get('first_seen', datetime.datetime.now().isoformat()),
                'last_seen': datetime.datetime.now().isoformat(),
                'link': game['link']
            }
    
    # Update current games list
    data['current_top_games'] = current_games
    
    # Save updated data
    save_json(json_file_path, data)
    
    # Return current games and whether they're new
    result = []
    for game in current_games:
        is_new = game['title'] not in data['seen_games']
        result.append((game, is_new))
    
    return result

def get_tracked_games_html(email_read=False):
    current_games = fetch_steam_wishlist()
    tracked_games = track_games(current_games, email_read)
    
    results_output = "<tr><td class='content'>"
    results_output += "<h3>Top Steam Wishlist Games</h3>"
    for i, (game, is_new) in enumerate(tracked_games[:10]):
        new_mark = " (New!)" if is_new else ""
        output = f"{i + 1}. <a href='{game['link']}'>{game['title']}</a>{new_mark}<br><br>"
        results_output += output
    results_output += "</td></tr>"
    return results_output
