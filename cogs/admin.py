"""
Admin Cog - Admin-only commands for bot management
"""
import discord
from discord.ext import commands
import pandas as pd
import io
from database import db, ALL_BADGES
from config import VERIFIED_ROLE_ID, COMPLETION_ROLE_ID, BADGE_URL_PATTERN
import re
import requests
from bs4 import BeautifulSoup
import json


class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    @commands.has_any_role("Admin")
    async def sync(self, ctx, guilds: commands.Greedy[discord.Object], spec: str = None):
        """Syncs slash commands."""
        async with ctx.typing():
            if not guilds:
                if spec == "~":
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                elif spec == "*":
                    ctx.bot.tree.copy_global_to(guild=ctx.guild)
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                elif spec == "^":
                    ctx.bot.tree.clear_commands(guild=ctx.guild)
                    await ctx.bot.tree.sync(guild=ctx.guild)
                    synced = []
                else:
                    synced = await ctx.bot.tree.sync()
                await ctx.send(f"✅ Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
                return

            ret = 0
            for guild in guilds:
                try:
                    await ctx.bot.tree.sync(guild=guild)
                    ret += 1
                except discord.HTTPException:
                    pass
            await ctx.send(f"✅ Synced the tree to {ret}/{len(guilds)} guilds.")

    @commands.hybrid_command(
        name="export_users",
        with_app_command=True,
        description="Export users data as CSV file.",
    )
    @commands.has_any_role("Admin")
    async def export_users(self, ctx):
        """Export all users to CSV"""
        if ctx.interaction:
            await ctx.defer()

        try:
            db.ensure_connection()
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT name, skillsboost_url, discord_id, verified, registered_at, profile_color
                FROM users
                ORDER BY registered_at
            """)
            users = cursor.fetchall()
            cursor.close()

            if not users:
                return await ctx.send("❌ No users found in database.")

            df = pd.DataFrame(users)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode('utf-8')

            file = discord.File(
                io.BytesIO(csv_data),
                filename=f"users_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            await ctx.send(f"📊 Users export complete! Total: {len(users)} users", file=file)
        except Exception as e:
            await ctx.send(f"❌ Error exporting users: {e}")

    @commands.hybrid_command(
        name="export_badges",
        with_app_command=True,
        description="Export badges data as CSV file.",
    )
    @commands.has_any_role("Admin")
    async def export_badges(self, ctx):
        """Export all badges to CSV"""
        if ctx.interaction:
            await ctx.defer()

        try:
            df = db.get_all_badges()

            if df.empty:
                return await ctx.send("❌ No badges found in database.")

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode('utf-8')

            file = discord.File(
                io.BytesIO(csv_data),
                filename=f"badges_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            await ctx.send(f"🏅 Badges export complete! Total: {len(df)} badges", file=file)
        except Exception as e:
            await ctx.send(f"❌ Error exporting badges: {e}")

    @commands.hybrid_command(
        name="download_data",
        with_app_command=True,
        description="Download original data files.",
    )
    @commands.has_any_role("Admin")
    async def download_csv(self, ctx):
        """Download original CSV and JSON files"""
        try:
            files = []

            try:
                files.append(discord.File("data.csv"))
            except FileNotFoundError:
                pass

            try:
                files.append(discord.File("badges.json"))
            except FileNotFoundError:
                pass

            if files:
                await ctx.send("📁 Original data files:", files=files)
            else:
                await ctx.send("❌ Original data files not found.")
        except Exception as e:
            await ctx.send(f"❌ Error downloading files: {e}")

    @commands.hybrid_command(
        name="add_member",
        with_app_command=True,
        description="Add a member to the database.",
    )
    @commands.has_any_role("Admin")
    async def add_member(self, ctx, member: discord.Member, skillsboost_url: str):
        """Manually add a member to the database"""
        if ctx.interaction:
            await ctx.defer()

        try:
            user_data = db.check_skillsboost_url_exists(skillsboost_url)
            if not user_data:
                return await ctx.send("❌ SkillsBoost profile not found in pre-registered users.")

            existing_user = db.get_user_by_discord_id(str(member.id))
            if existing_user:
                return await ctx.send("✅ User is already verified.")

            if user_data['discord_id']:
                return await ctx.send("❌ This profile is already linked to another Discord account.")

            success, result_message = db.register_discord_user(str(member.id), skillsboost_url)

            if success:
                role = discord.utils.get(ctx.guild.roles, id=VERIFIED_ROLE_ID)
                await member.add_roles(role)

                nickname = user_data['name']
                try:
                    await member.edit(nick=nickname)
                except discord.Forbidden:
                    pass

                await ctx.send(f"✅ {member.mention} added to database as {nickname}")
                print(f"Admin added user: {member.id} ({nickname})")
            else:
                await ctx.send(f"❌ {result_message}")

        except Exception as e:
            print(f"Error in add_member: {e}")
            await ctx.send(f"❌ Error adding member: {e}")

    @commands.hybrid_command(
        name="add_badge",
        with_app_command=True,
        description="Add a badge to a user.",
    )
    @commands.has_any_role("Admin")
    async def add_badge(self, ctx, member: discord.Member, badge_url: str):
        """Manually add a badge to a user"""
        if ctx.interaction:
            await ctx.defer()

        try:
            user_data = db.get_user_by_discord_id(str(member.id))
            if not user_data:
                return await ctx.send(f"❌ {member.display_name} is not verified.")

            if not re.match(BADGE_URL_PATTERN, badge_url):
                return await ctx.send("❌ Invalid badge URL format.")

            profile_url = badge_url.split("/badges")[0]

            if profile_url != user_data['skillsboost_url']:
                return await ctx.send("❌ Badge Profile URL does not match user's registered Profile URL.")

            try:
                response = requests.get(badge_url, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return await ctx.send(f"❌ Error fetching badge: {e}")

            soup = BeautifulSoup(response.text, "html.parser")
            badge_element = soup.find("ql-badge")

            if not badge_element or not badge_element.get("badge"):
                return await ctx.send("❌ Could not fetch badge information. Please check the URL.")

            try:
                badge_data = json.loads(badge_element["badge"])
                badge_title = badge_data.get("title")
                if not badge_title:
                    return await ctx.send("❌ Could not extract badge title from page.")
            except (json.JSONDecodeError, KeyError):
                return await ctx.send("❌ Invalid badge data format.")

            if badge_title not in ALL_BADGES:
                return await ctx.send(f"❌ Badge: {badge_title} is not a valid badge for this program.")

            existing_badges = db.get_user_badges(str(member.id))
            if any(badge['badge_name'] == badge_title for badge in existing_badges):
                return await ctx.send(f"❌ Badge: {badge_title} already exists in user's profile.")

            earned_date = ctx.message.created_at.strftime("%Y-%m-%d")
            success = db.add_badge(str(member.id), badge_title, badge_url, earned_date)

            if not success:
                return await ctx.send("❌ Error saving badge. Please try again.")

            user_badges = db.get_user_badges(str(member.id))
            if len(user_badges) >= len(ALL_BADGES):
                completion_role = discord.utils.get(ctx.guild.roles, id=COMPLETION_ROLE_ID)
                if completion_role:
                    await member.add_roles(completion_role)
                    await ctx.send(f"🎉 Badge: {badge_title} added to {member.mention}! They've completed all badges! 🏆")
                else:
                    await ctx.send(f"✅ Badge: {badge_title} added to {member.mention}")
            else:
                await ctx.send(f"✅ Badge: {badge_title} added to {member.mention}")

            print(f"Admin added badge: {badge_title} for user {user_data['name']} ({member.id})")

        except Exception as e:
            print(f"Error in add_badge: {e}")
            await ctx.send(f"❌ Error adding badge: {e}")


async def setup(client):
    await client.add_cog(Admin(client))
