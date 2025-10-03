"""
Integrated Discord Bot + FastAPI Server - Production Runner

This file runs both the Discord bot (from bot.py) and the FastAPI server
(from api_database.py) concurrently in a single process for deployment.
"""

import asyncio
import threading
import uvicorn
from dotenv import load_dotenv

# Import the FastAPI app instance
from api_database import app as fastapi_app

# Import the Discord client instance and token from the bot file
from bot import client as discord_bot, DISCORD_TOKEN

# Import database for startup check
from database import db

# Import configuration
from config import FASTAPI_HOST, FASTAPI_PORT

# Load environment variables
load_dotenv()


def run_fastapi():
    """Synchronous function to run the Uvicorn server."""
    print("🚀 Starting FastAPI Server...")
    print(f"📚 FastAPI docs: http://127.0.0.1:{FASTAPI_PORT}/docs")
    print(f"📘 FastAPI ReDoc: http://127.0.0.1:{FASTAPI_PORT}/redoc")
    uvicorn.run(
        fastapi_app,
        host=FASTAPI_HOST,
        port=FASTAPI_PORT,
        log_level="info",
        access_log=False  # Reduce noise in logs
    )


async def main():
    """Main async function to start both services."""
    print("=" * 70)
    print("🚀 Initializing Integrated Discord Bot + FastAPI Server...")
    print("=" * 70)

    # Test database connection on startup
    try:
        stats = db.get_progress_stats()
        print(f"✅ Database connected - {stats.get('total_users', 0)} users, {stats.get('total_badges', 0)} badges")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration and try again.")
        return

    # Run FastAPI in a separate, daemonized thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()

    # Give FastAPI a moment to initialize
    await asyncio.sleep(2)
    print("✅ FastAPI server is running in the background.")

    # Start the Discord bot (this is an async, blocking call)
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables. Bot cannot start.")
        return

    async with discord_bot:
        await discord_bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down servers...")
    finally:
        print("✅ Cleanup complete. Goodbye!")
