"""Welcome and leave message system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin
from utils.embeds import EmbedTemplates
from typing import Optional


class Welcome(commands.Cog):
    """Welcome and leave message system."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the welcome cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join events.
        
        Args:
            member: The member who joined
        """
        guild = member.guild
        config = await db.get_guild_config(guild.id)
        
        if not config or not config.get('welcome_channel_id'):
            return
        
        channel = guild.get_channel(config['welcome_channel_id'])
        if not channel:
            return
        
        # Get custom message or use default
        message = config.get('welcome_message') or f"Welcome {member.mention} to **{guild.name}**! 👋"
        
        # Replace placeholders
        message = message.replace('{user}', member.mention)
        message = message.replace('{username}', member.name)
        message = message.replace('{server}', guild.name)
        message = message.replace('{membercount}', str(guild.member_count))
        
        # Create embed
        embed = discord.Embed(
            title="👋 Welcome!",
            description=message,
            color=0x00FF00
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{guild.member_count}")
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leave events.
        
        Args:
            member: The member who left
        """
        guild = member.guild
        config = await db.get_guild_config(guild.id)
        
        if not config or not config.get('leave_channel_id'):
            return
        
        channel = guild.get_channel(config['leave_channel_id'])
        if not channel:
            return
        
        # Get custom message or use default
        message = config.get('leave_message') or f"**{member.name}** has left the server. 👋"
        
        # Replace placeholders
        message = message.replace('{username}', member.name)
        message = message.replace('{server}', guild.name)
        message = message.replace('{membercount}', str(guild.member_count))
        
        # Create embed
        embed = discord.Embed(
            title="👋 Goodbye!",
            description=message,
            color=0xFF0000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member count: {guild.member_count}")
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @app_commands.command(name="setwelcome", description="Set welcome message configuration")
    @app_commands.describe(
        channel="Channel to send welcome messages",
        message="Custom welcome message (use {user}, {username}, {server}, {membercount})"
    )
    @is_admin()
    async def set_welcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: Optional[str] = None
    ):
        """Configure welcome messages.
        
        Args:
            interaction: Discord interaction
            channel: Channel for welcome messages
            message: Custom welcome message
        """
        # Check bot permissions
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )
            return
        
        # Update configuration
        await db.set_guild_config(
            interaction.guild.id,
            welcome_channel_id=channel.id,
            welcome_message=message
        )
        
        # Confirm
        embed = EmbedTemplates.success(
            "Welcome Messages Configured",
            f"Welcome messages will be sent to {channel.mention}\n\n"
            f"**Message:** {message or 'Default message'}\n\n"
            f"**Available placeholders:** `{{user}}`, `{{username}}`, `{{server}}`, `{{membercount}}`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="setleave", description="Set leave message configuration")
    @app_commands.describe(
        channel="Channel to send leave messages",
        message="Custom leave message (use {username}, {server}, {membercount})"
    )
    @is_admin()
    async def set_leave(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: Optional[str] = None
    ):
        """Configure leave messages.
        
        Args:
            interaction: Discord interaction
            channel: Channel for leave messages
            message: Custom leave message
        """
        # Check bot permissions
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )
            return
        
        # Update configuration
        await db.set_guild_config(
            interaction.guild.id,
            leave_channel_id=channel.id,
            leave_message=message
        )
        
        # Confirm
        embed = EmbedTemplates.success(
            "Leave Messages Configured",
            f"Leave messages will be sent to {channel.mention}\n\n"
            f"**Message:** {message or 'Default message'}\n\n"
            f"**Available placeholders:** `{{username}}`, `{{server}}`, `{{membercount}}`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="testwelcome", description="Test the welcome message")
    @is_admin()
    async def test_welcome(self, interaction: discord.Interaction):
        """Test the welcome message configuration.
        
        Args:
            interaction: Discord interaction
        """
        await interaction.response.defer(ephemeral=True)
        await self.on_member_join(interaction.user)
        await interaction.followup.send("✅ Sent test welcome message!", ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the Welcome cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Welcome(bot))
