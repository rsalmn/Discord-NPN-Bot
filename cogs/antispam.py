"""Anti-spam system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin, is_mod
from utils.embeds import EmbedTemplates
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


class AntiSpam(commands.Cog):
    """Anti-spam and auto-moderation system."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the anti-spam cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        # Track messages per user per guild
        self.message_history = defaultdict(lambda: defaultdict(list))
        # Track duplicate messages
        self.last_messages = defaultdict(dict)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages for spam.
        
        Args:
            message: The message to check
        """
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        # Ignore admins
        if message.author.guild_permissions.administrator:
            return
        
        guild_id = message.guild.id
        user_id = message.author.id
        
        # Get anti-spam config
        config = await db.fetchone(
            "SELECT * FROM antispam_config WHERE guild_id = ?",
            (guild_id,)
        )
        
        if not config or not config['enabled']:
            return
        
        max_messages = config['max_messages']
        time_window = config['time_window']
        action = config['action']
        
        current_time = datetime.utcnow()
        
        # Clean old messages from history
        self.message_history[guild_id][user_id] = [
            msg_time for msg_time in self.message_history[guild_id][user_id]
            if current_time - msg_time < timedelta(seconds=time_window)
        ]
        
        # Add current message
        self.message_history[guild_id][user_id].append(current_time)
        
        # Check for spam
        message_count = len(self.message_history[guild_id][user_id])
        
        if message_count > max_messages:
            await self._take_action(message, action, "Spam detected")
            # Clear history after action
            self.message_history[guild_id][user_id].clear()
        
        # Check for duplicate messages
        last_msg = self.last_messages[guild_id].get(user_id)
        if last_msg and last_msg == message.content:
            await self._take_action(message, action, "Duplicate message spam")
        
        self.last_messages[guild_id][user_id] = message.content
    
    async def _take_action(self, message: discord.Message, action: str, reason: str):
        """Take moderation action against spammer.
        
        Args:
            message: The spam message
            action: Action to take (warn, mute, kick)
            reason: Reason for the action
        """
        try:
            # Delete the spam message
            await message.delete()
        except:
            pass
        
        user = message.author
        guild = message.guild
        
        if action == "warn":
            # Send warning
            try:
                await message.channel.send(
                    f"⚠️ {user.mention} Warning: {reason}",
                    delete_after=10
                )
            except:
                pass
        
        elif action == "mute":
            # Try to timeout the user (requires timeout permission)
            try:
                await user.timeout(timedelta(minutes=5), reason=reason)
                await message.channel.send(
                    f"🔇 {user.mention} has been timed out for 5 minutes: {reason}",
                    delete_after=10
                )
            except:
                pass
        
        elif action == "kick":
            # Try to kick the user
            try:
                await user.kick(reason=reason)
                await message.channel.send(
                    f"👢 {user.mention} has been kicked: {reason}",
                    delete_after=10
                )
            except:
                pass
    
    @app_commands.command(name="antispam", description="Configure anti-spam settings")
    @app_commands.describe(
        enabled="Enable or disable anti-spam",
        max_messages="Maximum messages allowed in time window",
        time_window="Time window in seconds",
        action="Action to take (warn, mute, kick)"
    )
    @is_admin()
    async def configure_antispam(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        max_messages: int = 5,
        time_window: int = 10,
        action: str = "warn"
    ):
        """Configure anti-spam settings.
        
        Args:
            interaction: Discord interaction
            enabled: Enable/disable anti-spam
            max_messages: Max messages in time window
            time_window: Time window in seconds
            action: Moderation action
        """
        # Validate action
        if action not in ["warn", "mute", "kick"]:
            await interaction.response.send_message(
                "❌ Invalid action! Must be: warn, mute, or kick",
                ephemeral=True
            )
            return
        
        # Check if config exists
        existing = await db.fetchone(
            "SELECT guild_id FROM antispam_config WHERE guild_id = ?",
            (interaction.guild.id,)
        )
        
        if existing:
            # Update
            await db.execute(
                """UPDATE antispam_config 
                   SET enabled = ?, max_messages = ?, time_window = ?, action = ?
                   WHERE guild_id = ?""",
                (1 if enabled else 0, max_messages, time_window, action, interaction.guild.id)
            )
        else:
            # Insert
            await db.execute(
                """INSERT INTO antispam_config (guild_id, enabled, max_messages, time_window, action)
                   VALUES (?, ?, ?, ?, ?)""",
                (interaction.guild.id, 1 if enabled else 0, max_messages, time_window, action)
            )
        
        # Confirm
        status = "enabled" if enabled else "disabled"
        embed = EmbedTemplates.success(
            "Anti-Spam Configured",
            f"Anti-spam has been **{status}**\n\n"
            f"**Settings:**\n"
            f"• Max messages: {max_messages}\n"
            f"• Time window: {time_window} seconds\n"
            f"• Action: {action}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the AntiSpam cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(AntiSpam(bot))
