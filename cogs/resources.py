"""
Resources Cog - View badge resources and tutorials
"""
import discord
from discord.ext import commands
from discord import app_commands
import json
from database import db


class ResourcesView(discord.ui.View):
    def __init__(self, resources_data, user_badges):
        super().__init__(timeout=180)
        self.resources_data = resources_data
        self.user_badges = user_badges  # Set of completed badge names

        # Create dropdown with badge options (add tick emoji if completed)
        options = []
        for badge_name in resources_data.keys():
            # Add tick emoji if user completed this badge
            display_name = badge_name[:100]
            if badge_name in user_badges:
                # Add animated tick emoji at the start
                display_name = f"✅ {badge_name[:97]}"  # Shorten to fit with emoji

            options.append(
                discord.SelectOption(label=display_name, value=badge_name)
            )

        select = discord.ui.Select(
            placeholder="Select a badge to view resources...",
            options=options,
            custom_id="badge_select"
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_badge = interaction.data["values"][0]
        badge_data = self.resources_data[selected_badge]

        # Create embed with badge info
        embed = discord.Embed(
            title=selected_badge,
            url=badge_data["link"],
            description=badge_data["des"],
            color=discord.Color.from_rgb(255, 255, 255)  # White color
        )
        embed.set_footer(text="Google Cloud Study Jams 2025 | Resources")

        await interaction.response.edit_message(embed=embed, view=self)


class Resources(commands.Cog):
    def __init__(self, client):
        self.client = client
        # Load resources data
        try:
            with open("resources.json", "r", encoding="utf-8") as f:
                self.resources_data = json.load(f)
        except FileNotFoundError:
            self.resources_data = {}
            print("Warning: resources.json not found")

    @app_commands.command(name="resources", description="View badge resources and tutorials")
    async def resources(self, interaction: discord.Interaction):
        """View resources for Google Cloud Study Jams badges"""
        # Defer the response to prevent timeout
        await interaction.response.defer(ephemeral=True)

        if not self.resources_data:
            return await interaction.followup.send(
                "You can check resources at: <#1421165896549928960>",
                ephemeral=True
            )

        # Get user's completed badges from database
        user_badges = set()
        user_data = db.get_user_by_discord_id(str(interaction.user.id))
        if user_data:
            # User is verified, get their badges
            badges = db.get_user_badges(str(interaction.user.id))
            user_badges = {badge['badge_name'] for badge in badges}

        # Create initial embed
        embed = discord.Embed(
            title="📚 Google Cloud Study Jams Resources",
            description="Select a badge from the dropdown below to view tutorials and lab links.",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        embed.set_footer(text="Google Cloud Study Jams 2025")

        # Create view with dropdown (pass user's completed badges)
        view = ResourcesView(self.resources_data, user_badges)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(client):
    await client.add_cog(Resources(client))
