"""
Database Cleanup and Reset Script
Prepares database for fresh data by clearing all user and badge records.
Also provides utilities to clean badges, clean badges by Discord ID,
and remove Discord ID from users (making them unverified).
"""

from database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cleanup')


def show_current_stats():
    """Show current database statistics before cleanup"""
    print("\n📊 CURRENT DATABASE STATISTICS")
    print("-" * 80)

    db.ensure_connection()
    cursor = db.connection.cursor(dictionary=True)

    # Users stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_users,
            SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified_users,
            SUM(CASE WHEN verified = 0 THEN 1 ELSE 0 END) as unverified_users,
            SUM(CASE WHEN discord_id IS NOT NULL THEN 1 ELSE 0 END) as linked_users
        FROM users
    """)
    user_stats = cursor.fetchone()

    print("\nUsers Table:")
    print(f"  • Total Users: {user_stats['total_users']}")
    print(f"  • Verified Users: {user_stats['verified_users']}")
    print(f"  • Unverified (Pre-registered): {user_stats['unverified_users']}")
    print(f"  • With Discord ID: {user_stats['linked_users']}")

    # Badges stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_badges,
            COUNT(DISTINCT user_discord_id) as users_with_badges,
            COUNT(DISTINCT badge_name) as unique_badges
        FROM badges
    """)
    badge_stats = cursor.fetchone()

    print("\nBadges Table:")
    print(f"  • Total Badge Records: {badge_stats['total_badges']}")
    print(f"  • Users with Badges: {badge_stats['users_with_badges']}")
    print(f"  • Unique Badge Types: {badge_stats['unique_badges']}")

    # Completion stats
    cursor.execute("""
        SELECT COUNT(*) as completed_users
        FROM (
            SELECT user_discord_id
            FROM badges
            GROUP BY user_discord_id
            HAVING COUNT(*) = 20
        ) as completed
    """)
    completion_stats = cursor.fetchone()

    print("\nCompletion Stats:")
    print(f"  • Users with All 20 Badges: {completion_stats['completed_users']}")

    cursor.close()
    print("-" * 80)


def cleanup_database(confirm=False):
    """Clean up all user and badge data"""
    if not confirm:
        print("\n⚠️  WARNING: This will DELETE ALL DATA!")
        print("=" * 80)
        response = input("\nType 'YES DELETE ALL' to confirm: ")
        if response != "YES DELETE ALL":
            print("❌ Cleanup cancelled.")
            return False

    print("\n🧹 Starting database cleanup...")
    print("-" * 80)

    db.ensure_connection()
    cursor = db.connection.cursor()

    try:
        # Delete badges first (foreign key constraint)
        print("1. Deleting all badges...")
        cursor.execute("DELETE FROM badges")
        badges_deleted = cursor.rowcount
        print(f"   ✅ Deleted {badges_deleted} badge records")

        # Delete users
        print("2. Deleting all users...")
        cursor.execute("DELETE FROM users")
        users_deleted = cursor.rowcount
        print(f"   ✅ Deleted {users_deleted} user records")

        # Reset auto-increment counters
        print("3. Resetting auto-increment counters...")
        cursor.execute("ALTER TABLE badges AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
        print("   ✅ Auto-increment counters reset")

        db.connection.commit()

        print("-" * 80)
        print("✅ DATABASE CLEANUP COMPLETE!")
        print(f"   • Removed {users_deleted} users")
        print(f"   • Removed {badges_deleted} badges")
        print("   • Database is now empty and ready for fresh data")

        return True

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        db.connection.rollback()
        return False
    finally:
        cursor.close()


def cleanup_all_badges(confirm=False):
    """Delete all badge records only"""
    if not confirm:
        print("\n⚠️  WARNING: This will DELETE ALL BADGES!")
        response = input("Type 'YES DELETE BADGES' to confirm: ")
        if response != "YES DELETE BADGES":
            print("❌ Badge cleanup cancelled.")
            return False

    db.ensure_connection()
    cursor = db.connection.cursor()
    try:
        cursor.execute("DELETE FROM badges")
        badges_deleted = cursor.rowcount
        cursor.execute("ALTER TABLE badges AUTO_INCREMENT = 1")
        db.connection.commit()
        print(f"✅ Deleted {badges_deleted} badge records. Badges table is now empty.")
        return True
    except Exception as e:
        logger.error(f"❌ Badge cleanup failed: {e}")
        db.connection.rollback()
        return False
    finally:
        cursor.close()


def cleanup_badges_by_discord_id(discord_id):
    """Delete all badges for a specific Discord ID"""
    db.ensure_connection()
    cursor = db.connection.cursor()
    try:
        cursor.execute("DELETE FROM badges WHERE user_discord_id = %s", (discord_id,))
        badges_deleted = cursor.rowcount
        db.connection.commit()
        print(f"✅ Deleted {badges_deleted} badges for Discord ID {discord_id}.")
        return True
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        db.connection.rollback()
        return False
    finally:
        cursor.close()


def remove_discord_id_from_user(discord_id):
    """Remove Discord ID from users table, making them unverified"""
    db.ensure_connection()
    cursor = db.connection.cursor()
    try:
        cursor.execute("""
            UPDATE users
            SET discord_id = NULL, verified = 0, registered_at = NULL
            WHERE discord_id = %s
        """, (discord_id,))
        updated = cursor.rowcount
        db.connection.commit()
        if updated:
            print(f"✅ Removed Discord ID {discord_id} from {updated} user(s). User(s) are now unverified.")
        else:
            print(f"⚠️ No user found with Discord ID {discord_id}.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to remove Discord ID: {e}")
        db.connection.rollback()
        return False
    finally:
        cursor.close()


def update_user_name(discord_id, new_name):
    """Update the name for a user by Discord ID"""
    db.ensure_connection()
    cursor = db.connection.cursor(dictionary=True)
    try:
        # First check if user exists
        cursor.execute("SELECT name FROM users WHERE discord_id = %s", (discord_id,))
        user = cursor.fetchone()

        if not user:
            print(f"⚠️ No user found with Discord ID {discord_id}.")
            return False

        old_name = user['name']

        # Update the name
        cursor.execute("""
            UPDATE users
            SET name = %s
            WHERE discord_id = %s
        """, (new_name, discord_id))

        db.connection.commit()
        print(f"✅ Updated name for Discord ID {discord_id}")
        print(f"   Old name: {old_name}")
        print(f"   New name: {new_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update name: {e}")
        db.connection.rollback()
        return False
    finally:
        cursor.close()


def update_skill_boost_url(discord_id, new_url):
    """Update the skill boost URL for a user by Discord ID"""
    db.ensure_connection()
    cursor = db.connection.cursor(dictionary=True)
    try:
        # First check if user exists
        cursor.execute("SELECT skillsboost_url FROM users WHERE discord_id = %s", (discord_id,))
        user = cursor.fetchone()

        if not user:
            print(f"⚠️ No user found with Discord ID {discord_id}.")
            return False

        old_url = user['skillsboost_url']

        # Update the URL
        cursor.execute("""
            UPDATE users
            SET skillsboost_url = %s
            WHERE discord_id = %s
        """, (new_url, discord_id))

        db.connection.commit()
        print(f"✅ Updated Skill Boost URL for Discord ID {discord_id}")
        print(f"   Old URL: {old_url}")
        print(f"   New URL: {new_url}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update Skill Boost URL: {e}")
        db.connection.rollback()
        return False
    finally:
        cursor.close()


def verify_cleanup():
    """Verify that cleanup was successful"""
    print("\n🔍 Verifying cleanup...")
    print("-" * 80)

    db.ensure_connection()
    cursor = db.connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM badges")
    badge_count = cursor.fetchone()['count']

    cursor.close()

    print(f"Users remaining: {user_count}")
    print(f"Badges remaining: {badge_count}")

    if user_count == 0 and badge_count == 0:
        print("✅ Cleanup verified - database is empty!")
        return True
    else:
        print("⚠️  Warning: Some records still remain")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DATABASE CLEANUP UTILITY")
    print("Google Cloud Study Jams 2025 Badge Tracking System")
    print("=" * 80)

    # Show current stats
    show_current_stats()

    # Ask for cleanup
    print("\n" + "=" * 80)
    print("CLEANUP OPTIONS")
    print("=" * 80)
    print("\n1. Clean all data (users + badges)")
    print("2. Clean all badges only")
    print("3. Clean badges by Discord ID")
    print("4. Remove Discord ID from user (make unverified)")
    print("5. Update user name")
    print("6. Update Skill Boost URL")
    print("7. Cancel")

    choice = input("\nEnter your choice (1-7): ")

    if choice == "1":
        success = cleanup_database()
        if success:
            verify_cleanup()
    elif choice == "2":
        success = cleanup_all_badges()
        if success:
            verify_cleanup()
    elif choice == "3":
        discord_id = input("Enter Discord ID to clean badges for: ")
        success = cleanup_badges_by_discord_id(discord_id)
        if success:
            verify_cleanup()
    elif choice == "4":
        discord_id = input("Enter Discord ID to remove from users: ")
        success = remove_discord_id_from_user(discord_id)
        if success:
            verify_cleanup()
    elif choice == "5":
        discord_id = input("Enter Discord ID: ")
        new_name = input("Enter new name: ")
        update_user_name(discord_id, new_name)
    elif choice == "6":
        discord_id = input("Enter Discord ID: ")
        new_url = input("Enter new Skill Boost URL: ")
        update_skill_boost_url(discord_id, new_url)
    else:
        print("\n❌ Operation cancelled.")

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80 + "\n")
