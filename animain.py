# using SeaDex (releases.moe) for Finished Airing shows
# using SubsPlease (subsplease.org) for Airing shows

# APIs that can be used: 
# MAL - pip install mal-api --> from mal import AnimeSearch
# AniList - pip install anilistpython --> https://github.com/ReZeroE/AnilistPython

# Other resources for reference:
# nyaascraper: https://github.com/zaini/nyaascraper
# miru: https://github.com/ThaUnknown/miru
# nyaapy: https://github.com/JuanjoSalvador/NyaaPy
# nyaadownloader: https://github.com/marcpinet/nyaadownloader


import requests # pip install requests
from bs4 import BeautifulSoup # pip install beautifulsoup
import pyperclip # pip install pyperclip

def search_anilist(anime_title):
    # GraphQL query with pagination (Page)
    query = '''
    query ($search: String) {
        Page {
            media (search: $search, type: ANIME) {
                id
                title {
                    romaji
                    english
                }
            }
        }
    }
    '''
    
    # Variables for the GraphQL query
    variables = {
        'search': anime_title
    }
    
    # Make the HTTP API request
    response = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        data = response.json()
        if data['data']['Page']['media']:
            animes = data['data']['Page']['media']
            results = []
            for anime in animes:
                results.append({
                    'id': anime['id'],
                    'title_romaji': anime['title']['romaji'],
                    'title_english': anime['title']['english']
                })
            return results
    return None

def get_anime_status(anime_id):
    # GraphQL query to get the status of a specific anime by its ID
    query = '''
    query ($id: Int) {
        Media (id: $id, type: ANIME) {
            id
            title {
                romaji
                english
            }
            status
        }
    }
    '''
    
    # Variables for the GraphQL query
    variables = {
        'id': anime_id
    }
    
    # Make the HTTP API request
    response = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        data = response.json()
        if data['data']['Media']:
            anime = data['data']['Media']
            return {
                'id': anime['id'],
                'title_romaji': anime['title']['romaji'],
                'title_english': anime['title']['english'],
                'status': anime['status']
            }
    return None

# Mapping for status descriptions
status_map = {
    'FINISHED': 'Finished Airing',
    'RELEASING': 'Currently Airing',
    'NOT_YET_RELEASED': 'Not Yet Released',
    'CANCELLED': 'Cancelled',
    'HIATUS': 'On Hiatus'
}

# example api calls:
# https://releases.moe/api/collections/entries/records?expand=trs&filter=alID=166216
# https://releases.moe/api/collections/entries/records?filter=alID=166216
# https://releases.moe/api/collections/torrents/records/wehqjgww9ch7odq
def get_url(anime_id, anime_status, title_romaji):
    # change 'subsplease' to 'erai-raws' if returning errors, or any other release group of choice
    subsplease_base_url = "https://nyaa.land/user/subsplease?f=0&c=1_2&q={}+1080p&o=desc&p=1"
    seadex_base_url = "https://releases.moe/"
    subsplease_batch_base_url = "https://nyaa.land/user/subsplease?f=0&c=1_2&q={}+1080p+batch&o=desc&p=1"
    seadex_api_url = "https://releases.moe/api/collections/entries/records?expand=trs&filter=alID={}"

    def custom_quote(s):
        return s.replace(" ", "+")

    if anime_status == 'FINISHED':
        # Check SeaDex API for entry
        api_response = requests.get(seadex_api_url.format(anime_id))
        if api_response.status_code == 200:
            data = api_response.json()
            if data['totalItems'] > 0:
                # SeaDex entry exists
                notes = data['items'][0]['notes']
                print("\nHere are the Seadex best releases:\n")
                print(f"(Source: {seadex_base_url}{anime_id})")
                print (f"{notes}\n")
                # Collect unique release groups with "Nyaa" tracker
                release_groups = set()
                for item in data['items'][0]['trs']:
                    for tr in data['items'][0]['expand']['trs']:
                        if tr['id'] == item and tr['tracker'] == "Nyaa":
                            release_groups.add(tr['releaseGroup'])

                # Print release groups in a numbered list
                print("Release Groups:")
                for i, release_group in enumerate(release_groups, 1):
                    print(f"{i}. {release_group}")

                # Prompt user for input
                choice = int(input("Enter the number of the desired release group: "))

                # Find and print the corresponding URL
                for item in data['items'][0]['trs']:
                    for tr in data['items'][0]['expand']['trs']:
                        if tr['id'] == item and tr['tracker'] == "Nyaa" and tr['releaseGroup'] == list(release_groups)[choice - 1]:
                            original_url = tr['url']
                            new_url = original_url.replace(".si/", ".land/")
                            return f"{new_url}"
                
        
        # If no SeaDex entry or API call failed, fall back to SubsPlease batch
        formatted_title = custom_quote(title_romaji)
        return subsplease_batch_base_url.format(formatted_title)

    elif anime_status == 'RELEASING':
        formatted_title = custom_quote(title_romaji)
        return subsplease_base_url.format(formatted_title)

    elif anime_status == 'NOT_YET_RELEASED':
        print(f"The show '{title_romaji}' has not been released yet.")
        return None

    else:
        print(f"Unknown anime status: {anime_status}")
        return None
    
def get_magnet(url):
    # Determine the type of URL
    if "/view/" in url:
        return scrape_specific_file(url)
    else:
        return scrape_file_list(url)
    
def scrape_specific_file(url):
    # Fetch the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the magnet link
    magnet_link = soup.find('a', href=lambda x: x and x.startswith('magnet:'))
    
    if magnet_link:
        print(f"Magnet Link: {magnet_link['href']}")
        return magnet_link['href']
    else:
        print("No magnet link found on this page.")
        return None

def scrape_file_list(url):
    # Fetch the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table (you may need to adjust this selector)
    table = soup.find('table')

    if not table:
        print("Table not found on the webpage.")
        return None

    # Find all rows in the table
    rows = table.find_all('tr')

    # Extract file names and magnet links
    files = []
    for row in rows[1:]:  # Skip header row
        name_column = row.find('td', colspan="2")
        if name_column:
            # Find the filename link (excluding the comments link)
            filename_link = name_column.find('a', class_=lambda x: x != 'comments')
            if filename_link:
                name = filename_link.text.strip()
                
                # Find the magnet link in the same row
                magnet_icon = row.find('i', class_='fa-magnet')
                if magnet_icon and magnet_icon.parent.name == 'a':
                    link = magnet_icon.parent['href']
                    files.append((name, link))

    if not files:
        print("No files with magnet links found.")
        return None

    # Display file names to user
    print("Available files:")
    for i, (name, _) in enumerate(files, 1):
        print(f"{i}. {name}")

    # Prompt user for selection
    while True:
        try:
            choice = int(input("\nEnter the number of the file you want to select: "))
            if 1 <= choice <= len(files):
                selected_file, selected_link = files[choice - 1]
                print(f"\nYou selected: {selected_file}")
                print(f"\nMagnet Link: {selected_link}")
                return selected_link
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    # Usage
    anime_title = input("Enter Anime: ")
    results = search_anilist(anime_title)

    if results:
        # Display results in a numbered list
        print("\nSearch results:\n")
        for i, result in enumerate(results, start=1):
            print(f"{i}. AniList ID: {result['id']}")
            print(f"   Title (Romaji): {result['title_romaji']}")
            print(f"   Title (English): {result['title_english']}")
            print("\n---\n")
        
        while True:
            try:
                # Prompt user to select a result
                selection = int(input("Enter the number of the anime you want to select: ")) - 1
                
                if 0 <= selection < len(results):
                    selected_anime = results[selection]
                    print(f"You selected: '{selected_anime['title_romaji']}' (AniList ID: {selected_anime['id']})")

                    # Fetch status of the selected anime
                    anime_status = get_anime_status(selected_anime['id'])
                    if anime_status:
                        status_description = status_map.get(anime_status['status'], "Unknown status")
                        print(f"'{anime_status['title_romaji']}' status: {status_description}.")
                        
                        # Get the URL based on the anime status
                        url = get_url(selected_anime['id'], anime_status['status'], selected_anime['title_romaji'])
                        if url:
                            print(f"Nyaa URL: {url}")
                            magnet_link = get_magnet(url)
                            if magnet_link:
                                while True:
                                    copy_input = input("Do you want to copy the magnet link? [Y/N]: ").strip().upper()
                                    if copy_input == 'Y':
                                        pyperclip.copy(magnet_link)
                                        print("Magnet link successfully copied to clipboard.")
                                        input("\nPress Enter to terminate the script...")
                                        break
                                    if copy_input == 'N':
                                        input("Press Enter to terminate the script...")
                                        break
                                    else:
                                        print("Invalid input. Please enter 'Y' for yes or 'N' for no.")
                        else:
                            print("Could not generate a URL for this anime.")
                    else:
                        print("Could not retrieve the anime's status.")
                    break
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid selection. Please enter a number.")
    else:
        print("No results found")

if __name__ == "__main__":
    main()
