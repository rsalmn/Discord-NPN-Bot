"""Permission check decorators and helpers."""
from discord import app_commands
from discord.ext import commands
import discord
from typing import Callable


def is_admin():
    """Check if user has administrator permissions."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


def is_mod():
    """Check if user has moderation permissions (manage messages, kick, ban)."""
    async def predicate(interaction: discord.Interaction) -> bool:
        perms = interaction.user.guild_permissions
        if not (perms.administrator or perms.manage_messages or perms.kick_members):
            await interaction.response.send_message(
                "❌ You need moderation permissions to use this command.",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


def has_permissions(**perms):
    """Check if user has specific permissions."""
    async def predicate(interaction: discord.Interaction) -> bool:
        user_perms = interaction.user.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(user_perms, perm) != value]
        if missing:
            await interaction.response.send_message(
                f"❌ You are missing the following permissions: {', '.join(missing)}",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


# Prefix command checks
def is_admin_prefix():
    """Check if user has administrator permissions (for prefix commands)."""
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You need administrator permissions to use this command.")
            return False
        return True
    return commands.check(predicate)


def is_mod_prefix():
    """Check if user has moderation permissions (for prefix commands)."""
    async def predicate(ctx: commands.Context) -> bool:
        perms = ctx.author.guild_permissions
        if not (perms.administrator or perms.manage_messages or perms.kick_members):
            await ctx.send("❌ You need moderation permissions to use this command.")
            return False
        return True
    return commands.check(predicate)
