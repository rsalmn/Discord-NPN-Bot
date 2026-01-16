"""Giveaway system cog."""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.database import db
from utils.checks import is_admin, is_mod
from utils.embeds import EmbedTemplates
from datetime import datetime, timedelta
import random
from typing import Optional


class Giveaways(commands.Cog):
    """Giveaway system for hosting giveaways."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the giveaways cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.check_giveaways.start()
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_giveaways.cancel()
    
    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Check for ended giveaways and select winners."""
        current_time = datetime.utcnow()
        
        # Get all active giveaways
        giveaways = await db.fetchall(
            "SELECT * FROM giveaways WHERE ended = 0 AND end_time <= ?",
            (current_time,)
        )
        
        for giveaway in giveaways:
            await self._end_giveaway(giveaway)
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        """Wait for bot to be ready before starting task."""
        await self.bot.wait_until_ready()
    
    async def _end_giveaway(self, giveaway: dict):
        """End a giveaway and select winners.
        
        Args:
            giveaway: Giveaway data from database
        """
        try:
            guild = self.bot.get_guild(giveaway['guild_id'])
            if not guild:
                return
            
            channel = guild.get_channel(giveaway['channel_id'])
            if not channel:
                return
            
            message = await channel.fetch_message(giveaway['message_id'])
            if not message:
                return
            
            # Get reaction users
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            if not reaction:
                await channel.send("❌ No one entered the giveaway!")
                await db.execute(
                    "UPDATE giveaways SET ended = 1 WHERE giveaway_id = ?",
                    (giveaway['giveaway_id'],)
                )
                return
            
            users = []
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
            
            if not users:
                await channel.send("❌ No valid entries for the giveaway!")
                await db.execute(
                    "UPDATE giveaways SET ended = 1 WHERE giveaway_id = ?",
                    (giveaway['giveaway_id'],)
                )
                return
            
            # Select winners
            winners_count = min(giveaway['winners_count'], len(users))
            winners = random.sample(users, winners_count)
            
            # Announce winners
            winners_mention = ", ".join([winner.mention for winner in winners])
            embed = discord.Embed(
                title="🎉 Giveaway Ended! 🎉",
                description=(
                    f"**Prize:** {giveaway['prize']}\n\n"
                    f"**Winner(s):** {winners_mention}\n\n"
                    f"Congratulations! 🎊"
                ),
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            
            await channel.send(content=winners_mention, embed=embed)
            
            # Update database
            await db.execute(
                "UPDATE giveaways SET ended = 1 WHERE giveaway_id = ?",
                (giveaway['giveaway_id'],)
            )
            
            # Edit original message
            original_embed = message.embeds[0]
            original_embed.color = 0xFF0000
            original_embed.title = "🎉 GIVEAWAY ENDED 🎉"
            await message.edit(embed=original_embed)
            
        except Exception as e:
            print(f"Error ending giveaway: {e}")
    
    @app_commands.command(name="gstart", description="Start a giveaway")
    @app_commands.describe(
        duration="Duration in minutes",
        winners="Number of winners",
        prize="Giveaway prize"
    )
    @is_admin()
    async def start_giveaway(
        self,
        interaction: discord.Interaction,
        duration: int,
        winners: int,
        prize: str
    ):
        """Start a new giveaway.
        
        Args:
            interaction: Discord interaction
            duration: Duration in minutes
            winners: Number of winners
            prize: Prize description
        """
        if duration < 1:
            await interaction.response.send_message(
                "❌ Duration must be at least 1 minute!",
                ephemeral=True
            )
            return
        
        if winners < 1:
            await interaction.response.send_message(
                "❌ Must have at least 1 winner!",
                ephemeral=True
            )
            return
        
        # Calculate end time
        end_time = datetime.utcnow() + timedelta(minutes=duration)
        
        # Create giveaway embed
        embed = EmbedTemplates.giveaway(prize, end_time, interaction.user)
        
        # Send giveaway message
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Add reaction
        await message.add_reaction("🎉")
        
        # Store in database
        await db.execute(
            """INSERT INTO giveaways 
               (guild_id, channel_id, message_id, prize, winners_count, end_time, host_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (interaction.guild.id, interaction.channel.id, message.id, 
             prize, winners, end_time, interaction.user.id)
        )
    
    @app_commands.command(name="gend", description="End a giveaway early")
    @app_commands.describe(message_id="Message ID of the giveaway")
    @is_admin()
    async def end_giveaway_early(self, interaction: discord.Interaction, message_id: str):
        """End a giveaway early.
        
        Args:
            interaction: Discord interaction
            message_id: ID of the giveaway message
        """
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID!",
                ephemeral=True
            )
            return
        
        # Get giveaway from database
        giveaway = await db.fetchone(
            "SELECT * FROM giveaways WHERE message_id = ? AND ended = 0",
            (msg_id,)
        )
        
        if not giveaway:
            await interaction.response.send_message(
                "❌ No active giveaway found with that message ID!",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message("⏳ Ending giveaway...", ephemeral=True)
        await self._end_giveaway(giveaway)
    
    @app_commands.command(name="greroll", description="Reroll a giveaway winner")
    @app_commands.describe(message_id="Message ID of the giveaway")
    @is_admin()
    async def reroll_giveaway(self, interaction: discord.Interaction, message_id: str):
        """Reroll a giveaway to select new winners.
        
        Args:
            interaction: Discord interaction
            message_id: ID of the giveaway message
        """
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID!",
                ephemeral=True
            )
            return
        
        # Get giveaway from database
        giveaway = await db.fetchone(
            "SELECT * FROM giveaways WHERE message_id = ? AND ended = 1",
            (msg_id,)
        )
        
        if not giveaway:
            await interaction.response.send_message(
                "❌ No ended giveaway found with that message ID!",
                ephemeral=True
            )
            return
        
        try:
            channel = interaction.guild.get_channel(giveaway['channel_id'])
            message = await channel.fetch_message(msg_id)
            
            # Get reaction users
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            if not reaction:
                await interaction.response.send_message(
                    "❌ No entries found!",
                    ephemeral=True
                )
                return
            
            users = []
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
            
            if not users:
                await interaction.response.send_message(
                    "❌ No valid entries!",
                    ephemeral=True
                )
                return
            
            # Select new winners
            winners_count = min(giveaway['winners_count'], len(users))
            winners = random.sample(users, winners_count)
            
            # Announce new winners
            winners_mention = ", ".join([winner.mention for winner in winners])
            embed = discord.Embed(
                title="🎉 Giveaway Rerolled! 🎉",
                description=(
                    f"**Prize:** {giveaway['prize']}\n\n"
                    f"**New Winner(s):** {winners_mention}\n\n"
                    f"Congratulations! 🎊"
                ),
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(content=winners_mention, embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error rerolling giveaway: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Load the Giveaways cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Giveaways(bot))
