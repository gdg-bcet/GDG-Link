"""
analyze_full.py

This script analyzes Google Cloud Skills Boost registration data for GDG events.
It processes a CSV file of participant information, checks each participant's Skills Boost public profile,
and applies qualification logic based on email/domain, account creation year, badge/league status, and duplicates.

Features:
- Detects and groups duplicate entries by phone number.
- Checks for incomplete registrations and declined terms.
- Scrapes Skills Boost profiles for creation year, badges, league, and points.
- Applies multi-level qualification logic (hard qualified, tier 2, flagged, disqualified, etc.).
- Handles edge cases (missing data, declined terms, no profile URL).
- Outputs a cleaned CSV and prints a detailed summary with counts for each qualification status.
- Designed for further analysis and conditional formatting in Excel/Google Sheets.

Usage:
- Place your registration data in 'data.csv' in the same directory.
- Run this script. Results are saved to 'full_analysis_results.csv' and a summary is printed to the console.
"""

from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time


def check_profile(url, max_retries=3):
    """
    Check Google Cloud Skills Boost profile with retry logic
    """
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            data = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(data.text, "html.parser")

            # Check account creation date
            acc_creation_element = soup.find("p", class_="ql-body-large l-mbl")
            creation_year = None
            creation_text = None

            if acc_creation_element:
                creation_text = acc_creation_element.text.strip()
                year_match = re.search(r'Member since (\d{4})', creation_text)
                if year_match:
                    creation_year = int(year_match.group(1))

            # Check for badges
            badge_elements = soup.find_all("div", class_="profile-badge")
            badge_count = len(badge_elements) if badge_elements else 0

            # Check for league membership and points
            league_element = soup.find("div", class_="profile-league")
            league_name = None
            points = None

            if league_element:
                league_name_element = league_element.find("h2", class_="ql-headline-medium")
                points_element = league_element.find("strong")

                if league_name_element:
                    league_name = league_name_element.text.strip()
                if points_element:
                    points_text = points_element.text.strip()
                    points_match = re.search(r'(\d+)', points_text)
                    if points_match:
                        points = int(points_match.group(1))

            return {
                'creation_date': creation_text,
                'creation_year': creation_year,
                'badge_count': badge_count,
                'league': league_name,
                'points': points,
                'status': 'success'
            }

        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return {
                    'creation_date': None,
                    'creation_year': None,
                    'badge_count': None,
                    'league': None,
                    'points': None,
                    'status': f'error: {str(e)}'
                }


def determine_qualification(row):
    """
    Determine qualification status based on criteria
    """
    # Check for incomplete registration (missing required fields)
    if (pd.isna(row['Name']) or pd.isna(row['Email Address']) or
            pd.isna(row['Skills Boost Email']) or pd.isna(row['Phone Number'])):
        return 'INCOMPLETE_REGISTRATION', 'Missing required fields (Name, Email, or Phone)'

    # Check if terms were declined or required fields are empty
    if 'Terms' in row and row['Terms'] != "Yes, I accept the terms":
        return 'TERMS_DECLINED', 'Terms and conditions not accepted'

    # Check if Skills Boost profile URL is missing
    if pd.isna(row['Skills Boost Public Profile URL']) or row['Skills Boost Public Profile URL'].strip() == '':
        return 'NO_PROFILE_URL', 'Skills Boost profile URL missing'

    email_matches = row['email_matches']
    email_has_gdg = row['email_has_gdg_domain']
    skillsboost_has_gdg = row['skillsboost_has_gdg_domain']
    creation_year = row['profile_creation_year']
    badge_count = row['profile_badge_count']
    league = row['profile_league']
    points = row['profile_points']
    is_duplicate = row['is_duplicate']
    duplicate_position = row['duplicate_position']

    # Mark duplicates (keep first entry as primary)
    if is_duplicate and duplicate_position > 1:
        return 'DUPLICATE_ENTRY', f'Duplicate entry #{duplicate_position} for same phone number'

    # Hard qualified: GDG domain + 2025 creation + no badges + no points + no league
    if (email_has_gdg and
            creation_year == 2025 and
            (badge_count == 0 or pd.isna(badge_count)) and
            (points == 0 or pd.isna(points)) and
            (pd.isna(league) or league == "")):
        return 'HARD_QUALIFIED', 'GDG domain + 2025 creation + empty profile'

    # Tier 2: matching emails + 2025 creation + no badges + no league + no points
    if (email_matches and
            creation_year == 2025 and
            (badge_count == 0 or pd.isna(badge_count)) and
            (pd.isna(league) or league == "") and
            (points == 0 or pd.isna(points))):
        return 'QUALIFIED_TIER2', 'Matching emails + 2025 creation + empty profile'

    # Flag different accounts but check URL clause
    if not email_matches and skillsboost_has_gdg:
        return 'FLAGGED_DIFF_ACCOUNT', 'Different email but Skills Boost has GDG domain'

    # Disqualify those with badges
    if badge_count and badge_count > 0:
        return 'DISQUALIFIED', f'Has {badge_count} badges'

    # Caution for pre-2025 accounts with empty profiles
    if (creation_year and creation_year < 2025 and
            (badge_count == 0 or pd.isna(badge_count)) and
            (pd.isna(league) or league == "") and
            (points == 0 or pd.isna(points))):
        return 'CAUTION_PRE2025', f'Created in {creation_year} but empty profile'

    # Default cases
    if creation_year == 2025:
        return 'REVIEW_NEEDED', f'2025 account with {badge_count or 0} badges, {points or 0} points'
    elif creation_year and creation_year < 2025:
        return 'REVIEW_PRE2025', f'Pre-2025 account ({creation_year}) needs review'
    else:
        return 'UNKNOWN', 'Could not determine profile details'


def main():
    # Load CSV data
    df = pd.read_csv('data.csv')
    print(f"Loaded {len(df)} records from CSV")

    # Detect and mark duplicates by phone number
    df['is_duplicate'] = df.duplicated(subset=['Phone Number'], keep=False)
    df['duplicate_group'] = df.groupby('Phone Number').ngroup()
    df['duplicate_position'] = df.groupby('Phone Number').cumcount() + 1

    # Sort by duplicate group and position to keep duplicates together
    df = df.sort_values(['duplicate_group', 'duplicate_position']).reset_index(drop=True)

    # Count duplicates
    duplicate_count = df['is_duplicate'].sum()
    duplicate_groups = len(df[df['is_duplicate']]['Phone Number'].unique())
    print(f"Found {duplicate_count} duplicate entries across {duplicate_groups} phone numbers")

    # Add email analysis columns
    df['email_matches'] = df['Email Address'] == df['Skills Boost Email']
    df['email_has_gdg_domain'] = df['Email Address'].str.contains('.gdgocbcet@gmail.com', na=False)
    df['skillsboost_has_gdg_domain'] = df['Skills Boost Email'].str.contains('.gdgocbcet@gmail.com', na=False)

    # Initialize profile analysis columns
    df['profile_creation_year'] = None
    df['profile_badge_count'] = None
    df['profile_league'] = None
    df['profile_points'] = None
    df['profile_status'] = None
    df['qualification_status'] = None
    df['qualification_reason'] = None

    # Process each profile
    for index, row in df.iterrows():
        print(f"Processing {index + 1}/{len(df)}: {row['Name']}")

        # First check for incomplete registration or declined terms
        status, reason = determine_qualification(df.iloc[index])

        # If registration is incomplete or terms declined, skip profile checking
        if status in ['INCOMPLETE_REGISTRATION', 'TERMS_DECLINED', 'NO_PROFILE_URL']:
            df.at[index, 'qualification_status'] = status
            df.at[index, 'qualification_reason'] = reason
            df.at[index, 'profile_status'] = 'skipped'
            continue

        # If it's a duplicate, mark it but still check profile
        if status == 'DUPLICATE_ENTRY':
            df.at[index, 'qualification_status'] = status
            df.at[index, 'qualification_reason'] = reason
            # Continue to check profile for duplicates too

        # Check profile only if URL is available
        if pd.notna(row['Skills Boost Public Profile URL']) and row['Skills Boost Public Profile URL'].strip() != '':
            profile_data = check_profile(row['Skills Boost Public Profile URL'])

            # Update profile data
            df.at[index, 'profile_creation_year'] = profile_data['creation_year']
            df.at[index, 'profile_badge_count'] = profile_data['badge_count']
            df.at[index, 'profile_league'] = profile_data['league']
            df.at[index, 'profile_points'] = profile_data['points']
            df.at[index, 'profile_status'] = profile_data['status']

            # Re-determine qualification with profile data (unless already marked as duplicate)
            if status != 'DUPLICATE_ENTRY':
                status, reason = determine_qualification(df.iloc[index])
                df.at[index, 'qualification_status'] = status
                df.at[index, 'qualification_reason'] = reason

        # Add delay to be respectful
        time.sleep(1)

    # Clean up unnecessary columns before saving
    columns_to_remove = ['Terms', 'Internet', 'Verify', 'Completing', 'Signup']
    df_clean = df.drop(columns=columns_to_remove, errors='ignore')

    # Save results
    df_clean.to_csv('full_analysis_results.csv', index=False)

    # Generate summary
    print("\n" + "="*80)
    print("FINAL ANALYSIS SUMMARY")
    print("="*80)

    # Overall counts
    total_entries = len(df)
    unique_phones = df['Phone Number'].nunique()
    duplicate_entries = len(df[df['is_duplicate'] & (df['duplicate_position'] > 1)])

    print("OVERALL STATISTICS:")
    print(f"  Total Entries: {total_entries}")
    print(f"  Unique Phone Numbers: {unique_phones}")
    print(f"  Duplicate Entries: {duplicate_entries}")
    print(f"  Valid Unique Entries: {unique_phones}")

    # Qualification status breakdown
    status_counts = df['qualification_status'].value_counts()
    print("\nQUALIFICATION STATUS BREAKDOWN:")
    for status, count in status_counts.items():
        percentage = (count / total_entries) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")

    # Valid entries (excluding incomplete, declined terms, duplicates)
    invalid_statuses = ['INCOMPLETE_REGISTRATION', 'TERMS_DECLINED', 'NO_PROFILE_URL', 'DUPLICATE_ENTRY']
    valid_entries = df[~df['qualification_status'].isin(invalid_statuses)]
    valid_count = len(valid_entries)

    print("\nVALID ENTRIES ANALYSIS:")
    print(f"  Total Valid Entries: {valid_count} out of {total_entries} "
          f"({(valid_count/total_entries)*100:.1f}%)")

    if valid_count > 0:
        valid_status_counts = valid_entries['qualification_status'].value_counts()
        print("  Valid Entries Breakdown:")
        for status, count in valid_status_counts.items():
            percentage = (count / valid_count) * 100
            print(f"    {status}: {count} ({percentage:.1f}%)")

    # Qualified candidates (Hard + Tier2)
    qualified_statuses = ['HARD_QUALIFIED', 'QUALIFIED_TIER2']
    qualified_entries = df[df['qualification_status'].isin(qualified_statuses)]
    qualified_count = len(qualified_entries)

    print("\nQUALIFIED CANDIDATES:")
    qualified_percentage = (qualified_count/valid_count)*100 if valid_count > 0 else 0
    print(f"  Total Qualified: {qualified_count} out of {valid_count} valid entries "
          f"({qualified_percentage:.1f}%)")

    # Action required entries
    action_required_statuses = ['FLAGGED_DIFF_ACCOUNT', 'REVIEW_NEEDED', 'CAUTION_PRE2025', 'REVIEW_PRE2025']
    action_required_entries = df[df['qualification_status'].isin(action_required_statuses)]
    action_required_count = len(action_required_entries)

    print("\nACTION REQUIRED:")
    action_percentage = (action_required_count/valid_count)*100 if valid_count > 0 else 0
    print(f"  Entries Needing Review: {action_required_count} out of {valid_count} "
          f"valid entries ({action_percentage:.1f}%)")

    # Show duplicate entries
    duplicates = df[df['is_duplicate']]
    if len(duplicates) > 0:
        print(f"\nDUPLICATE ENTRIES ({len(duplicates)}):")
        for phone in duplicates['Phone Number'].unique():
            duplicate_group = duplicates[duplicates['Phone Number'] == phone]
            print(f"\n  Phone: {phone}")
            for _, row in duplicate_group.iterrows():
                status_indicator = "🔴" if row['duplicate_position'] > 1 else "🔵"
                print(f"    {status_indicator} {row['Name']} - {row['Email Address']} ({row['qualification_status']})")

    # Show key groups
    hard_qualified = df[df['qualification_status'] == 'HARD_QUALIFIED']
    print(f"\nHARD QUALIFIED ({len(hard_qualified)}):")
    for _, row in hard_qualified.iterrows():
        print(f"  - {row['Name']} ({row['Email Address']})")

    tier2_qualified = df[df['qualification_status'] == 'QUALIFIED_TIER2']
    print(f"\nTIER 2 QUALIFIED ({len(tier2_qualified)}):")
    for _, row in tier2_qualified.iterrows():
        print(f"  - {row['Name']} ({row['Email Address']})")

    flagged = df[df['qualification_status'] == 'FLAGGED_DIFF_ACCOUNT']
    print(f"\nFLAGGED DIFFERENT ACCOUNTS ({len(flagged)}):")
    for _, row in flagged.iterrows():
        print(f"  - {row['Name']} (Email: {row['Email Address']}, Skills Boost: {row['Skills Boost Email']})")

    disqualified = df[df['qualification_status'] == 'DISQUALIFIED']
    print(f"\nDISQUALIFIED ({len(disqualified)}):")
    for _, row in disqualified.iterrows():
        print(f"  - {row['Name']} - {row['qualification_reason']}")


if __name__ == "__main__":
    main()
