"""
Stats Cog - Statistics and leaderboard commands
"""
import discord
from discord.ext import commands
from database import db
from datetime import datetime


class Stats(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(name="leaderboard", description="View the badge leaderboard.")
    async def leaderboard(self, ctx, limit: int = 10):
        """Display badge leaderboard."""
        if ctx.interaction:
            await ctx.defer()
        limit = max(5, min(25, limit))

        df = db.get_all_badges()
        if df.empty:
            return await ctx.send("📊 No badges have been earned yet!")

        grouped = (
            df.groupby(['discord_id', 'name'])
            .agg(
                badge_count=('badge_name', 'count'),
                last_badge_date=('earned_date', 'max')
            )
            .reset_index()
        )

        leaderboard_data = (
            grouped.sort_values(
                by=['badge_count', 'last_badge_date', 'name'],
                ascending=[False, True, True]
            )
            .head(limit)
        )

        embed = discord.Embed(
            title="🏆 Badge Leaderboard",
            color=discord.Color.gold(),
            description="*[View Full Leaderboard](https://gdg-bcet.netlify.app/progress)*"
        )
        medals = ["🥇", "🥈", "🥉"]
        embed.set_footer(text=f"Showing top {len(leaderboard_data)} of {len(df['discord_id'].unique())} participants.")

        for idx, row in enumerate(leaderboard_data.itertuples(index=False), start=1):
            mention = f"<@{row.discord_id}>" if str(row.discord_id).isdigit() else row.name
            if idx <= 3:
                rank = medals[idx - 1]
            else:
                rank = f"{idx}."
            field_title = f"{rank} {row.name}"
            field_value = f"{mention} - {row.badge_count} badges"
            embed.add_field(name=field_title, value=field_value, inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stats", description="View overall program statistics.")
    async def stats(self, ctx):
        """Display program statistics."""
        if ctx.interaction:
            await ctx.defer()

        stats_data = db.get_progress_stats()
        embed = discord.Embed(
            title="📊 Cloud Study Jams 2025 Statistics",
            description="*[View Detailed Stats](https://gdg-bcet.netlify.app/)*",
            color=discord.Color.blue()
        )

        verified = stats_data.get('verified_users', 0)
        completion_rate = round((stats_data.get('completed_users', 0) / verified) * 100, 1) if verified > 0 else 0

        embed.add_field(
            name="👥 Participants",
            value=f"**{stats_data.get('total_users', 0)}** registered\n**{verified}** verified",
            inline=True
        )
        embed.add_field(
            name="🏅 Badges",
            value=f"**{stats_data.get('total_badges', 0)}** earned\n**{len(stats_data.get('badge_distribution', {}))}** unique",
            inline=True
        )
        embed.add_field(
            name="📈 Progress",
            value=f"**{stats_data.get('completed_users', 0)}** completed\n**{completion_rate}%** completion",
            inline=True
        )

        badge_dist = stats_data.get('badge_distribution', {})
        if badge_dist:
            top_badges = sorted(badge_dist.items(), key=lambda x: x[1], reverse=True)[:5]
            badge_text = "\n".join([f"• {badge}: {count}" for badge, count in top_badges])
            embed.add_field(name="🔥 Most Popular Badges", value=badge_text, inline=False)

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Stats(client))
