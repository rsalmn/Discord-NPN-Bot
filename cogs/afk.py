"""AFK (Away From Keyboard) system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.embeds import EmbedTemplates
from datetime import datetime
from typing import Optional


class AFK(commands.Cog):
    """AFK system for users."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the AFK cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle AFK status on messages.
        
        Args:
            message: The message sent
        """
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id
        user_id = message.author.id
        
        # Check if user is AFK
        afk_status = await db.fetchone(
            "SELECT * FROM afk_users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        
        if afk_status:
            # Remove AFK status
            await db.execute(
                "DELETE FROM afk_users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            
            # Try to remove [AFK] from nickname
            if message.author.nick and "[AFK]" in message.author.nick:
                try:
                    new_nick = message.author.nick.replace("[AFK]", "").strip()
                    await message.author.edit(nick=new_nick if new_nick else None)
                except:
                    pass
            
            # Notify user
            try:
                await message.channel.send(
                    f"👋 Welcome back {message.author.mention}! I removed your AFK status.",
                    delete_after=10
                )
            except:
                pass
        
        # Check if message mentions any AFK users
        for mention in message.mentions:
            if mention.bot:
                continue
            
            afk_data = await db.fetchone(
                "SELECT * FROM afk_users WHERE user_id = ? AND guild_id = ?",
                (mention.id, guild_id)
            )
            
            if afk_data:
                try:
                    await message.channel.send(
                        f"💤 {mention.display_name} is currently AFK: {afk_data['reason']}",
                        delete_after=15
                    )
                except:
                    pass
    
    @app_commands.command(name="afk", description="Set your AFK status")
    @app_commands.describe(reason="Reason for being AFK")
    async def set_afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        """Set AFK status.
        
        Args:
            interaction: Discord interaction
            reason: Reason for being AFK
        """
        user = interaction.user
        guild_id = interaction.guild.id
        
        # Store AFK status
        await db.execute(
            "INSERT OR REPLACE INTO afk_users (user_id, guild_id, reason) VALUES (?, ?, ?)",
            (user.id, guild_id, reason)
        )
        
        # Try to add [AFK] to nickname
        try:
            current_nick = user.nick or user.name
            if "[AFK]" not in current_nick:
                new_nick = f"[AFK] {current_nick}"
                # Discord nickname limit is 32 characters
                if len(new_nick) <= 32:
                    await user.edit(nick=new_nick)
        except:
            pass
        
        # Confirm
        embed = EmbedTemplates.success(
            "AFK Status Set",
            f"Your AFK status has been set.\n\n**Reason:** {reason}\n\n"
            f"Your AFK status will be removed when you send a message."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="removeafk", description="Remove your AFK status")
    async def remove_afk(self, interaction: discord.Interaction):
        """Manually remove AFK status.
        
        Args:
            interaction: Discord interaction
        """
        user = interaction.user
        guild_id = interaction.guild.id
        
        # Check if user is AFK
        afk_status = await db.fetchone(
            "SELECT * FROM afk_users WHERE user_id = ? AND guild_id = ?",
            (user.id, guild_id)
        )
        
        if not afk_status:
            await interaction.response.send_message(
                "❌ You don't have an AFK status set!",
                ephemeral=True
            )
            return
        
        # Remove AFK status
        await db.execute(
            "DELETE FROM afk_users WHERE user_id = ? AND guild_id = ?",
            (user.id, guild_id)
        )
        
        # Try to remove [AFK] from nickname
        if user.nick and "[AFK]" in user.nick:
            try:
                new_nick = user.nick.replace("[AFK]", "").strip()
                await user.edit(nick=new_nick if new_nick else None)
            except:
                pass
        
        # Confirm
        embed = EmbedTemplates.success(
            "AFK Status Removed",
            "Your AFK status has been removed."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the AFK cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(AFK(bot))
