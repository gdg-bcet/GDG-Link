"""
Profile Cog - Profile and badge viewing commands
"""
import discord
from discord.ext import commands
from discord import app_commands
from database import db, ALL_BADGES


class Profile(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(name="profile", description="View your profile and badge progress.")
    async def profile(self, ctx, user: discord.Member = None):
        """View user profile and badge progress."""
        if ctx.interaction:
            await ctx.defer()

        target_user = user or ctx.author

        user_data = db.get_user_by_discord_id(str(target_user.id))
        if not user_data:
            msg = "You are not verified." if target_user == ctx.author else f"{target_user.display_name} is not verified."
            return await ctx.send(f"❌ {msg}")

        badges = db.get_user_badges(str(target_user.id))
        earned_count, total_badges = len(badges), len(ALL_BADGES)

        embed = discord.Embed(
            title=f"🏆 {user_data['name']}'s Profile",
            description=f"*[View Complete Profile](https://gdg-bcet.netlify.app/profile/{target_user.id})*",
            color=discord.Color.gold() if earned_count == total_badges else discord.Color.blue()
        )
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        embed.add_field(
            name="📊 Progress",
            value=f"{earned_count}/{total_badges} badges ({round((earned_count/total_badges)*100, 1)}%)",
            inline=True
        )

        if earned_count == total_badges:
            embed.add_field(name="🎉 Status", value="**COMPLETED!** 🏆", inline=False)

        if badges:
            recent_badges = sorted(badges, key=lambda x: x['earned_date'], reverse=True)[:5]
            badge_list = "\n".join([f"• {b['badge_name']}" for b in recent_badges])
            embed.add_field(name=f"🏅 Recent Badges ({min(5, len(badges))})", value=badge_list, inline=False)

        embed.set_footer(text=f"Last updated on {user_data['updated_at'].strftime('%B %d, %Y')}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="badges",
        with_app_command=True,
        description="Show all badges of a user.",
    )
    @app_commands.describe(
        member="The member to show the badges of.",
    )
    async def badges(self, ctx, member: discord.Member = None):
        """Show user's badges"""
        if ctx.interaction:
            await ctx.defer()

        try:
            target_user = member or ctx.author

            user_data = db.get_user_by_discord_id(str(target_user.id))
            if not user_data:
                if target_user == ctx.author:
                    return await ctx.send("❌ You are not verified.")
                else:
                    return await ctx.send(f"❌ {target_user.display_name} is not verified.")

            badges = db.get_user_badges(str(target_user.id))
            total_badges = len(ALL_BADGES)
            earned_count = len(badges)

            embed = discord.Embed(
                title=f"🏆 {user_data['name']}'s Badges",
                color=discord.Color.gold() if earned_count == total_badges else discord.Color.blue()
            )

            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
            embed.set_footer(text=f"Badge count: {earned_count}/{total_badges}")
            embed.timestamp = ctx.message.created_at

            if earned_count == total_badges:
                embed.add_field(
                    name="🎉 Status",
                    value="**COMPLETED!** 🏆",
                    inline=False
                )

            if badges:
                sorted_badges = sorted(badges, key=lambda x: x['earned_date'], reverse=True)

                badge_text = ""
                for badge in sorted_badges:
                    badge_text += f"✅ [{badge['badge_name']}]({badge['badge_url']})\n"

                if len(badge_text) > 1024:
                    chunks = [badge_text[i:i+1024] for i in range(0, len(badge_text), 1024)]
                    for i, chunk in enumerate(chunks):
                        embed.add_field(
                            name=f"🏅 Badges (Part {i+1})" if len(chunks) > 1 else "🏅 Earned Badges",
                            value=chunk,
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="🏅 Earned Badges",
                        value=badge_text or "None yet",
                        inline=False
                    )

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error in badges command: {e}")
            await ctx.send(f"❌ Error fetching badges: {e}")


async def setup(client):
    await client.add_cog(Profile(client))
