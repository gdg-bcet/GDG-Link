# Utils - Utility Scripts

This folder contains utility scripts for database management, data import, API services, and badge scraping for the GDG-Link bot system.

## 📁 Contents

### 1. `analyze_full.py`

**📊 GDG Event Registration Analyzer & Qualifier**

A comprehensive analysis tool for processing Google Cloud Skills Boost registration data for GDG events. It validates participants, checks profiles, applies multi-tier qualification logic, and generates detailed reports.

**Features:**

- � Detects and groups duplicate entries by phone number
- ✅ Checks for incomplete registrations and declined terms
- 🕷️ Scrapes Skills Boost profiles for account details
- 🎯 Multi-level qualification logic (Hard Qualified, Tier 2, Flagged, Disqualified)
- � Handles edge cases (missing data, declined terms, no profile URL)
- 📈 Detailed summary with counts for each qualification status
- � Outputs cleaned CSV for further analysis in Excel/Google Sheets
- 🏅 Validates badge count, league status, and account creation year

**Qualification Tiers:**

1. **HARD_QUALIFIED** - GDG domain + 2025 creation + empty profile (no badges/points/league)
2. **QUALIFIED_TIER2** - Matching emails + 2025 creation + empty profile
3. **FLAGGED_DIFF_ACCOUNT** - Different email but Skills Boost has GDG domain
4. **DISQUALIFIED** - Has badges (existing account activity)
5. **CAUTION_PRE2025** - Created before 2025 but empty profile (needs review)
6. **REVIEW_NEEDED** - 2025 account with some activity (needs review)
7. **DUPLICATE_ENTRY** - Duplicate phone number (keeps first entry as primary)
8. **INCOMPLETE_REGISTRATION** - Missing required fields
9. **TERMS_DECLINED** - Terms and conditions not accepted
10. **NO_PROFILE_URL** - Skills Boost profile URL missing

**Input CSV Format:**

```csv
Name,Email Address,Skills Boost Email,Phone Number,Skills Boost Public Profile URL,Terms
John Doe,john.gdgocbcet@gmail.com,john.gdgocbcet@gmail.com,1234567890,https://...,Yes, I accept the terms
```

**Output:** `full_analysis_results.csv` with:

- All original fields
- Email matching analysis
- Profile scraping results (creation year, badges, league, points)
- Qualification status and reason
- Duplicate detection markers

**Usage:**

```bash
# Place registration data in data.csv
python analyze_full.py
# Output: full_analysis_results.csv
```

**Analysis Includes:**

- Profile creation year detection
- Badge count verification
- League membership check
- Points/activity analysis
- Email domain validation
- Duplicate detection and grouping

---

### 2. `import_users_csv.py`

**📥 CSV User Import with Auto-Generated Profile Colors**

Imports users from a CSV file into the database with automatically assigned random profile colors from a curated color palette.

**Features:**

- 🎨 Auto-assigns visually appealing profile colors (50+ colors)
- ✅ Skip or update existing users
- 🔍 Preview CSV data before import
- 📊 Detailed import summary and statistics
- ✨ Pre-verified user support (with Discord ID)

**CSV Format:**

```csv
User Name,Google Cloud Skills Boost Profile URL,Discord ID
John Doe,https://www.cloudskillsboost.google/public_profiles/...,549415697726439434
Jane Smith,https://www.cloudskillsboost.google/public_profiles/...,
```

**Color Palette:**

- Blues, Purples, Pinks, Reds, Oranges
- Yellows, Greens, Teals, Cyans, Indigos
- Grays (for variety)
- All colors are optimized for white text (WCAG AA compliant)

**Usage:**

```bash
python import_users_csv.py
```

**Interactive Menu:**

1. Preview CSV data (first 10 rows)
2. Import users (skip existing)
3. Import users (update existing)
4. Exit

**Functions:**

- `import_users_from_csv(csv_file, skip_existing)` - Import users from CSV
- `show_import_preview(csv_file, limit)` - Preview CSV before import
- `generate_random_color()` - Generate random color from palette

---

### 3. `cleanup_database.py`

**🧹 Database Cleanup and Management Utility**

Provides comprehensive database cleanup and maintenance operations for the badge tracking system.

**Features:**

- 🗑️ Complete database cleanup (users + badges)
- 🏆 Badge-only cleanup
- 👤 Per-user badge cleanup
- 🔓 Unverify users (remove Discord ID)
- ✏️ Update user information
- 📊 Current database statistics
- ✅ Cleanup verification

**Operations:**

1. **Clean All Data** - Delete all users and badges
2. **Clean All Badges** - Delete all badge records only
3. **Clean Badges by Discord ID** - Delete badges for specific user
4. **Remove Discord ID** - Make user unverified
5. **Update User Name** - Change user's display name
6. **Update Skill Boost URL** - Change user's profile URL

**Usage:**

```bash
python cleanup_database.py
```

**Safety Features:**

- ⚠️ Confirmation prompts before destructive operations
- 📊 Shows current statistics before cleanup
- ✅ Verifies cleanup success
- 🔄 Transaction rollback on errors

**Functions:**

- `show_current_stats()` - Display database statistics
- `cleanup_database(confirm)` - Clean all data
- `cleanup_all_badges(confirm)` - Clean all badges
- `cleanup_badges_by_discord_id(discord_id)` - Clean badges for user
- `remove_discord_id_from_user(discord_id)` - Unverify user
- `update_user_name(discord_id, new_name)` - Update user name
- `update_skill_boost_url(discord_id, new_url)` - Update profile URL
- `verify_cleanup()` - Verify cleanup success

---

### 4. `scrape_badges.py`

**🕷️ Badge Date Scraper for Google Cloud Skills Boost**

Scrapes Google Cloud Skills Boost profiles to extract badge earned dates and creates a comprehensive CSV report.

**Features:**

- 🏆 Tracks 20 specific Google Cloud badges
- 📅 Extracts earned dates in YYYY-MM-DD format
- 🔄 Automatic retry on failures (max 3 attempts)
- 📊 Generates badge completion summary
- ⏱️ Respectful rate limiting (1 second delay)

**Tracked Badges (20):**

1. The Basics of Google Cloud Compute
2. Get Started with Cloud Storage
3. Get Started with Pub/Sub
4. Get Started with API Gateway
5. Get Started with Looker
6. Get Started with Dataplex
7. Get Started with Google Workspace Tools
8. App Building with AppSheet
9. Develop with Apps Script and AppSheet
10. Develop Gen AI Apps with Gemini and Streamlit
11. Build a Website on Google Cloud
12. Set Up a Google Cloud Network
13. Store, Process, and Manage Data on Google Cloud - Console
14. Cloud Run Functions: 3 Ways
15. App Engine: 3 Ways
16. Cloud Speech API: 3 Ways
17. Analyze Speech and Language with Google APIs
18. Monitoring in Google Cloud
19. Prompt Design in Vertex AI
20. Level 3: Generative AI

**Input:** `progress.csv` with columns:

- User Name
- User Email
- Google Cloud Skills Boost Profile URL

**Output:** `badge_dates.csv` with:

- User information
- Each badge as a column with earned date
- Total badge count

**Usage:**

```bash
python scrape_badges.py
```

**Functions:**

- `scrape_badge_dates(url, max_retries)` - Scrape badges from profile URL
- `parse_earned_date(date_text)` - Convert date to YYYY-MM-DD format
- `clean_columns(df)` - Clean CSV column names
- `main()` - Main execution function

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install required packages
pip install -r ../requirements.txt
```

### Common Workflows

**1. Analyze GDG Event Registrations:**

```bash
# Place registration data in data.csv
python analyze_full.py
# Output: full_analysis_results.csv with qualification status
```

**2. Import Users from CSV:**

```bash
python import_users_csv.py
# Follow interactive prompts
```

**3. Scrape Badge Dates:**

```bash
# Ensure progress.csv exists
python scrape_badges.py
# Output: badge_dates.csv
```

**4. Clean Database:**

```bash
python cleanup_database.py
# Choose operation from menu
```

---

## 📚 Dependencies

These scripts rely on the following packages:

- `mysql-connector-python` - Database connectivity
- `pandas` - Data manipulation and CSV processing
- `beautifulsoup4` - Web scraping and HTML parsing
- `requests` - HTTP requests for profile scraping
- `pytz` - Timezone handling

See `../requirements.txt` for complete list and versions.

---

## 🔒 Security Notes

- **Database Cleanup:** Always requires confirmation before destructive operations
- **Web Scraping:** Respects rate limits with 1-second delays between requests
- **CSV Processing:** Validates data integrity and handles missing/incomplete fields
- **Duplicate Detection:** Prevents multiple entries from same phone number

---

## 🛠️ Development

### Database Connection

All scripts use the centralized `database.py` module for database connectivity:

```python
from database import db
db.ensure_connection()
cursor = db.connection.cursor(dictionary=True)
```

### Logging

Scripts use Python's `logging` module for output:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

## 📞 Support

For issues or questions:

1. Check the main `README.md` in the project root
2. Review the script's docstrings and comments
3. Check the API documentation at `/docs` endpoint

---

## 📝 License

Part of the GDG-Link bot system. See project root for license information.

---

**Author:** Sayan Barma  
**Program:** Google Cloud Study Jams 2025
