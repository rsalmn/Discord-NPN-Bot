"""Sticky messages system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin
from utils.embeds import EmbedTemplates


class StickyMessages(commands.Cog):
    """Sticky messages that auto-repost when other messages are sent."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the sticky messages cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages to repost sticky messages.
        
        Args:
            message: The message sent
        """
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        # Check if channel has a sticky message
        sticky = await db.fetchone(
            "SELECT * FROM sticky_messages WHERE channel_id = ?",
            (message.channel.id,)
        )
        
        if not sticky:
            return
        
        # Delete old sticky message if it exists
        if sticky['last_message_id']:
            try:
                old_message = await message.channel.fetch_message(sticky['last_message_id'])
                await old_message.delete()
            except:
                pass
        
        # Send new sticky message
        try:
            new_sticky = await message.channel.send(sticky['content'])
            
            # Update database with new message ID
            await db.execute(
                "UPDATE sticky_messages SET last_message_id = ? WHERE channel_id = ?",
                (new_sticky.id, message.channel.id)
            )
        except:
            pass
    
    @app_commands.command(name="sticky", description="Set a sticky message in the current channel")
    @app_commands.describe(message="The message to make sticky")
    @is_admin()
    async def set_sticky(self, interaction: discord.Interaction, message: str):
        """Set a sticky message in the current channel.
        
        Args:
            interaction: Discord interaction
            message: Message content
        """
        channel = interaction.channel
        
        # Check if sticky already exists
        existing = await db.fetchone(
            "SELECT * FROM sticky_messages WHERE channel_id = ?",
            (channel.id,)
        )
        
        if existing:
            # Update existing
            await db.execute(
                "UPDATE sticky_messages SET content = ? WHERE channel_id = ?",
                (message, channel.id)
            )
        else:
            # Insert new
            await db.execute(
                "INSERT INTO sticky_messages (channel_id, guild_id, content) VALUES (?, ?, ?)",
                (channel.id, interaction.guild.id, message)
            )
        
        # Send the sticky message
        sticky_msg = await channel.send(message)
        
        # Update last message ID
        await db.execute(
            "UPDATE sticky_messages SET last_message_id = ? WHERE channel_id = ?",
            (sticky_msg.id, channel.id)
        )
        
        # Confirm to user
        embed = EmbedTemplates.success(
            "Sticky Message Set",
            f"The sticky message has been set in {channel.mention}\n\n"
            f"It will automatically repost when other messages are sent."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unsticky", description="Remove the sticky message from the current channel")
    @is_admin()
    async def remove_sticky(self, interaction: discord.Interaction):
        """Remove sticky message from the current channel.
        
        Args:
            interaction: Discord interaction
        """
        channel = interaction.channel
        
        # Get sticky message
        sticky = await db.fetchone(
            "SELECT * FROM sticky_messages WHERE channel_id = ?",
            (channel.id,)
        )
        
        if not sticky:
            await interaction.response.send_message(
                "❌ There is no sticky message in this channel!",
                ephemeral=True
            )
            return
        
        # Delete the sticky message if it exists
        if sticky['last_message_id']:
            try:
                message = await channel.fetch_message(sticky['last_message_id'])
                await message.delete()
            except:
                pass
        
        # Remove from database
        await db.execute(
            "DELETE FROM sticky_messages WHERE channel_id = ?",
            (channel.id,)
        )
        
        # Confirm
        embed = EmbedTemplates.success(
            "Sticky Message Removed",
            f"The sticky message has been removed from {channel.mention}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the StickyMessages cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(StickyMessages(bot))
