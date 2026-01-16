"""Ticket system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin, is_mod
from utils.embeds import EmbedTemplates
from datetime import datetime
from typing import Optional


class Tickets(commands.Cog):
    """Ticket system for user support."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the tickets cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @app_commands.command(name="ticket", description="Create a new support ticket")
    @app_commands.describe(reason="Reason for opening the ticket")
    async def create_ticket(self, interaction: discord.Interaction, reason: str = "No reason provided"):
        """Create a new support ticket.
        
        Args:
            interaction: Discord interaction
            reason: Reason for the ticket
        """
        guild = interaction.guild
        user = interaction.user
        
        # Check if user already has an open ticket
        existing_ticket = await db.fetchone(
            "SELECT channel_id FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'open'",
            (guild.id, user.id)
        )
        
        if existing_ticket:
            channel = guild.get_channel(existing_ticket['channel_id'])
            if channel:
                await interaction.response.send_message(
                    f"❌ You already have an open ticket: {channel.mention}",
                    ephemeral=True
                )
                return
        
        # Create ticket channel
        try:
            # Find or create tickets category
            category = discord.utils.get(guild.categories, name="Tickets")
            if not category:
                category = await guild.create_category("Tickets")
            
            # Create channel with proper permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            # Add permissions for admins
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            channel_name = f"ticket-{user.name}-{user.discriminator}"
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
            
            # Store ticket in database
            await db.execute(
                "INSERT INTO tickets (guild_id, channel_id, user_id, status) VALUES (?, ?, ?, 'open')",
                (guild.id, channel.id, user.id)
            )
            
            # Send initial message in ticket
            embed = discord.Embed(
                title="🎫 Support Ticket",
                description=(
                    f"**Opened by:** {user.mention}\n"
                    f"**Reason:** {reason}\n\n"
                    f"Our staff team will be with you shortly!\n"
                    f"To close this ticket, use `/closeticket`"
                ),
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Ticket for {user.display_name}", icon_url=user.display_avatar.url)
            
            await channel.send(content=user.mention, embed=embed)
            
            # Confirm to user
            await interaction.response.send_message(
                f"✅ Ticket created! {channel.mention}",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create channels!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create ticket: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="closeticket", description="Close a support ticket")
    @app_commands.describe(reason="Reason for closing the ticket")
    async def close_ticket(self, interaction: discord.Interaction, reason: str = "No reason provided"):
        """Close a support ticket.
        
        Args:
            interaction: Discord interaction
            reason: Reason for closing
        """
        channel = interaction.channel
        
        # Check if this is a ticket channel
        ticket = await db.fetchone(
            "SELECT * FROM tickets WHERE channel_id = ? AND status = 'open'",
            (channel.id,)
        )
        
        if not ticket:
            await interaction.response.send_message(
                "❌ This is not an active ticket channel!",
                ephemeral=True
            )
            return
        
        # Check permissions (ticket owner or admin)
        user = interaction.user
        if ticket['user_id'] != user.id and not user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You don't have permission to close this ticket!",
                ephemeral=True
            )
            return
        
        # Create transcript embed
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=(
                f"**Closed by:** {user.mention}\n"
                f"**Reason:** {reason}\n\n"
                f"This channel will be deleted in 10 seconds."
            ),
            color=0xFF0000,
            timestamp=datetime.utcnow()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Update database
        await db.execute(
            "UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE channel_id = ?",
            (channel.id,)
        )
        
        # Delete channel after delay
        await discord.utils.sleep_until(datetime.utcnow())
        import asyncio
        await asyncio.sleep(10)
        try:
            await channel.delete(reason=f"Ticket closed by {user.name}: {reason}")
        except:
            pass
    
    @commands.command(name="ticket", help="Create a support ticket")
    async def ticket_prefix(self, ctx: commands.Context, *, reason: str = "No reason provided"):
        """Prefix command to create a ticket.
        
        Args:
            ctx: Command context
            reason: Reason for the ticket
        """
        # Reuse the slash command logic
        class FakeInteraction:
            def __init__(self, ctx):
                self.guild = ctx.guild
                self.user = ctx.author
                self.response_sent = False
                self.ctx = ctx
            
            class Response:
                def __init__(self, ctx):
                    self.ctx = ctx
                
                async def send_message(self, content=None, embed=None, ephemeral=False):
                    if embed:
                        await self.ctx.send(embed=embed)
                    else:
                        await self.ctx.send(content)
            
            @property
            def response(self):
                return self.Response(self.ctx)
        
        fake_interaction = FakeInteraction(ctx)
        await self.create_ticket(fake_interaction, reason)


async def setup(bot: commands.Bot):
    """Load the Tickets cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Tickets(bot))
