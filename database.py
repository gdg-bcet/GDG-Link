"""
Optimized Database operations for Study Jams 2025 Badge Tracking System
Clean, efficient, production-ready implementation
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, Optional, List
import logging
from datetime import datetime
import pytz  # For timezone handling
import os
from dotenv import load_dotenv

load_dotenv()

# Kolkata timezone
KOLKATA_TZ = pytz.timezone('Asia/Kolkata')


def get_kolkata_time():
    """Get current time in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)


# Database Configuration
DB_CONFIG = {
    'host': os.getenv("DATABASE_HOST"),
    'port': int(os.getenv("DATABASE_PORT")),
    'user': os.getenv("DATABASE_USER"),
    'password': os.getenv("DATABASE_PASSWORD"),
    'database': os.getenv("DATABASE_NAME"),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'time_zone': '+05:30'  # Asia/Kolkata timezone (UTC+5:30)
}

# Setup logging
logger = logging.getLogger('database')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Define all Google Cloud Study Jams 2025 badges (constant)
ALL_BADGES = [
    "The Basics of Google Cloud Compute", "Get Started with Cloud Storage",
    "Get Started with Pub/Sub", "Get Started with API Gateway",
    "Get Started with Looker", "Get Started with Dataplex",
    "Get Started with Google Workspace Tools", "App Building with AppSheet",
    "Develop with Apps Script and AppSheet", "Develop Gen AI Apps with Gemini and Streamlit",
    "Build a Website on Google Cloud", "Set Up a Google Cloud Network",
    "Store, Process, and Manage Data on Google Cloud - Console", "Cloud Run Functions: 3 Ways",
    "App Engine: 3 Ways", "Cloud Speech API: 3 Ways",
    "Analyze Speech and Language with Google APIs", "Monitoring in Google Cloud",
    "Prompt Design in Vertex AI", "Level 3: Generative AI"
]


class DatabaseOperations:
    def __init__(self):
        """Initialize optimized database connection"""
        self.connection = None
        self.connect()
        self.ensure_tables_exist()

    def connect(self) -> bool:
        """Establish database connection with retry logic"""
        try:
            if self.connection and self.connection.is_connected():
                return True

            self.connection = mysql.connector.connect(**DB_CONFIG)
            logger.info("✅ Successfully connected to MySQL database")
            return True

        except Error as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def ensure_connection(self):
        """Ensure database connection is active"""
        if not self.connection or not self.connection.is_connected():
            self.connect()

    def ensure_tables_exist(self):
        """Create tables if they don't exist with optimized indexes"""
        self.ensure_connection()
        cursor = self.connection.cursor()

        try:
            # Users table with optimized indexes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    skillsboost_url VARCHAR(500) NOT NULL UNIQUE,
                    discord_id VARCHAR(50) UNIQUE DEFAULT NULL,
                    profile_color VARCHAR(7) DEFAULT NULL COMMENT 'Hex color for profile image generation',
                    verified BOOLEAN DEFAULT FALSE,
                    registered_at TIMESTAMP NULL DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_discord_id (discord_id),
                    INDEX idx_verified (verified),
                    INDEX idx_skillsboost_url (skillsboost_url)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            # Badges table with optimized indexes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS badges (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_discord_id VARCHAR(50) NOT NULL,
                    badge_name VARCHAR(255) NOT NULL,
                    badge_url VARCHAR(500) NOT NULL,
                    earned_date DATE NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
                    verification_notes TEXT,
                    FOREIGN KEY (user_discord_id) REFERENCES users(discord_id) ON DELETE CASCADE,
                    INDEX idx_user_discord_id (user_discord_id),
                    INDEX idx_badge_name (badge_name),
                    INDEX idx_submitted_at (submitted_at),
                    UNIQUE KEY unique_user_badge (user_discord_id, badge_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            self.connection.commit()
            logger.info("✅ Database tables ensured to exist")

        except Error as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
        finally:
            cursor.close()

    # ==================== CORE API METHODS ====================

    def get_all_user_progress(self) -> Dict:
        """Get progress data for all verified users - OPTIMIZED"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            # Single optimized query with GROUP_CONCAT
            cursor.execute("""
                SELECT
                    u.discord_id,
                    u.name,
                    u.skillsboost_url,
                    u.profile_color,
                    COUNT(b.id) as badge_count,
                    MAX(b.submitted_at) as latest_badge_date,
                    GROUP_CONCAT(b.badge_name SEPARATOR '|||') as badges_earned
                FROM users u
                LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                WHERE u.verified = 1
                GROUP BY u.discord_id, u.name, u.skillsboost_url, u.profile_color
                ORDER BY badge_count DESC, latest_badge_date ASC, u.name ASC
            """)
            users_data = cursor.fetchall()

            # Process data efficiently in memory
            users_list = []
            rank = 1

            for user in users_data:
                # Parse badges from concatenated string
                user_badges = set()
                if user['badges_earned']:
                    user_badges = set(user['badges_earned'].split('|||'))

                # Create badges dictionary efficiently
                badges_status = {badge: "Done" if badge in user_badges else "" for badge in ALL_BADGES}

                users_list.append({
                    "Rank": rank,
                    "Discord ID": user['discord_id'],
                    "Name": user['name'],
                    "Profile URL": user['skillsboost_url'] or "",
                    "Profile Color": user['profile_color'] or "#1F2937",
                    "Badge Count": user['badge_count'] or 0,
                    "badges": badges_status
                })
                rank += 1

            return {
                "program_name": "Google Cloud Study Jams 2025",
                "total_badges": len(ALL_BADGES),
                "total_users": len(users_list),
                "users": users_list
            }

        except Exception as e:
            logger.error(f"Error getting all user progress: {e}")
            return {
                "program_name": "Google Cloud Study Jams 2025",
                "total_badges": 20,
                "total_users": 0,
                "users": []
            }
        finally:
            cursor.close()

    def get_all_user_progress_filtered(self, search=None, sort_by="badge_count", sort_order="desc", badge_count_condition="") -> Dict:
        """Get progress data for all verified users with advanced filtering - OPTIMIZED"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            # First, get ALL users to calculate global ranks
            cursor.execute("""
                SELECT
                    u.discord_id,
                    u.name,
                    u.skillsboost_url,
                    u.profile_color,
                    COUNT(b.id) as badge_count,
                    MAX(b.submitted_at) as latest_badge_date,
                    GROUP_CONCAT(b.badge_name SEPARATOR '|||') as badges_earned
                FROM users u
                LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                WHERE u.verified = 1
                GROUP BY u.discord_id, u.name, u.skillsboost_url, u.profile_color
            """)
            all_users = cursor.fetchall()

            # Sort ALL users by global ranking criteria (badge_count DESC, latest_badge_date ASC, name ASC)
            # FCFS: Earlier last badge date = higher rank for same badge count
            def global_sort_key(x):
                badge_count = x['badge_count'] or 0
                latest_date = x['latest_badge_date']
                # For FCFS: earlier dates should rank higher
                # Use timestamp() to include hours/minutes/seconds, not just date
                if latest_date:
                    # Convert to timestamp (seconds since epoch) for precise sorting
                    date_value = latest_date.timestamp()
                else:
                    # Put users with no badges at the end
                    date_value = float('inf')
                return (-badge_count, date_value, x['name'])

            all_users.sort(key=global_sort_key)

            # Create a mapping of discord_id to global rank
            rank_map = {}
            for rank, user in enumerate(all_users, start=1):
                rank_map[user['discord_id']] = rank

            # Apply filters to get the subset of users to display
            users_data = all_users.copy()

            # Apply search filter
            if search:
                users_data = [u for u in users_data if search.lower() in u['name'].lower()]

            # Apply badge count filter in Python for complex logic
            if badge_count_condition:
                filtered_users = []
                for user in users_data:
                    badge_count = user['badge_count'] or 0

                    # Parse the condition properly - handle " AND badge_count = 4" format
                    condition_str = badge_count_condition.strip()

                    # Extract operator and value from condition like " AND badge_count = 4"
                    import re
                    match = re.search(r'badge_count\s*(>=|<=|>|<|=)\s*(\d+)', condition_str)
                    if match:
                        operator, value = match.groups()
                        target_value = int(value)

                        # Evaluate condition
                        condition_met = False
                        if operator == "=":
                            condition_met = badge_count == target_value
                        elif operator == ">":
                            condition_met = badge_count > target_value
                        elif operator == "<":
                            condition_met = badge_count < target_value
                        elif operator == ">=":
                            condition_met = badge_count >= target_value
                        elif operator == "<=":
                            condition_met = badge_count <= target_value

                        if condition_met:
                            filtered_users.append(user)
                users_data = filtered_users

            # Sort the filtered data ONLY if user explicitly requests different sorting
            # Default (sort_by="badge_count", sort_order="desc") should use global ranking
            if sort_by == "name":
                # User requested name sorting
                users_data.sort(key=lambda x: x['name'], reverse=(sort_order == "desc"))
            elif sort_order == "asc":
                # User requested ascending badge count (non-default)
                def sort_key(x):
                    badge_count = x['badge_count'] or 0
                    latest_date = x['latest_badge_date']
                    if latest_date:
                        date_value = latest_date.timestamp()
                    else:
                        date_value = float('inf')
                    return (badge_count, date_value, x['name'])
                users_data.sort(key=sort_key)
            # else: keep global ranking order (default: sort_by="badge_count", sort_order="desc")

            # Get total user count (unfiltered)
            total_users = len(all_users)

            # Process data efficiently in memory
            users_list = []

            for user in users_data:
                # Parse badges from concatenated string
                user_badges = set()
                if user['badges_earned']:
                    user_badges = set(user['badges_earned'].split('|||'))

                # Create badges dictionary efficiently
                badges_status = {badge: "Done" if badge in user_badges else "" for badge in ALL_BADGES}

                users_list.append({
                    "Rank": rank_map[user['discord_id']],  # Use global rank from rank_map
                    "Discord ID": user['discord_id'],
                    "Name": user['name'],
                    "Profile URL": user['skillsboost_url'] or "",
                    "Profile Color": user['profile_color'] or "#1F2937",
                    "Badge Count": user['badge_count'] or 0,
                    "badges": badges_status
                })

            return {
                "program_name": "Google Cloud Study Jams 2025",
                "total_badges": len(ALL_BADGES),
                "total_users": total_users,
                "users": users_list
            }

        except Exception as e:
            logger.error(f"Error getting filtered user progress: {e}")
            return {
                "program_name": "Google Cloud Study Jams 2025",
                "total_badges": 20,
                "total_users": 0,
                "users": []
            }
        finally:
            cursor.close()

    def get_stats(self) -> Dict:
        """Get overall statistics - HIGHLY OPTIMIZED"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            # Optimized mega-query for main stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(DISTINCT CASE WHEN u.discord_id IS NOT NULL THEN u.discord_id END) as verified_users,
                    COUNT(DISTINCT CASE WHEN badge_counts.badge_count = 20 THEN badge_counts.discord_id END) as completed_users,
                    COALESCE(SUM(badge_counts.badge_count), 0) as total_badges_earned,
                    COUNT(DISTINCT CASE WHEN badge_counts.badge_count > 0 THEN badge_counts.discord_id END) as users_with_badges,
                    (SELECT u.discord_id FROM users u
                     LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                     WHERE u.discord_id IS NOT NULL GROUP BY u.discord_id
                     ORDER BY COUNT(b.id) DESC, MAX(b.submitted_at) ASC LIMIT 1) as top_discord_id,
                    (SELECT u.name FROM users u
                     LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                     WHERE u.discord_id IS NOT NULL GROUP BY u.discord_id
                     ORDER BY COUNT(b.id) DESC, MAX(b.submitted_at) ASC LIMIT 1) as top_name,
                    (SELECT u.skillsboost_url FROM users u
                     LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                     WHERE u.discord_id IS NOT NULL GROUP BY u.discord_id
                     ORDER BY COUNT(b.id) DESC, MAX(b.submitted_at) ASC LIMIT 1) as top_url,
                    (SELECT u.profile_color FROM users u
                     LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                     WHERE u.discord_id IS NOT NULL GROUP BY u.discord_id
                     ORDER BY COUNT(b.id) DESC, MAX(b.submitted_at) ASC LIMIT 1) as top_color,
                    (SELECT COUNT(b.id) FROM users u
                     LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                     WHERE u.discord_id IS NOT NULL GROUP BY u.discord_id
                     ORDER BY COUNT(b.id) DESC, MAX(b.submitted_at) ASC LIMIT 1) as top_badge_count
                FROM users u
                LEFT JOIN (
                    SELECT user_discord_id as discord_id, COUNT(*) as badge_count
                    FROM badges GROUP BY user_discord_id
                ) badge_counts ON u.discord_id = badge_counts.discord_id
            """)

            main_stats = cursor.fetchone()

            # Get badge completion stats efficiently
            cursor.execute("SELECT badge_name, COUNT(*) as count FROM badges GROUP BY badge_name")
            badge_data = cursor.fetchall()
            badge_completion_stats = {badge: 0 for badge in ALL_BADGES}
            for badge in badge_data:
                if badge['badge_name'] in badge_completion_stats:
                    badge_completion_stats[badge['badge_name']] = badge['count']

            # Get completion distribution
            cursor.execute("""
                SELECT badge_count, COUNT(*) as user_count
                FROM (
                    SELECT COALESCE(COUNT(b.id), 0) as badge_count
                    FROM users u
                    LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                    WHERE u.verified = 1
                    GROUP BY u.discord_id
                ) as counts
                GROUP BY badge_count
            """)

            distribution_data = cursor.fetchall()
            completion_distribution = {str(i): 0 for i in range(21)}
            for dist in distribution_data:
                completion_distribution[str(dist['badge_count'])] = dist['user_count']

            # Get progress timeline
            cursor.execute("""
                SELECT DATE(submitted_at) as date, COUNT(*) as count
                FROM badges
                WHERE submitted_at IS NOT NULL
                GROUP BY DATE(submitted_at)
                ORDER BY DATE(submitted_at)
            """)
            timeline_data = cursor.fetchall()
            progress_timeline = {}
            for entry in timeline_data:
                if entry['date']:
                    date_str = entry['date'].strftime('%Y-%m-%d')
                    progress_timeline[date_str] = entry['count']

            # Calculate metrics
            total_users = main_stats['total_users'] or 0
            verified_users = main_stats['verified_users'] or 0
            completed_users = main_stats['completed_users'] or 0
            total_badges_earned = main_stats['total_badges_earned'] or 0
            users_with_badges = main_stats['users_with_badges'] or 0

            # Average badges only for users who have at least 1 badge
            average_badges = int(total_badges_earned / max(users_with_badges, 1))

            # Calculate completion percentage based on tiers
            # Tier 3 (0-49): Show progress out of 50
            # Tier 2 (50-69): Show progress out of 70
            # Tier 1 (70-100): Show progress out of 100, capped at 100%
            if completed_users < 50:
                # Tier 3: Calculate percentage out of 50
                completion_percentage = int((completed_users / 50) * 100)
                tier_name = "Tier 3"
                tier_emoji = "🥉"
                tier_target = 50
            elif completed_users < 70:
                # Tier 2: Calculate percentage out of 70
                completion_percentage = int((completed_users / 70) * 100)
                tier_name = "Tier 2"
                tier_emoji = "🥈"
                tier_target = 70
            else:
                # Tier 1: Calculate percentage out of 100, cap at 100%
                completion_percentage = min(int((completed_users / 100) * 100), 100)
                tier_name = "Tier 1"
                tier_emoji = "🥇"
                tier_target = 100

            # Top performer
            top_performer = {}
            if main_stats['top_discord_id']:
                top_performer = {
                    "discord_id": main_stats['top_discord_id'],
                    "name": main_stats['top_name'] or "",
                    "badge_count": main_stats['top_badge_count'] or 0,
                    "profile_url": main_stats['top_url'] or "",
                    "profile_color": main_stats['top_color'] or "#1F2937"
                }

            return {
                "program_name": "Google Cloud Study Jams 2025",
                "total_users": total_users,
                "verified_users": verified_users,
                "completed_users": completed_users,
                "total_badges": len(ALL_BADGES),
                "total_badges_earned": total_badges_earned,
                "completion_percentage": completion_percentage,
                "tier": tier_name,
                "tier_emoji": tier_emoji,
                "tier_target": tier_target,
                "average_badges": average_badges,
                "badge_completion_stats": badge_completion_stats,
                "completion_distribution": completion_distribution,
                "top_performer": top_performer,
                "progress_timeline": progress_timeline,
                "last_updated": get_kolkata_time().isoformat(),
                "mode": "production-ready"
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "program_name": "Google Cloud Study Jams 2025",
                "total_users": 0, "completed_users": 0, "total_badges": 20,
                "completion_percentage": 0, "tier": "Tier 3", "tier_emoji": "🥉",
                "tier_target": 50, "average_badges": 0,
                "badge_completion_stats": {badge: 0 for badge in ALL_BADGES},
                "completion_distribution": {str(i): 0 for i in range(21)},
                "top_performer": {}, "progress_timeline": {},
                "last_updated": get_kolkata_time().isoformat(), "mode": "production-ready"
            }
        finally:
            cursor.close()

    def get_user_progress(self, discord_id: str) -> Dict:
        """Get detailed progress for specific user with timestamps"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            # Get user data
            cursor.execute("""
                SELECT discord_id, name, skillsboost_url, profile_color, verified
                FROM users
                WHERE discord_id = %s AND verified = 1
            """, (discord_id,))

            user_data = cursor.fetchone()
            if not user_data:
                return None

            # Get user badges with details
            cursor.execute("""
                SELECT badge_name, badge_url, submitted_at
                FROM badges
                WHERE user_discord_id = %s
                ORDER BY submitted_at ASC
            """, (discord_id,))

            user_badges = cursor.fetchall()
            completed_badges = {badge['badge_name']: badge for badge in user_badges}

            # Build detailed badge list
            badges = []
            for badge_name in ALL_BADGES:
                if badge_name in completed_badges:
                    badge_info = completed_badges[badge_name]
                    # Format timestamp
                    timestamp = None
                    if badge_info['submitted_at']:
                        timestamp = badge_info['submitted_at'].strftime('%Y-%m-%d %H:%M:%S')

                    badges.append({
                        "name": badge_name,
                        "completed": True,
                        "url": badge_info['badge_url'],
                        "timestamp": timestamp
                    })
                else:
                    badges.append({
                        "name": badge_name,
                        "completed": False,
                        "url": None,
                        "timestamp": None
                    })

            badge_count = len([b for b in badges if b['completed']])
            completion_percentage = int((badge_count / len(ALL_BADGES)) * 100)

            return {
                "discord_id": user_data['discord_id'],
                "name": user_data['name'],
                "profile": user_data['skillsboost_url'] or "",
                "profile_color": user_data['profile_color'] or "#1F2937",
                "badge_count": badge_count,
                "total_badges": len(ALL_BADGES),
                "completion_percentage": completion_percentage,
                "badges": badges,
                "mode": "production-ready"
            }

        except Exception as e:
            logger.error(f"Error getting user progress for {discord_id}: {e}")
            return None
        finally:
            cursor.close()

    def get_leaderboard(self) -> Dict:
        """Get leaderboard data - top 10 performers"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            # Get top 10 performers with their badges
            cursor.execute("""
                SELECT
                    u.discord_id,
                    u.name,
                    u.skillsboost_url,
                    u.profile_color,
                    COUNT(b.id) as badge_count,
                    MAX(b.submitted_at) as latest_badge_date,
                    GROUP_CONCAT(b.badge_name SEPARATOR '|||') as badges_earned
                FROM users u
                LEFT JOIN badges b ON u.discord_id = b.user_discord_id
                WHERE u.verified = 1
                GROUP BY u.discord_id, u.name, u.skillsboost_url, u.profile_color
                ORDER BY badge_count DESC, latest_badge_date ASC, u.name ASC
                LIMIT 10
            """)
            users_data = cursor.fetchall()

            # Get total participants count
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE verified = 1")
            total_participants = cursor.fetchone()['total']

            # Process top performers
            top_performers = []
            rank = 1

            for user in users_data:
                # Parse badges from concatenated string
                user_badges = set()
                if user['badges_earned']:
                    user_badges = set(user['badges_earned'].split('|||'))

                # Create badges dictionary efficiently
                badges_status = {badge: "Done" if badge in user_badges else "" for badge in ALL_BADGES}

                top_performers.append({
                    "Rank": rank,
                    "Discord ID": user['discord_id'],
                    "Name": user['name'],
                    "Profile URL": user['skillsboost_url'] or "",
                    "Profile Color": user['profile_color'] or "#1F2937",
                    "Badge Count": user['badge_count'] or 0,
                    "badges": badges_status
                })
                rank += 1

            return {
                "program_name": "Google Cloud Study Jams 2025",
                "top_performers": top_performers,
                "total_participants": total_participants,
                "last_updated": get_kolkata_time().isoformat(),
                "mode": "production-ready"
            }

        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return {
                "program_name": "Google Cloud Study Jams 2025",
                "top_performers": [],
                "total_participants": 0,
                "last_updated": get_kolkata_time().isoformat(),
                "mode": "production-ready"
            }
        finally:
            cursor.close()

    # ==================== DISCORD BOT METHODS ====================

    def get_user_by_discord_id(self, discord_id: str) -> Optional[Dict]:
        """Get user by Discord ID for bot commands"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE discord_id = %s", (discord_id,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"❌ Failed to get user by Discord ID {discord_id}: {e}")
            return None
        finally:
            cursor.close()

    def get_user_by_skillsboost_url(self, skillsboost_url: str) -> Optional[Dict]:
        """Get user by SkillsBoost URL for verification"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE skillsboost_url = %s", (skillsboost_url,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"❌ Failed to get user by URL: {e}")
            return None
        finally:
            cursor.close()

    def add_badge(self, discord_id: str, badge_name: str, badge_url: str, earned_date: str) -> bool:
        """Add badge for user"""
        self.ensure_connection()
        cursor = self.connection.cursor()

        try:
            query = """
                INSERT INTO badges (user_discord_id, badge_name, badge_url, earned_date)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    badge_url = VALUES(badge_url),
                    earned_date = VALUES(earned_date),
                    submitted_at = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (discord_id, badge_name, badge_url, earned_date))

            if cursor.rowcount > 0:
                logger.info(f"✅ Badge '{badge_name}' added for {discord_id}")
                return True
            return False

        except Error as e:
            logger.error(f"❌ Failed to add badge: {e}")
            return False
        finally:
            cursor.close()

    def verify_user(self, discord_id: str) -> bool:
        """Mark user as verified"""
        self.ensure_connection()
        cursor = self.connection.cursor()

        try:
            query = "UPDATE users SET verified = TRUE, updated_at = CURRENT_TIMESTAMP WHERE discord_id = %s"
            cursor.execute(query, (discord_id,))

            if cursor.rowcount > 0:
                logger.info(f"✅ User {discord_id} verified successfully")
                return True
            else:
                logger.warning(f"⚠️ User {discord_id} not found for verification")
                return False

        except Error as e:
            logger.error(f"❌ Failed to verify user {discord_id}: {e}")
            return False
        finally:
            cursor.close()

    def check_skillsboost_url_exists(self, skillsboost_url: str) -> Optional[Dict]:
        """Check if a SkillsBoost URL exists in the database and return user data"""
        return self.get_user_by_skillsboost_url(skillsboost_url)

    def register_discord_user(self, discord_id: str, skillsboost_url: str) -> tuple:
        """Register a Discord user by linking to existing SkillsBoost profile"""
        self.ensure_connection()
        cursor = self.connection.cursor()

        try:
            # Update the users table to link Discord ID
            cursor.execute("""
                UPDATE users
                SET discord_id = %s, verified = 1, registered_at = NOW()
                WHERE skillsboost_url = %s AND discord_id IS NULL
            """, (discord_id, skillsboost_url))

            if cursor.rowcount > 0:
                self.connection.commit()
                return True, "Registration successful"
            else:
                return False, "Profile not found or already linked"

        except Exception as e:
            logger.error(f"Error registering Discord user: {e}")
            return False, f"Registration error: {str(e)}"
        finally:
            cursor.close()

    def get_user_badges(self, discord_id: str) -> List[Dict]:
        """Get all badges for a specific user"""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT badge_name, badge_url, submitted_at
                FROM badges
                WHERE user_discord_id = %s
                ORDER BY submitted_at DESC
            """, (discord_id,))

            return cursor.fetchall()

        except Exception as e:
            logger.error(f"Error getting user badges: {e}")
            return []
        finally:
            cursor.close()

    def get_all_badges(self):
        """Get all badges as pandas DataFrame (for compatibility with old code)"""
        import pandas as pd

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    b.user_discord_id as discord_id,
                    u.name,
                    b.badge_name,
                    b.badge_url,
                    b.earned_date,
                    b.submitted_at
                FROM badges b
                LEFT JOIN users u ON b.user_discord_id = u.discord_id
                ORDER BY b.submitted_at DESC
            """)

            data = cursor.fetchall()
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error getting all badges: {e}")
            import pandas as pd
            return pd.DataFrame()
        finally:
            cursor.close()

    def get_progress_stats(self) -> Dict:
        """Get progress statistics with bot-compatible format"""
        stats = self.get_stats()

        # Create compatible format for Discord bot commands
        return {
            "total_users": stats.get("total_users", 0),
            "verified_users": stats.get("verified_users", 0),
            "completed_users": stats.get("completed_users", 0),
            "total_badges": int(stats.get("total_badges_earned", 0)),  # Use actual count from database
            "average_badges": stats.get("average_badges", 0),  # Average for users with badges
            "badge_distribution": stats.get("badge_completion_stats", {}),
            "completion_percentage": stats.get("completion_percentage", 0),
            "program_name": stats.get("program_name", "Google Cloud Study Jams 2025"),
            "last_updated": stats.get("last_updated", ""),
            "top_performer": stats.get("top_performer", {})
        }

    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("📝 Database connection closed")


# Global database instance
db = DatabaseOperations()


# Test database connection on import
if __name__ == "__main__":
    print("🧪 Testing database connection...")

    # Test connection
    if db.connection and db.connection.is_connected():
        print("✅ Database connection test passed")

    # Test basic query
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE verified = 1")
        result = cursor.fetchone()
        print(f"✅ Database query test passed: {result[0]} verified users")
        cursor.close()
    except Exception as e:
        print(f"❌ Database query test failed: {e}")

    print("🎉 Database module loaded successfully!")
