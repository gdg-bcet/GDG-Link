"""
Errors Cog - Global error handling for commands
"""
import discord
from discord.ext import commands
import asyncio


class Errors(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle general command errors."""
        if isinstance(error, (commands.CommandNotFound, discord.errors.NotFound)):
            pass  # Ignore these errors
        else:
            print(f"Command error: {error}")
            try:
                msg = await ctx.send(f'❌ Error: {str(error)}')
                await asyncio.sleep(5)
                await msg.delete()
            except Exception as e:
                print(f"Error handling command error: {e}")


async def setup(client):
    await client.add_cog(Errors(client))
