"""
scrape_badges.py

This script scrapes Google Cloud Skills Boost profiles to extract badge earned dates.
It reads profile URLs from progress.csv and creates a CSV with badge names as columns
and earned dates as values.

Usage:
- Place your progress.csv in the same directory.
- Run this script. Results are saved to 'badge_dates.csv'.
"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from datetime import datetime

# Badge list to track
BADGE_LIST = [
    "The Basics of Google Cloud Compute",
    "Get Started with Cloud Storage",
    "Get Started with Pub/Sub",
    "Get Started with API Gateway",
    "Get Started with Looker",
    "Get Started with Dataplex",
    "Get Started with Google Workspace Tools",
    "App Building with AppSheet",
    "Develop with Apps Script and AppSheet",
    "Develop Gen AI Apps with Gemini and Streamlit",
    "Build a Website on Google Cloud",
    "Set Up a Google Cloud Network",
    "Store, Process, and Manage Data on Google Cloud - Console",
    "Cloud Run Functions: 3 Ways",
    "App Engine: 3 Ways",
    "Cloud Speech API: 3 Ways",
    "Analyze Speech and Language with Google APIs",
    "Monitoring in Google Cloud",
    "Prompt Design in Vertex AI",
    "Level 3: Generative AI"
]


def clean_columns(df):
    """Clean and standardize column names"""
    df.columns = [c.encode('utf-8').decode('utf-8').strip().replace('\ufeff', '').replace('\xa0', '').replace('\u200b', '') for c in df.columns]
    df.columns = [c.strip() for c in df.columns]
    return df


def parse_earned_date(date_text):
    """
    Convert earned date to YYYY-MM-DD format
    Input examples: "Oct  8, 2025 EDT", "Jan 15, 2025 PST"
    Output: "2025-10-08", "2025-01-15"
    """
    try:
        # Remove timezone abbreviations (EDT, PST, etc.)
        date_text = date_text.replace("EDT", "").replace("EST", "").replace("PDT", "").replace("PST", "").strip()
        # Parse the date
        parsed_date = datetime.strptime(date_text, "%b %d, %Y")
        # Return in YYYY-MM-DD format
        return parsed_date.strftime("%Y-%m-%d")
    except Exception:
        # If parsing fails, return original text
        return date_text


def scrape_badge_dates(url, max_retries=3):
    """
    Scrape badge earned dates from Google Cloud Skills Boost profile
    Returns a dictionary with badge names as keys and earned dates as values
    """
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            badge_dates = {}

            # Find all badge elements
            badge_elements = soup.find_all("div", class_="profile-badge")

            for badge_elem in badge_elements:
                # Get badge name - it's in a <span class="ql-title-medium">
                badge_name_elem = badge_elem.find("span", class_="ql-title-medium")

                if badge_name_elem:
                    badge_name = badge_name_elem.text.strip()

                    # Check if this badge is in our list
                    if badge_name in BADGE_LIST:
                        # Get earned date - it's in a <span class="ql-body-medium">
                        date_elem = badge_elem.find("span", class_="ql-body-medium")

                        if date_elem:
                            date_text = date_elem.text.strip()
                            # Extract just the date part (e.g., "Earned Oct  8, 2025 EDT" -> "Oct  8, 2025 EDT")
                            if "Earned" in date_text:
                                earned_date = date_text.replace("Earned", "").strip()
                            else:
                                earned_date = date_text
                            # Convert to YYYY-MM-DD format
                            earned_date = parse_earned_date(earned_date)
                            badge_dates[badge_name] = earned_date
                        else:
                            badge_dates[badge_name] = "Date not found"

            return badge_dates, 'success'

        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return {}, f'error: {str(e)}'


def main():
    # Load progress.csv
    print("Loading progress.csv...")
    progress = pd.read_csv('progress.csv')
    progress = clean_columns(progress)

    print(f"Loaded {len(progress)} records from progress.csv")

    # Initialize result dataframe
    result_data = []

    # Process each profile URL
    for index, row in progress.iterrows():
        url = row.get('Google Cloud Skills Boost Profile URL')

        if pd.isna(url) or not str(url).strip():
            print(f"Skipping row {index + 1}: No profile URL")
            # Add empty row with user info
            row_data = {
                'User Name': row.get('User Name', ''),
                'User Email': row.get('User Email', ''),
                'Google Cloud Skills Boost Profile URL': ''
            }
            # Initialize all badge columns as empty
            for badge in BADGE_LIST:
                row_data[badge] = ''
            row_data['Total Badges'] = 0
            result_data.append(row_data)
            continue

        print(f"Processing {index + 1}/{len(progress)}: {row.get('User Name', 'Unknown')}")

        # Scrape badge dates
        badge_dates, status = scrape_badge_dates(url)

        # Build row data
        row_data = {
            'User Name': row.get('User Name', ''),
            'User Email': row.get('User Email', ''),
            'Google Cloud Skills Boost Profile URL': url
        }

        # Add badge dates (empty if not found)
        for badge in BADGE_LIST:
            row_data[badge] = badge_dates.get(badge, '')

        # Count total badges earned from our list
        total_badges = sum(1 for badge in BADGE_LIST if badge_dates.get(badge, '') != '')
        row_data['Total Badges'] = total_badges

        result_data.append(row_data)

        # Be respectful with requests
        time.sleep(1)

    # Create result dataframe
    result_df = pd.DataFrame(result_data)

    # Save to CSV
    output_file = 'badge_dates.csv'
    result_df.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to {output_file}")

    # Print summary
    print("\n" + "="*80)
    print("BADGE SCRAPING SUMMARY")
    print("="*80)
    print(f"Total profiles processed: {len(result_df)}")

    # Count how many users earned each badge
    print("\nBadge Earned Counts:")
    for badge in BADGE_LIST:
        count = (result_df[badge] != '').sum()
        print(f"  {badge}: {count} users")


if __name__ == "__main__":
    main()
