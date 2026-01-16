"""Announcement system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import is_admin
from utils.embeds import EmbedTemplates
from typing import Optional


class Announcements(commands.Cog):
    """Commands for creating and managing announcements."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the announcements cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @app_commands.command(name="announce", description="Create an announcement")
    @app_commands.describe(
        channel="Channel to post the announcement in",
        title="Title of the announcement",
        message="Content of the announcement",
        mention_everyone="Whether to mention @everyone (default: False)"
    )
    @is_admin()
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        message: str,
        mention_everyone: bool = False
    ):
        """Create an announcement in a specified channel.
        
        Args:
            interaction: Discord interaction
            channel: Target channel
            title: Announcement title
            message: Announcement message
            mention_everyone: Whether to mention everyone
        """
        # Check bot permissions in target channel
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )
            return
        
        # Create announcement embed
        embed = EmbedTemplates.announcement(title, message, interaction.user)
        
        # Send announcement
        content = "@everyone" if mention_everyone else None
        try:
            await channel.send(content=content, embed=embed)
            
            # Confirm to the user
            confirm_embed = EmbedTemplates.success(
                "Announcement Posted",
                f"Your announcement has been posted in {channel.mention}"
            )
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to post announcement: {str(e)}",
                ephemeral=True
            )
    
    @commands.command(name="announce", help="Create an announcement (prefix command)")
    @commands.has_permissions(administrator=True)
    async def announce_prefix(self, ctx: commands.Context, channel: discord.TextChannel, *, content: str):
        """Prefix command version of announce.
        
        Args:
            ctx: Command context
            channel: Target channel
            content: Announcement content
        """
        # Split into title and message if possible
        parts = content.split('|', 1)
        if len(parts) == 2:
            title, message = parts
            title = title.strip()
            message = message.strip()
        else:
            title = "Announcement"
            message = content.strip()
        
        # Check bot permissions
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send("❌ I don't have permission to send messages in that channel!")
            return
        
        # Create and send announcement
        embed = EmbedTemplates.announcement(title, message, ctx.author)
        try:
            await channel.send(embed=embed)
            await ctx.send(f"✅ Announcement posted in {channel.mention}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send messages in that channel!")
        except Exception as e:
            await ctx.send(f"❌ Failed to post announcement: {str(e)}")


async def setup(bot: commands.Bot):
    """Load the Announcements cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Announcements(bot))
