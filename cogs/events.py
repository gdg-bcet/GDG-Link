"""
Events Cog - Event handlers for message verification and badge submission
"""
import discord
from discord.ext import commands
import json
import requests
import re
from bs4 import BeautifulSoup
from database import db, ALL_BADGES
from config import (
    VERIFICATION_CHANNEL_ID,
    BADGE_SUBMISSION_CHANNELS,
    VERIFIED_ROLE_ID,
    COMPLETION_ROLE_ID,
    BADGE_URL_PATTERN
)


class Events(commands.Cog):
    def __init__(self, client):
        self.client = client

        # Load configuration from config.py
        self.VERIFICATION_CHANNEL_ID = VERIFICATION_CHANNEL_ID
        self.BADGE_SUBMISSION_CHANNELS = BADGE_SUBMISSION_CHANNELS
        self.VERIFIED_ROLE_ID = VERIFIED_ROLE_ID
        self.COMPLETION_ROLE_ID = COMPLETION_ROLE_ID
        self.BADGE_URL_PATTERN = BADGE_URL_PATTERN

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle verification and badge submission messages."""
        if message.author == self.client.user:
            return

        # Profile verification in verification channel
        if message.channel.id == self.VERIFICATION_CHANNEL_ID:
            profile_url = message.content.strip()
            if not profile_url or len(profile_url) > 500:
                return
            if profile_url.startswith("https://www.cloudskillsboost.google/public_profiles/"):
                await self.handle_profile_verification(message)

        # Badge submission in badge submission channels
        elif message.channel.id in self.BADGE_SUBMISSION_CHANNELS:
            url = message.content.split("?")[0].strip()
            if not url or len(url) > 500:
                return
            if re.match(self.BADGE_URL_PATTERN, url):
                await self.handle_badge_submission(message, url)

    async def handle_profile_verification(self, message):
        """Handle profile verification logic using the database."""
        try:
            link = message.content.split("?")[0].rstrip("/")
            user_data = db.check_skillsboost_url_exists(link)
            if not user_data:
                return await message.reply("❌ Your SkillsBoost profile is not pre-registered. Please contact an admin.")

            if db.get_user_by_discord_id(str(message.author.id)):
                return await message.reply("✅ You are already verified.")

            if user_data['discord_id']:
                return await message.reply("❌ This profile is already linked to another Discord account.")

            success, result_message = db.register_discord_user(str(message.author.id), link)
            if success:
                role = discord.utils.get(message.guild.roles, id=self.VERIFIED_ROLE_ID)
                await message.author.add_roles(role)
                try:
                    await message.author.edit(nick=user_data['name'])
                except discord.Forbidden:
                    pass  # Can't change admin/owner nicknames
                await message.add_reaction("✅")
                print(f"✅ User {message.author.id} ({user_data['name']}) verified successfully")
            else:
                await message.reply(f"❌ {result_message}")
        except Exception as e:
            print(f"❌ Error in profile verification: {e}")
            await message.reply("❌ An error occurred during verification.")

    async def handle_badge_submission(self, message, url):
        """Handle badge submission logic using the database."""
        try:
            user_data = db.get_user_by_discord_id(str(message.author.id))
            if not user_data:
                return await message.reply("❌ You are not verified. Please verify your profile first.")

            if url.split("/badges")[0] != user_data['skillsboost_url']:
                return await message.reply("❌ Badge Profile URL does not match your registered Profile URL.")

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
            except requests.RequestException:
                return await message.reply("❌ Could not fetch badge information. Please check the URL and try again.")

            soup = BeautifulSoup(response.text, "html.parser")
            badge_element = soup.find("ql-badge")
            if not badge_element or not badge_element.get("badge"):
                return await message.reply("❌ Could not find badge data on the page.")

            try:
                badge_title = json.loads(badge_element["badge"]).get("title")
                if not badge_title:
                    raise KeyError
            except (json.JSONDecodeError, KeyError):
                return await message.reply("❌ Could not extract badge title.")

            if badge_title not in ALL_BADGES:
                return await message.reply(f"❌ Badge '{badge_title}' is not part of this program.")

            if any(b['badge_name'] == badge_title for b in db.get_user_badges(str(message.author.id))):
                return await message.reply(f"❌ You have already submitted the '{badge_title}' badge.")

            earned_date = message.created_at.strftime("%Y-%m-%d")
            if db.add_badge(str(message.author.id), badge_title, url, earned_date):
                await message.add_reaction("✅")
                print(f"✅ Badge '{badge_title}' added for {user_data['name']}")

                # Check for completion
                if len(db.get_user_badges(str(message.author.id))) >= len(ALL_BADGES):
                    role = discord.utils.get(message.guild.roles, id=self.COMPLETION_ROLE_ID)
                    if role:
                        await message.author.add_roles(role)
                        await message.reply(f"🎉 Congratulations! You've completed all {len(ALL_BADGES)} badges! 🏆")
            else:
                await message.reply("❌ Error saving badge to the database.")
        except Exception as e:
            print(f"❌ Error in badge submission: {e}")
            await message.reply("❌ An unexpected error occurred.")


async def setup(client):
    await client.add_cog(Events(client))
