"""
Utility Cog - General utility commands
"""
import discord
from discord.ext import commands
from database import db


class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx: commands.Context):
        """Check bot latency."""
        await ctx.send(f"🏓 Pong! Latency: {round(self.client.latency * 1000)}ms")

    @commands.hybrid_command(name="status", description="Check bot and API server status.")
    async def status(self, ctx):
        """Check system status."""
        if ctx.interaction:
            await ctx.defer()

        embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.green())
        embed.add_field(
            name="Discord Bot",
            value=f"✅ Online\n🏓 Latency: {round(self.client.latency * 1000)}ms",
            inline=True
        )

        try:
            db_stats = db.get_progress_stats()
            embed.add_field(
                name="Database",
                value=f"✅ Connected\n📊 {db_stats.get('total_users', 0)} users",
                inline=True
            )
        except Exception as e:
            embed.add_field(
                name="Database",
                value=f"❌ Error: {str(e)[:100]}",
                inline=True
            )

        embed.add_field(
            name="Homepage",
            value="✅ Online\n🔗 https://gdg-bcet.netlify.app",
            inline=True
        )

        await ctx.reply(embed=embed)


async def setup(client):
    await client.add_cog(Utility(client))
