"""Voting and poll system cog."""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.database import db
from utils.checks import is_admin
from utils.embeds import EmbedTemplates
from datetime import datetime, timedelta
from typing import Optional
import json


class Voting(commands.Cog):
    """Voting and poll system."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the voting cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.check_polls.start()
        # Number emojis for poll options
        self.number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_polls.cancel()
    
    @tasks.loop(seconds=30)
    async def check_polls(self):
        """Check for ended polls and display results."""
        current_time = datetime.utcnow()
        
        # Get all active polls that have ended
        polls = await db.fetchall(
            "SELECT * FROM polls WHERE ended = 0 AND end_time <= ?",
            (current_time,)
        )
        
        for poll in polls:
            await self._end_poll(poll)
    
    @check_polls.before_loop
    async def before_check_polls(self):
        """Wait for bot to be ready before starting task."""
        await self.bot.wait_until_ready()
    
    async def _end_poll(self, poll: dict):
        """End a poll and display results.
        
        Args:
            poll: Poll data from database
        """
        try:
            guild = self.bot.get_guild(poll['guild_id'])
            if not guild:
                return
            
            channel = guild.get_channel(poll['channel_id'])
            if not channel:
                return
            
            # Get vote counts
            options = json.loads(poll['options'])
            vote_counts = [0] * len(options)
            
            votes = await db.fetchall(
                "SELECT option_index FROM poll_votes WHERE poll_id = ?",
                (poll['poll_id'],)
            )
            
            for vote in votes:
                vote_counts[vote['option_index']] += 1
            
            # Create results message
            total_votes = sum(vote_counts)
            results = []
            for i, option in enumerate(options):
                count = vote_counts[i]
                percentage = (count / total_votes * 100) if total_votes > 0 else 0
                bar_length = int(percentage / 10)
                bar = "█" * bar_length + "░" * (10 - bar_length)
                results.append(f"{self.number_emojis[i]} **{option}**\n{bar} {count} votes ({percentage:.1f}%)")
            
            embed = discord.Embed(
                title=f"📊 Poll Results: {poll['question']}",
                description="\n\n".join(results),
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Total votes: {total_votes}")
            
            await channel.send(embed=embed)
            
            # Mark as ended
            await db.execute(
                "UPDATE polls SET ended = 1 WHERE poll_id = ?",
                (poll['poll_id'],)
            )
            
            # Try to edit original message
            try:
                message = await channel.fetch_message(poll['message_id'])
                original_embed = message.embeds[0]
                original_embed.color = 0xFF0000
                original_embed.title = f"📊 Poll Ended: {poll['question']}"
                await message.edit(embed=original_embed)
            except:
                pass
            
        except Exception as e:
            print(f"Error ending poll: {e}")
    
    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="Poll question",
        options="Poll options separated by semicolons (;)",
        duration="Duration in minutes (optional)"
    )
    async def create_poll(
        self,
        interaction: discord.Interaction,
        question: str,
        options: str,
        duration: Optional[int] = None
    ):
        """Create a poll.
        
        Args:
            interaction: Discord interaction
            question: Poll question
            options: Poll options (semicolon-separated)
            duration: Duration in minutes
        """
        # Parse options
        option_list = [opt.strip() for opt in options.split(';') if opt.strip()]
        
        if len(option_list) < 2:
            await interaction.response.send_message(
                "❌ You need at least 2 options! Separate them with semicolons (;)",
                ephemeral=True
            )
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message(
                "❌ Maximum 10 options allowed!",
                ephemeral=True
            )
            return
        
        # Calculate end time if duration provided
        end_time = None
        if duration:
            if duration < 1:
                await interaction.response.send_message(
                    "❌ Duration must be at least 1 minute!",
                    ephemeral=True
                )
                return
            end_time = datetime.utcnow() + timedelta(minutes=duration)
        
        # Create poll embed
        embed = EmbedTemplates.poll(question, option_list, interaction.user)
        
        if end_time:
            embed.add_field(
                name="⏰ Ends",
                value=f"<t:{int(end_time.timestamp())}:R>",
                inline=False
            )
        
        # Send poll
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Add reactions
        for i in range(len(option_list)):
            await message.add_reaction(self.number_emojis[i])
        
        # Store in database
        await db.execute(
            """INSERT INTO polls 
               (guild_id, channel_id, message_id, question, options, end_time, ended, creator_id)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
            (interaction.guild.id, interaction.channel.id, message.id,
             question, json.dumps(option_list), end_time, interaction.user.id)
        )
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle poll votes.
        
        Args:
            payload: Reaction event payload
        """
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a poll message
        poll = await db.fetchone(
            "SELECT * FROM polls WHERE message_id = ? AND ended = 0",
            (payload.message_id,)
        )
        
        if not poll:
            return
        
        # Check if emoji is valid for this poll
        emoji_str = str(payload.emoji)
        if emoji_str not in self.number_emojis:
            return
        
        option_index = self.number_emojis.index(emoji_str)
        options = json.loads(poll['options'])
        
        if option_index >= len(options):
            return
        
        # Check if user already voted
        existing_vote = await db.fetchone(
            "SELECT * FROM poll_votes WHERE poll_id = ? AND user_id = ?",
            (poll['poll_id'], payload.user_id)
        )
        
        if existing_vote:
            # Update vote
            await db.execute(
                "UPDATE poll_votes SET option_index = ? WHERE poll_id = ? AND user_id = ?",
                (option_index, poll['poll_id'], payload.user_id)
            )
        else:
            # Insert new vote
            await db.execute(
                "INSERT INTO poll_votes (poll_id, user_id, option_index) VALUES (?, ?, ?)",
                (poll['poll_id'], payload.user_id, option_index)
            )
        
        # Remove other reactions from this user
        try:
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            
            for i, emoji in enumerate(self.number_emojis[:len(options)]):
                if i != option_index:
                    await message.remove_reaction(emoji, payload.member)
        except:
            pass
    
    @app_commands.command(name="endpoll", description="End a poll early")
    @app_commands.describe(message_id="Message ID of the poll")
    @is_admin()
    async def end_poll_early(self, interaction: discord.Interaction, message_id: str):
        """End a poll early.
        
        Args:
            interaction: Discord interaction
            message_id: ID of the poll message
        """
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID!",
                ephemeral=True
            )
            return
        
        # Get poll from database
        poll = await db.fetchone(
            "SELECT * FROM polls WHERE message_id = ? AND ended = 0",
            (msg_id,)
        )
        
        if not poll:
            await interaction.response.send_message(
                "❌ No active poll found with that message ID!",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message("⏳ Ending poll...", ephemeral=True)
        await self._end_poll(poll)


async def setup(bot: commands.Bot):
    """Load the Voting cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Voting(bot))
