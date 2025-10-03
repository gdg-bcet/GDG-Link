"""
Google Cloud Study Jams 2025 - Standalone Discord Bot

This file contains the core logic for the Discord bot and can be run as a
standalone service. It handles all Discord-facing interactions, including
verification, badge submissions, and user commands.
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Import the database system
from database import db

# Load environment variables
load_dotenv()

# --- Bot Configuration ---
BOT_PREFIX = "."
DISCORD_TOKEN = os.getenv("TOKEN")

# --- Discord Bot Setup ---
intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents,
    case_insensitive=True
)


# --- Event Handlers & Logic ---
@client.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    print("=" * 60)
    print("✅ Discord Bot Ready!")
    print(f"🤖 Logged in as: {client.user}")
    print(f"🆔 Bot ID: {client.user.id}")
    print(f"🔗 Connected to {len(client.guilds)} servers")
    print("=" * 60)

    # Load cogs
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            try:
                await client.load_extension(f"cogs.{file[:-3]}")
                print(f"✅ Loaded cog: {file[:-3]}")
            except Exception as e:
                print(f"❌ Failed to load cog {file}: {e}")


# --- Bot Commands ---
@client.hybrid_command(name="reload", description="Reload a cog.")
@commands.has_any_role("Admin")
async def reload(ctx, cog: str):
    try:
        await client.reload_extension(f"cogs.{cog}")
        await ctx.send(f"✅ Reloaded cog: `{cog}`")
    except Exception as e:
        await ctx.send(f"❌ Failed to reload cog `{cog}`: ```{e}```")


# --- Main Execution ---
async def main():
    """Main function to run the Discord bot."""
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables.")
        return

    print("🤖 Starting Discord Bot (Standalone)...")
    try:
        # Test database connection on startup
        stats = db.get_progress_stats()
        print(f"✅ Database connected - {stats.get('total_users', 0)} users, {stats.get('total_badges', 0)} badges")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    async with client:
        await client.start(DISCORD_TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down bot...")
