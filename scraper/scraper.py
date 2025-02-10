import requests
from bs4 import BeautifulSoup
import re
import mysql.connector
from datetime import datetime
from database import get_db_connection
from config import BASE_URL


# Function to fetch episode details
def fetch_episode_details(episode_url):
    response = requests.get(episode_url)
    soup = BeautifulSoup(response.content, "html.parser")

    presenters, location, date_object = [], None, None

    date_label = soup.find("h3", string="First Broadcast")
    if date_label:
        date_div = date_label.find_next_sibling("div", class_="pi-data-value")
        if date_div:
            date = date_div.get_text(strip=True)
            try:
                date_object = datetime.strptime(date, "%d %B %Y").strftime("%Y-%m-%d")
            except ValueError:
                date_object = datetime.strptime(date, "%d %b %Y").strftime("%Y-%m-%d")

    presenters_label = soup.find("h3", string="Presenters")
    if presenters_label:
        presenters_div = presenters_label.find_next_sibling("div", class_="pi-data-value")
        if presenters_div:
            presenters = [a.get_text(strip=True) for a in presenters_div.find_all("a")]

    location_label = soup.find("h3", string="Location")
    if location_label:
        location_div = location_label.find_next_sibling("div", class_="pi-data-value")
        if location_div:
            location = location_div.get_text(strip=True)

    return {"presenters": presenters, "location": location, "date": date_object}


# Extract episode number and title from URL
def extract_episode_info(url):
    match = re.search(r"Episode_(\d+):_(.+)", url)
    if match:
        return int(match.group(1)), match.group(2).replace("_", " ")
    return None, None


# Get existing episode numbers from the database
def get_existing_episodes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM fish_episodes")
    existing_episodes = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return existing_episodes


# Insert new episodes into the database
def insert_episode(episode):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO fish_episodes (number, title, presenters, location, is_live, date)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    is_live = "office" in (episode["location"] or "").lower()
    cursor.execute(
        query,
        (
            episode["number"],
            episode["title"],
            ", ".join(episode["presenters"]),
            episode["location"],
            is_live,
            episode["date"],
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()


# Main function to scrape episodes
def scrape_episodes():
    main_url = f"{BASE_URL}/wiki/List_of_Episodes_of_No_Such_Thing_As_A_Fish"
    response = requests.get(main_url)
    soup = BeautifulSoup(response.content, "html.parser")

    episode_links = soup.find_all("a", href=True, title=True)
    existing_episodes = get_existing_episodes()
    new_episodes = []

    for link in episode_links:
        if link["href"].startswith("/wiki/Episode_"):
            ep_number, ep_title = extract_episode_info(link["href"])
            if ep_number is None or ep_number in existing_episodes:
                print(f"Skipping Episode {ep_number} (already in database)")
                continue

            episode_url = BASE_URL + link["href"]
            details = fetch_episode_details(episode_url)

            episode_data = {"number": ep_number, "title": ep_title, **details}
            insert_episode(episode_data)
            new_episodes.append(episode_data)
            print(f"Added Episode {ep_number}: {ep_title}, {details}")

    print(f"Scraping completed. {len(new_episodes)} new episodes added.")


if __name__ == "__main__":
    scrape_episodes()
