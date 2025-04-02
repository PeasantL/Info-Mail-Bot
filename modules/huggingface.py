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

def scrape_huggingface_models(email_read=False):
    tracking_file = os.path.join(os.path.dirname(__file__), 'huggingface.json')
    tracking_data = open_json(tracking_file)
    
    # Initialize if empty
    if not tracking_data:
        tracking_data = {
            "current_models": {},
            "seen_models": {}
        }
    
    # If email was read, update seen models with current models
    if email_read and tracking_data.get("current_models"):
        for model, details in tracking_data["current_models"].items():
            tracking_data["seen_models"][model] = details
    
    # The URL to scrape
    url = "https://huggingface.co/models?sort=trending&search=24b"

    # Send a GET request to the URL
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all the relevant article elements with the class 'overview-card-wrapper group/repo'
        models = soup.find_all("article", class_="overview-card-wrapper group/repo")
        
        # Initialize data storage for the current run
        current_data = {}
        html_output = "<tr><td class='content'><h3>Hugging Face Models: 12b</h3>"
        
        # Index to track each model entry
        index = 1
        
        for model in models[:6]: 
            # Extract the link
            link = model.find("a", class_="flex items-center justify-between gap-4 p-2")['href']
            # Full link for correct redirection
            full_link = f"https://huggingface.co{link}"
            # Extract the title (assuming the title is in the link text)
            title = link.split("/")[-1]
            # Extract the release date
            release_date = model.find("time").text.strip()
            
            # Extract all SVG icons and their associated text
            svg_elements = model.find_all("svg", {"aria-hidden": "true"})
            svg_texts = [svg.find_next_sibling(string=True).strip() for svg in svg_elements]
            
            # Determine if 'type' is present (i.e., more than 2 SVG elements)
            if len(svg_texts) > 2:
                # Assume the first SVG is 'type' and discard it
                downloads = svg_texts[1]
                likes = svg_texts[2]
            elif len(svg_texts) == 2:
                # No 'type' present, so use the first two directly
                downloads = svg_texts[0]
                likes = svg_texts[1]
            else:
                downloads = "Unknown"
                likes = "Unknown"
            
            # Check if this model is new compared to the seen models
            is_new = title not in tracking_data.get("seen_models", {})
            
            # Store the current data
            current_data[title] = {
                "link": full_link,
                "release_date": release_date,
                "downloads": downloads,
                "likes": likes
            }
            
            # Build the HTML output
            html_output += f'<div>{index}. <a href="{full_link}" target="_blank">{title}</a>'
            if is_new:
                html_output += " (New!)"
            html_output += f'<br>  Released: {release_date}<br>'
            html_output += f'  Downloads: {downloads}<br>'
            html_output += f'  Likes: {likes}<br><br></div>'
            
            # Increment the index for the next model
            index += 1
        
        html_output += "</td></tr>"
        
        # Update the tracking data with the current data
        tracking_data["current_models"] = current_data
        save_json(tracking_file, tracking_data)
        
        # Return the HTML string
        return html_output

    else:
        return f"<tr><td class='content'><p>Failed to retrieve content. Status code: {response.status_code}</p></td></tr>"

# Run this code when the script is executed directly
if __name__ == "__main__":
    result = scrape_huggingface_models()
    print(result)
