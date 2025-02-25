import json
import re
import os
import time
from playwright.sync_api import sync_playwright

#1.remove this if you want the pure raw tweet
def clean_tweet_text(text: str) -> str:
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"·\s*\w{3}\s*\d{1,2}", "", text)
    text = re.sub(r"\d+[KM]?$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"The media could not be played\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Reload", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Show more", "", text, flags=re.IGNORECASE)
    return text.strip()

def login_x_and_save_cookies(username, password, cookie_file="x_cookies.json", profile_path="user_data"):
    """Logs into X (formerly Twitter), saves cookies for future use."""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch_persistent_context(profile_path, headless=False)
            page = browser.new_page()

            # Open login page
            print("Opening login page...")
            page.goto("https://x.com/login", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            # Enter username
            page.fill("input[name='text']", username)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)
            
            # Enter password
            page.fill("input[name='password']", password)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            # Verify successful login
            if "Home / X" in page.title():
                print("Login successful!")
                cookies = browser.cookies()
                with open(cookie_file, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print("Cookies saved for future use.")
            else:
                print("Login failed. Please check credentials.")
            
            browser.close()
    except Exception as e:
        print(f"Error logging in: {e}")

def scrape_single_tweet(tweet_url: str, cookie_file="x_cookies.json", profile_path="user_data"):
    """Scrapes a single tweet using stored cookies."""
    try:
        with sync_playwright() as pw:
            context = pw.chromium.launch_persistent_context(profile_path, headless=False)
            page = context.new_page()

            # Load cookies if they exist
            if os.path.exists(cookie_file):
                with open(cookie_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
                print("Loaded stored cookies.")

            # Open Tweet URL
            print(f"Opening tweet URL: {tweet_url}")
            page.goto(tweet_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            # Scroll slightly to trigger JavaScript elements
            page.mouse.wheel(0, 300)
            page.wait_for_timeout(2000)

            # Locate tweet
            tweet_element = page.locator("[role='article']").first
            if not tweet_element:
                print("Tweet not found.")
                return None

            # Extract text (RAW, NO CLEANING)
            tweet_text = tweet_element.text_content().strip()
            cleaned_text = clean_tweet_text(tweet_text) #2.REMOVE THIS PART FOR RAW TWEETS ONLY!!

            # Extract tweet ID
            tweet_id = tweet_url.split("/")[-1]

            # Save updated cookies
            cookies = context.cookies()
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            context.close()

            tweet_data = {
                "tweet_id": tweet_id,
                "tweet_text": cleaned_text, #3.CHANGE THIS TO "tweet_text": tweet_text,
                "tweet_link": tweet_url
            }

            print(f"Successfully extracted tweet: {tweet_data}")
            return tweet_data

    except Exception as e:
        print(f"Error scraping tweet: {e}")
        return None

def save_to_file(data, filename="single_tweet_data.json"):
    """Saves tweet data to a JSON file while avoiding duplicates."""
    try:
        if os.path.exists(filename) and os.stat(filename).st_size > 0:
            with open(filename, "r", encoding="utf-8") as file:
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        raise ValueError("Existing data is not a list")
                except (json.JSONDecodeError, ValueError):
                    existing_data = []
        else:
            existing_data = []

        unique_tweet_ids = {tweet["tweet_id"] for tweet in existing_data if "tweet_id" in tweet}
        if data["tweet_id"] not in unique_tweet_ids:
            existing_data.append(data)
            print(f"Added new tweet to {filename}")
        else:
            print("Tweet already exists in file. Skipping save.")

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=2)
        print(f"Successfully updated {filename}")

    except Exception as e:
        print(f"Error saving to file {filename}: {e}")

if __name__ == "__main__":
    choice = input("Do you want to login first? (yes/no): ").strip().lower()
    if choice == "yes":
        username = input("Enter your X username: ")
        password = input("Enter your X password: ")
        login_x_and_save_cookies(username, password)

    tweet_url = input("Enter Tweet URL: ")
    tweet_data = scrape_single_tweet(tweet_url)

    if tweet_data:
        save_to_file(tweet_data)

        print("\nExtracted Tweet Data:")
        print(json.dumps(tweet_data, indent=2))
    else:
        print("No tweet data extracted.")