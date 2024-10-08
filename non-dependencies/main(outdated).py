from imdb import Cinemagoer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import sys
import time

# IMDb search functions
def get_movie_id():
    ia = Cinemagoer()

    while True:
        keywords = input("Enter title + year (e.g Inception 2010 or Stranger Things 2016): ")
        search_results = ia.search_movie(keywords)
    
        if search_results:
            movie = search_results[0]
            return movie.getID()
        else:
            print(f"Error. Unable to find '{keywords}'. Make sure both the title and year are correct.")

def get_tv_id():
    ia = Cinemagoer()

    while True:
        keywords = input("Enter title + year (e.g Inception 2010 or Stranger Things 2016): ")
        search_results = ia.search_movie(keywords)  # Note: This also works for TV series
    
        if search_results:
            for result in search_results:
                if result.get('kind') in ['tv series', 'tv miniseries']:
                    return result.getID()
        else:
            print(f"Error. Unable to find '{keywords}'. Make sure both the title and year are correct.")

def get_url(media_type, imdb_id):
    base_movie_url = "https://debridmediamanager.com/movie/tt"
    base_tv_url = "https://debridmediamanager.com/show/tt"
    
    if media_type == 'M':
        return f"{base_movie_url}{imdb_id}"
    else:
        return f"{base_tv_url}{imdb_id}"

# Web automation for scraping and interacting with search results
def automate_webpage(url, search_text, media__type):
    # Set up WebDriver (assuming Chrome)
    # Path to ChromeDriver
    chrome_driver_path = "C:/Users/user/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"

    # Path to your Chrome user profile
    chrome_profile_path = "C:/Users/user/AppData/Local/Google/Chrome/User Data"

    # Set Chrome options to use the existing profile
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={chrome_profile_path}")  # Path to user data directory
    chrome_options.add_argument("profile-directory=Default")  # Specify profile directory (e.g., 'Profile 1' if you use a custom profile)

    # Create a service object and start ChromeDriver using the profile
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Minimize window
        driver.minimize_window()

        # Open the URL
        driver.get(url)

        # Wait for the page to load
        time.sleep(5)

        # Locate the search filter (update the class/ID as per the actual webpage)
        search_filter = driver.find_element(By.CSS_SELECTOR, "#query")

        # Click on the filter and enter the search text
        search_filter.click()
        search_filter.send_keys(search_text)
        search_filter.send_keys(Keys.RETURN)

        # Wait for the results to filter (120 seconds)
        time.sleep(120)

        # Scrape all file names (Generalized selector)
        file_name_elements = driver.find_elements(By.CSS_SELECTOR, "#__next > div > div.mx-2.my-1.overflow-x-auto.grid.grid-cols-1.sm\\:grid-cols-2.md\\:grid-cols-3.lg\\:grid-cols-4.xl\\:grid-cols-6.gap-4 > div > div > h2")

        # Check if there are any files found
        if not file_name_elements:
            print("No matching files found. The script will now terminate...")
            sys.exit(1)

        # Get the text from each file name element
        print("\nMatching files found:")
        file_names = [element.text for element in file_name_elements]

        # Print file names to the terminal for the user to select
        for idx, file_name in enumerate(file_names, start=1):
            print(f"{idx}. {file_name}")

        # Get user to input a number to choose the corresponding file
        selected_num = int(input("Type in the NUMBER corresponding to the file you want: "))
        selected_file_element = file_name_elements[selected_num - 1]

        print(f"Getting file, please wait...")

        # Now locate the corresponding button for the selected file (within the same section)
        # We can navigate to the button using the parent div structure
        button = selected_file_element.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'space-x-2')]/button")

        # Click the button corresponding to the selected file
        button.click()

        time.sleep(10)

        print(f"File '{file_names[selected_num - 1]}' added to library successfully. Click on the file then click on 'DL' to send to Real-Debrid to download or stream it. Now opening DMM Library...")

        time.sleep(5)

        # Show browser window
        driver.maximize_window()

        # Go to DMM library
        library_url = 'https://debridmediamanager.com/library'
        driver.get(library_url)

        input("\nPress Enter to terminate the script and browser window...")

    except Exception as e:
        print(f"Error occurred: {e}")

def main():
    input("Reminder: Make sure you are logged into Real-Debrid (real-debrid.com) and Debrid Media Manager (debridmediamanager.com).\nPress Enter to continue...\n")

    while True:
        media_type = input("Movie or TV? [M/T]: ").strip().upper()
        
        if media_type in ['M', 'T']:
            break  # Exit the loop if the input is valid
        else:
            print("Invalid input. Please enter 'M' for movie or 'T' for TV.")
    
    if media_type == 'M':
        imdb_id = get_movie_id()

        while True:
            query = input("Is it a recently released (within this month) movie? [Y/N]: ").strip().upper()
            if query == 'Y':
                search_text = "web-dl ^(?!.*(?:hdr|dv|dovi)).*(?:2160p).*$"
                break  # Exit the loop on valid input
            elif query == 'N':
                search_text = "remux ^(?!.*(?:hdr|dv|dovi)).*(?:1080p).*$"
                break  # Exit the loop on valid input
            else:
                print("Invalid input. Please enter 'Y' for yes or 'N' for no.")

    else:
        imdb_id = get_tv_id()
        search_text = "web-dl ^(?!.*(?:hdr|dv|dovi)).*(?:1080p|2160p).*$"
    
    print(f"Wait for around 2 minutes...")

    time.sleep(3)

    if imdb_id:
        url = get_url(media_type, imdb_id)

        # Automate the web page interaction
        automate_webpage(url, search_text, media_type)
    else:
        print(f"\nNo active URL found.")

if __name__ == "__main__":
    main()