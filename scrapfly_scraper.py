import json
import re
import os
import time
from playwright.sync_api import sync_playwright

# def clean_tweet_text(text: str) -> str:
#     text = re.sub(r"@\w+", "", text)
#     text = re.sub(r"·\s*\w{3}\s*\d{1,2}", "", text)
#     text = re.sub(r"\d+[KM]?$", "", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     text = re.sub(r"The media could not be played\.?", "", text, flags=re.IGNORECASE)
#     text = re.sub(r"Reload", "", text, flags=re.IGNORECASE)
#     text = re.sub(r"Show more", "", text, flags=re.IGNORECASE)
#     return text.strip()

def scrape_single_tweet(tweet_url: str, cookie_file="x_cookies.json", profile_path="user_data"):
    try:
        with sync_playwright() as pw:
            context = pw.chromium.launch_persistent_context(profile_path, headless=False)
            page = context.new_page()

            # Set User-Agent to avoid bot detection
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            })

            # Open Tweet URL with increased timeout
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

            # Extract text
            tweet_text = tweet_element.text_content().strip()
            # cleaned_text = clean_tweet_text(tweet_text)

            # Extract tweet ID
            tweet_id = tweet_url.split("/")[-1]

            # Save cookies
            cookies = context.cookies()
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            context.close()

            tweet_data = {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "tweet_link": tweet_url,
            }

            print(f"Successfully extracted tweet: {tweet_data}")
            return tweet_data

    except Exception as e:
        print(f"Error scraping tweet: {e}")
        return None

def save_to_file(data, filename="single_tweet_data.json"):
    try:
        print(f"Attempting to save tweet: {json.dumps(data, indent=2)}")  # Debugging

        # Ensure file exists, if not, create it
        if not os.path.exists(filename):
            print("File does not exist. Creating a new JSON file.")
            with open(filename, "w", encoding="utf-8") as file:
                json.dump([], file)  # Initialize with an empty list

        # Read existing data
        with open(filename, "r", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    print("Existing data is not a list. Resetting file.")
                    existing_data = []
            except json.JSONDecodeError:
                print("JSON Decode Error. Resetting file.")
                existing_data = []

        # Avoid duplicates
        unique_tweet_ids = {tweet["tweet_id"] for tweet in existing_data if "tweet_id" in tweet}

        if data["tweet_id"] not in unique_tweet_ids:
            existing_data.append(data)

            # Write data to file
            print(f"Writing to {filename}...")
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(existing_data, file, ensure_ascii=False, indent=2)

            print(f"Tweet successfully saved to {filename}")
        else:
            print("Tweet already exists in file. Skipping save.")

        # Print file content for verification
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
            print("Final File Content:")
            print(content if content else "(Empty File)")

    except Exception as e:
        print(f"Error saving to file {filename}: {e}")


if __name__ == "__main__":
    tweet_url = input("Enter Tweet URL: ")
    tweet_data = scrape_single_tweet(tweet_url)

    if tweet_data:
        save_to_file(tweet_data)

        print("\nExtracted Tweet Data:")
        print(json.dumps(tweet_data, indent=2))
    else:
        print("No tweet data extracted.")

