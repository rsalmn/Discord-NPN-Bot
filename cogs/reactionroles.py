"""Reaction roles system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin
from utils.embeds import EmbedTemplates
from typing import Optional


class ReactionRoles(commands.Cog):
    """Reaction role system - get roles by reacting to messages."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the reaction roles cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction additions for role assignment.
        
        Args:
            payload: Reaction event payload
        """
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a reaction role message
        reaction_role = await db.fetchone(
            "SELECT * FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (payload.message_id, str(payload.emoji))
        )
        
        if not reaction_role:
            return
        
        # Get guild and member
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        # Get role
        role = guild.get_role(reaction_role['role_id'])
        if not role:
            return
        
        # Add role to member
        try:
            await member.add_roles(role, reason="Reaction role")
        except discord.Forbidden:
            pass
        except Exception:
            pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle reaction removals for role removal.
        
        Args:
            payload: Reaction event payload
        """
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a reaction role message
        reaction_role = await db.fetchone(
            "SELECT * FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (payload.message_id, str(payload.emoji))
        )
        
        if not reaction_role:
            return
        
        # Get guild and member
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        # Get role
        role = guild.get_role(reaction_role['role_id'])
        if not role:
            return
        
        # Remove role from member
        try:
            await member.remove_roles(role, reason="Reaction role removed")
        except discord.Forbidden:
            pass
        except Exception:
            pass
    
    @app_commands.command(name="reactionrole", description="Create a reaction role")
    @app_commands.describe(
        message_id="ID of the message to add reaction role to",
        emoji="Emoji to react with",
        role="Role to assign"
    )
    @is_admin()
    async def create_reaction_role(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        """Create a reaction role.
        
        Args:
            interaction: Discord interaction
            message_id: Message ID to add reaction to
            emoji: Emoji for the reaction
            role: Role to assign
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
        
        # Check if role is higher than bot's highest role
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(
                "❌ That role is higher than or equal to my highest role! I cannot assign it.",
                ephemeral=True
            )
            return
        
        # Try to fetch the message
        message = None
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(msg_id)
                break
            except:
                continue
        
        if not message:
            await interaction.response.send_message(
                "❌ Could not find message with that ID!",
                ephemeral=True
            )
            return
        
        # Add reaction to message
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Invalid emoji or unable to add reaction!",
                ephemeral=True
            )
            return
        
        # Store in database
        await db.execute(
            "INSERT OR REPLACE INTO reaction_roles (message_id, emoji, role_id, guild_id) VALUES (?, ?, ?, ?)",
            (msg_id, str(emoji), role.id, interaction.guild.id)
        )
        
        # Confirm
        embed = EmbedTemplates.success(
            "Reaction Role Created",
            f"Users who react with {emoji} will receive the {role.mention} role.\n\n"
            f"**Message:** [Jump to message]({message.jump_url})"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="removereactionrole", description="Remove a reaction role")
    @app_commands.describe(
        message_id="ID of the message",
        emoji="Emoji to remove"
    )
    @is_admin()
    async def remove_reaction_role(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str
    ):
        """Remove a reaction role.
        
        Args:
            interaction: Discord interaction
            message_id: Message ID
            emoji: Emoji to remove
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
        
        # Check if reaction role exists
        reaction_role = await db.fetchone(
            "SELECT * FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (msg_id, str(emoji))
        )
        
        if not reaction_role:
            await interaction.response.send_message(
                "❌ No reaction role found with that message ID and emoji!",
                ephemeral=True
            )
            return
        
        # Remove from database
        await db.execute(
            "DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (msg_id, str(emoji))
        )
        
        # Try to remove reaction from message
        message = None
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(msg_id)
                await message.clear_reaction(emoji)
                break
            except:
                continue
        
        # Confirm
        embed = EmbedTemplates.success(
            "Reaction Role Removed",
            f"The reaction role for {emoji} has been removed."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the ReactionRoles cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(ReactionRoles(bot))
