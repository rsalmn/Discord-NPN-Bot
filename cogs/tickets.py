"""Ticket system cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from utils.checks import is_admin, is_mod
from utils.embeds import EmbedTemplates
from datetime import datetime
from typing import Optional
import json
import asyncio
import logging

# Constants
TICKET_NUMBER_FORMAT = "{:04d}"  # Format for ticket numbers (e.g., 0001, 0002)

logger = logging.getLogger('discord_bot')


class Tickets(commands.Cog):
    """Ticket system for user support."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the tickets cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self._ticket_lock = asyncio.Lock()  # Lock for ticket counter to prevent race conditions
    
    async def _create_ticket_channel(
        self,
        guild: discord.Guild,
        user: discord.Member,
        reason: str = "No reason provided"
    ) -> tuple[Optional[discord.TextChannel], Optional[str]]:
        """Helper method to create a ticket channel.
        
        Args:
            guild: The guild
            user: The user creating the ticket
            reason: Reason for the ticket
            
        Returns:
            Tuple of (channel, error_message). Channel is None if error occurred.
        """
        # Check if user already has an open ticket
        existing_ticket = await db.fetchone(
            "SELECT channel_id FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'open'",
            (guild.id, user.id)
        )
        
        if existing_ticket:
            channel = guild.get_channel(existing_ticket['channel_id'])
            if channel:
                return None, f"❌ You already have an open ticket: {channel.mention}"
        
        # Get ticket configuration
        config = await db.fetchone(
            "SELECT * FROM ticket_config WHERE guild_id = ?",
            (guild.id,)
        )
        
        try:
            # Get or create tickets category
            category = None
            if config and config['category_id']:
                category = guild.get_channel(config['category_id'])
            
            if not category:
                category = discord.utils.get(guild.categories, name="Tickets")
                if not category:
                    category = await guild.create_category("Tickets")
            
            # Get and increment ticket number atomically
            async with self._ticket_lock:
                # Re-fetch config inside lock to ensure we have latest counter
                config = await db.fetchone(
                    "SELECT * FROM ticket_config WHERE guild_id = ?",
                    (guild.id,)
                )
                
                ticket_number = 1
                if config and config['ticket_counter']:
                    ticket_number = config['ticket_counter'] + 1
                
                # Update ticket counter
                if config:
                    await db.execute(
                        "UPDATE ticket_config SET ticket_counter = ? WHERE guild_id = ?",
                        (ticket_number, guild.id)
                    )
                else:
                    await db.execute(
                        "INSERT INTO ticket_config (guild_id, ticket_counter) VALUES (?, ?)",
                        (guild.id, ticket_number)
                    )
            
            # Create channel with proper permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            # Add permissions for support roles if configured
            if config and config['support_role_ids']:
                try:
                    support_role_ids = json.loads(config['support_role_ids'])
                    for role_id in support_role_ids:
                        role = guild.get_role(role_id)
                        if role:
                            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                except (json.JSONDecodeError, TypeError) as e:
                    # If JSON is malformed, log error and skip support roles
                    logger.error(f"Malformed support_role_ids in ticket config for guild {guild.id}: {e}")
            
            # Add permissions for admins (fallback)
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            channel_name = f"ticket-{TICKET_NUMBER_FORMAT.format(ticket_number)}"
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
                    f"**Ticket Number:** #{TICKET_NUMBER_FORMAT.format(ticket_number)}\n"
                    f"**Reason:** {reason}\n\n"
                    f"Our staff team will be with you shortly!\n"
                    f"To close this ticket, use `/closeticket`"
                ),
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Ticket for {user.display_name}", icon_url=user.display_avatar.url)
            
            await channel.send(content=user.mention, embed=embed)
            
            return channel, None
            
        except discord.Forbidden:
            return None, "❌ I don't have permission to create channels!"
        except Exception as e:
            return None, f"❌ Failed to create ticket: {str(e)}"
    
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Add persistent view for ticket buttons
        self.bot.add_view(TicketButton(self))
    
    @app_commands.command(name="ticket_setup", description="Setup a ticket panel in a channel")
    @app_commands.describe(
        channel="The channel to post the ticket panel in",
        title="Title for the ticket panel",
        description="Description for the ticket panel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str = "Support Tickets",
        description: str = "Click the button below to open a support ticket"
    ):
        """Setup a ticket panel in a channel.
        
        Args:
            interaction: Discord interaction
            channel: Target channel
            title: Panel title
            description: Panel description
        """
        try:
            # Create embed for ticket panel
            embed = discord.Embed(
                title=f"🎫 {title}",
                description=description,
                color=0x5865F2
            )
            embed.add_field(
                name="How to create a ticket:",
                value="Click the **Open Ticket** button below to create a private support ticket.",
                inline=False
            )
            embed.set_footer(text=f"Ticket system for {interaction.guild.name}")
            
            # Send the panel with the button
            view = TicketButton(self)
            message = await channel.send(embed=embed, view=view)
            
            # Store panel in database
            await db.execute(
                "INSERT INTO ticket_panels (guild_id, channel_id, message_id, title, description) VALUES (?, ?, ?, ?, ?)",
                (interaction.guild.id, channel.id, message.id, title, description)
            )
            
            await interaction.response.send_message(
                f"✅ Ticket panel created in {channel.mention}!",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to post in that channel!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create ticket panel: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="ticket_config", description="Configure ticket system settings")
    @app_commands.describe(
        category="Category to create tickets in",
        support_roles="Comma-separated list of role names/IDs that can access tickets"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_config(
        self,
        interaction: discord.Interaction,
        category: Optional[discord.CategoryChannel] = None,
        support_roles: Optional[str] = None
    ):
        """Configure ticket system settings.
        
        Args:
            interaction: Discord interaction
            category: Ticket category
            support_roles: Support role names or IDs
        """
        guild = interaction.guild
        
        # Check if config exists
        config = await db.fetchone(
            "SELECT * FROM ticket_config WHERE guild_id = ?",
            (guild.id,)
        )
        
        try:
            # Parse support roles
            role_ids = []
            not_found_roles = []
            if support_roles:
                role_parts = [r.strip() for r in support_roles.split(',')]
                for role_part in role_parts:
                    # Try to find role by ID or name
                    role = None
                    if role_part.isdigit():
                        role = guild.get_role(int(role_part))
                    else:
                        role = discord.utils.get(guild.roles, name=role_part)
                    
                    if role:
                        role_ids.append(role.id)
                    else:
                        not_found_roles.append(role_part)
            
            # Update or insert configuration
            if config:
                updates = []
                params = []
                
                if category:
                    updates.append("category_id = ?")
                    params.append(category.id)
                
                if role_ids:
                    updates.append("support_role_ids = ?")
                    params.append(json.dumps(role_ids))
                
                if updates:
                    params.append(guild.id)
                    await db.execute(
                        f"UPDATE ticket_config SET {', '.join(updates)} WHERE guild_id = ?",
                        tuple(params)
                    )
            else:
                await db.execute(
                    "INSERT INTO ticket_config (guild_id, category_id, support_role_ids, ticket_counter) VALUES (?, ?, ?, 0)",
                    (guild.id, category.id if category else None, json.dumps(role_ids) if role_ids else None)
                )
            
            # Build response message
            response = "✅ Ticket configuration updated!\n\n"
            if category:
                response += f"**Category:** {category.mention}\n"
            if role_ids:
                role_mentions = [f"<@&{role_id}>" for role_id in role_ids]
                response += f"**Support Roles:** {', '.join(role_mentions)}\n"
            if not_found_roles:
                response += f"\n⚠️ Roles not found: {', '.join(not_found_roles)}"
            
            await interaction.response.send_message(response, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to update configuration: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="ticket", description="Create a new support ticket")
    @app_commands.describe(reason="Reason for opening the ticket")
    async def create_ticket(self, interaction: discord.Interaction, reason: str = "No reason provided"):
        """Create a new support ticket (legacy command).
        
        Args:
            interaction: Discord interaction
            reason: Reason for the ticket
        """
        channel, error = await self._create_ticket_channel(
            interaction.guild,
            interaction.user,
            reason
        )
        
        if error:
            await interaction.response.send_message(error, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"✅ Ticket created! {channel.mention}",
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


class TicketButton(discord.ui.View):
    """Persistent view for ticket creation button."""
    
    def __init__(self, cog: Tickets):
        """Initialize the view with persistent timeout.
        
        Args:
            cog: The Tickets cog instance
        """
        super().__init__(timeout=None)
        self.cog = cog
    
    @discord.ui.button(
        label="Open Ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="create_ticket_button"
    )
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle ticket creation button click.
        
        Args:
            interaction: Discord interaction
            button: Button instance
        """
        channel, error = await self.cog._create_ticket_channel(
            interaction.guild,
            interaction.user,
            "Created via ticket panel"
        )
        
        if error:
            await interaction.response.send_message(error, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"✅ Ticket created! {channel.mention}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Load the Tickets cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Tickets(bot))

