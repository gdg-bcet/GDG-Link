"""
Import users from CSV with auto-assigned profile colors
Format: User Name, Google Cloud Skills Boost Profile URL, Discord ID (optional)
"""

import csv
import random
from database import db

# Curated list of visually appealing colors for profiles
PROFILE_COLORS = [
    # Blues
    "#3B82F6", "#2563EB", "#1D4ED8", "#60A5FA", "#0EA5E9",
    # Purples
    "#8B5CF6", "#7C3AED", "#6D28D9", "#A78BFA", "#9333EA",
    # Pinks
    "#EC4899", "#DB2777", "#BE185D", "#F472B6", "#E879F9",
    # Reds
    "#EF4444", "#DC2626", "#B91C1C", "#F87171", "#FB923C",
    # Oranges
    "#F97316", "#EA580C", "#C2410C", "#FB923C", "#FDBA74",
    # Yellows
    "#EAB308", "#CA8A04", "#A16207", "#FDE047", "#FCD34D",
    # Greens
    "#10B981", "#059669", "#047857", "#34D399", "#4ADE80",
    # Teals
    "#14B8A6", "#0D9488", "#0F766E", "#2DD4BF", "#5EEAD4",
    # Cyans
    "#06B6D4", "#0891B2", "#0E7490", "#22D3EE", "#67E8F9",
    # Indigos
    "#6366F1", "#4F46E5", "#4338CA", "#818CF8", "#A5B4FC",
    # Grays (for variety)
    "#64748B", "#475569", "#334155", "#94A3B8", "#52525B",
]


def generate_random_color():
    """Generate a random color from the curated palette"""
    return random.choice(PROFILE_COLORS)


def import_users_from_csv(csv_file="data.csv", skip_existing=True):
    """
    Import users from CSV with auto-assigned random profile colors

    Args:
        csv_file: Path to CSV file
        skip_existing: If True, skip users that already exist (by skillsboost_url)
    """
    print("\n" + "=" * 80)
    print("📥 IMPORTING USERS FROM CSV")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Mode: {'Skip existing' if skip_existing else 'Update existing'}")
    print("-" * 80)

    db.ensure_connection()
    cursor = db.connection.cursor(dictionary=True)

    try:
        # Read CSV file
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)

        print(f"\n📊 Found {len(rows)} users in CSV")
        print("-" * 80)

        imported = 0
        skipped = 0
        updated = 0
        errors = 0

        for row in rows:
            try:
                name = row['User Name'].strip()
                skillsboost_url = row['Google Cloud Skills Boost Profile URL'].strip()
                discord_id = row.get('Discord ID', '').strip() or None

                # Validate required fields
                if not name or not skillsboost_url:
                    print(f"  ⚠️  Skipping invalid row: {row}")
                    errors += 1
                    continue

                # Generate random color
                profile_color = generate_random_color()

                # Check if user already exists
                cursor.execute("SELECT id, profile_color FROM users WHERE skillsboost_url = %s", (skillsboost_url,))
                existing_user = cursor.fetchone()

                if existing_user:
                    if skip_existing:
                        print(f"  ⏭️  {name:40} (already exists)")
                        skipped += 1
                        continue
                    else:
                        # Update existing user
                        update_fields = []
                        update_values = []

                        update_fields.append("name = %s")
                        update_values.append(name)

                        if discord_id:
                            update_fields.append("discord_id = %s")
                            update_values.append(discord_id)

                        # Only update color if it doesn't have one
                        if not existing_user['profile_color']:
                            update_fields.append("profile_color = %s")
                            update_values.append(profile_color)

                        update_values.append(skillsboost_url)

                        query = f"UPDATE users SET {', '.join(update_fields)} WHERE skillsboost_url = %s"
                        cursor.execute(query, update_values)

                        print(f"  🔄 {name:40} (updated)")
                        updated += 1
                else:
                    # Insert new user
                    if discord_id:
                        # User is pre-verified
                        cursor.execute("""
                            INSERT INTO users (name, skillsboost_url, discord_id, profile_color, verified, registered_at)
                            VALUES (%s, %s, %s, %s, TRUE, NOW())
                        """, (name, skillsboost_url, discord_id, profile_color))
                        print(f"  ✅ {name:40} 🎨 {profile_color} [Verified]")
                    else:
                        # User needs to verify
                        cursor.execute("""
                            INSERT INTO users (name, skillsboost_url, profile_color, verified)
                            VALUES (%s, %s, %s, FALSE)
                        """, (name, skillsboost_url, profile_color))
                        print(f"  ✅ {name:40} 🎨 {profile_color}")

                    imported += 1

            except Exception as e:
                print(f"  ❌ Error processing {row.get('User Name', 'Unknown')}: {e}")
                errors += 1

        db.connection.commit()

        print("-" * 80)
        print("\n📊 IMPORT SUMMARY:")
        print(f"  • New users imported: {imported}")
        print(f"  • Existing users skipped: {skipped}")
        print(f"  • Users updated: {updated}")
        print(f"  • Errors: {errors}")
        print(f"  • Total processed: {imported + skipped + updated + errors}")

        if imported > 0 or updated > 0:
            print(f"\n✅ Successfully processed {imported + updated} users!")

    except FileNotFoundError:
        print(f"\n❌ CSV file not found: {csv_file}")
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        db.connection.rollback()
    finally:
        cursor.close()


def show_import_preview(csv_file="data.csv", limit=10):
    """Preview CSV data before import"""
    print("\n" + "=" * 80)
    print("👀 CSV PREVIEW")
    print("=" * 80)

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)

        print(f"\nFile: {csv_file}")
        print(f"Total rows: {len(rows)}")
        print(f"Showing first {min(limit, len(rows))} rows:\n")
        print("-" * 80)

        for i, row in enumerate(rows[:limit], 1):
            name = row.get('User Name', 'N/A')
            # url = row.get('Google Cloud Skills Boost Profile URL', 'N/A')
            discord = row.get('Discord ID', 'None')

            print(f"{i:3}. {name:30} {discord if discord else '(Not verified)'}")

        if len(rows) > limit:
            print(f"\n... and {len(rows) - limit} more users")

    except FileNotFoundError:
        print(f"\n❌ CSV file not found: {csv_file}")
    except Exception as e:
        print(f"\n❌ Preview failed: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CSV USER IMPORT UTILITY")
    print("Google Cloud Study Jams 2025 Badge Tracking System")
    print("=" * 80)

    csv_file = input("\nEnter CSV file path (default: data.csv): ").strip() or "data.csv"

    print("\nOptions:")
    print("1. Preview CSV data (first 10 rows)")
    print("2. Import users (skip existing)")
    print("3. Import users (update existing)")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        show_import_preview(csv_file)
    elif choice == "2":
        show_import_preview(csv_file, limit=5)
        confirm = input("\nProceed with import? (yes/no): ")
        if confirm.lower() == "yes":
            import_users_from_csv(csv_file, skip_existing=True)
        else:
            print("❌ Import cancelled")
    elif choice == "3":
        show_import_preview(csv_file, limit=5)
        confirm = input("\n⚠️  This will update existing users. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            import_users_from_csv(csv_file, skip_existing=False)
        else:
            print("❌ Import cancelled")
    else:
        print("\n👋 Goodbye!")

    print("\n" + "=" * 80)
