"""Donation management system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin
from utils.embeds import EmbedTemplates
from typing import Optional


class Donations(commands.Cog):
    """Donation tracking and management system."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the donations cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @app_commands.command(name="donation", description="Create a donation announcement")
    @app_commands.describe(
        channel="Channel to post the donation announcement",
        title="Title of the donation announcement",
        content="Content/details of the donation",
        goal="Optional donation goal amount"
    )
    @is_admin()
    async def create_donation(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        content: str,
        goal: Optional[str] = None
    ):
        """Create a donation announcement.
        
        Args:
            interaction: Discord interaction
            channel: Target channel
            title: Donation title
            content: Donation details
            goal: Optional goal amount
        """
        # Check bot permissions
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )
            return
        
        # Create donation embed
        embed = discord.Embed(
            title=f"💰 {title}",
            description=content,
            color=0xFFD700,  # Gold color
            timestamp=interaction.created_at
        )
        
        if goal:
            embed.add_field(name="🎯 Goal", value=goal, inline=False)
        
        embed.set_footer(
            text=f"Posted by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Send donation message
        try:
            message = await channel.send(embed=embed)
            
            # Store in database
            await db.execute(
                """INSERT INTO donations 
                   (guild_id, message_id, channel_id, content)
                   VALUES (?, ?, ?, ?)""",
                (interaction.guild.id, message.id, channel.id, content)
            )
            
            # Confirm to user
            confirm_embed = EmbedTemplates.success(
                "Donation Announcement Posted",
                f"Your donation announcement has been posted in {channel.mention}\n\n"
                f"**Message ID:** `{message.id}` (save this to edit later)"
            )
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to post donation announcement: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="editdonation", description="Edit an existing donation announcement")
    @app_commands.describe(
        message_id="Message ID of the donation announcement",
        title="New title (optional)",
        content="New content",
        goal="New goal amount (optional)"
    )
    @is_admin()
    async def edit_donation(
        self,
        interaction: discord.Interaction,
        message_id: str,
        content: str,
        title: Optional[str] = None,
        goal: Optional[str] = None
    ):
        """Edit an existing donation announcement.
        
        Args:
            interaction: Discord interaction
            message_id: ID of the donation message
            content: New content
            title: New title (optional)
            goal: New goal (optional)
        """
        # Validate message ID
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID!",
                ephemeral=True
            )
            return
        
        # Check if donation exists in database
        donation = await db.fetchone(
            "SELECT * FROM donations WHERE message_id = ?",
            (msg_id,)
        )
        
        if not donation:
            await interaction.response.send_message(
                "❌ No donation announcement found with that message ID!",
                ephemeral=True
            )
            return
        
        # Fetch the message
        try:
            channel = interaction.guild.get_channel(donation['channel_id'])
            if not channel:
                await interaction.response.send_message(
                    "❌ Could not find the channel!",
                    ephemeral=True
                )
                return
            
            message = await channel.fetch_message(msg_id)
            
            # Get original embed
            if not message.embeds:
                await interaction.response.send_message(
                    "❌ Message does not have an embed!",
                    ephemeral=True
                )
                return
            
            original_embed = message.embeds[0]
            
            # Update embed
            if title:
                original_embed.title = f"💰 {title}"
            
            original_embed.description = content
            
            # Update or add goal field
            if goal:
                # Remove existing goal field if present
                for i, field in enumerate(original_embed.fields):
                    if field.name == "🎯 Goal":
                        original_embed.remove_field(i)
                        break
                original_embed.add_field(name="🎯 Goal", value=goal, inline=False)
            
            # Update message
            await message.edit(embed=original_embed)
            
            # Update database
            await db.execute(
                "UPDATE donations SET content = ? WHERE message_id = ?",
                (content, msg_id)
            )
            
            # Confirm
            confirm_embed = EmbedTemplates.success(
                "Donation Updated",
                f"The donation announcement has been updated.\n\n"
                f"[Jump to message]({message.jump_url})"
            )
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
            
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Could not find the message!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to edit that message!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to edit donation: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="listdonations", description="List all donation announcements")
    @is_admin()
    async def list_donations(self, interaction: discord.Interaction):
        """List all donation announcements in the server.
        
        Args:
            interaction: Discord interaction
        """
        donations = await db.fetchall(
            "SELECT * FROM donations WHERE guild_id = ? ORDER BY created_at DESC",
            (interaction.guild.id,)
        )
        
        if not donations:
            await interaction.response.send_message(
                "ℹ️ No donation announcements found in this server.",
                ephemeral=True
            )
            return
        
        # Create embed with donation list
        embed = discord.Embed(
            title="💰 Donation Announcements",
            description="List of all donation announcements in this server",
            color=0xFFD700
        )
        
        for donation in donations[:10]:  # Limit to 10 most recent
            channel = interaction.guild.get_channel(donation['channel_id'])
            channel_name = channel.mention if channel else "Unknown Channel"
            
            content_preview = donation['content'][:50] + "..." if len(donation['content']) > 50 else donation['content']
            
            embed.add_field(
                name=f"ID: {donation['message_id']}",
                value=f"**Channel:** {channel_name}\n**Preview:** {content_preview}",
                inline=False
            )
        
        if len(donations) > 10:
            embed.set_footer(text=f"Showing 10 of {len(donations)} donations")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the Donations cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Donations(bot))
