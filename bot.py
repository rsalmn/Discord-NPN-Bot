"""
Discord NPN Bot - Main Entry Point
A feature-rich Discord bot with announcements, tickets, moderation, and more.
"""
import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
import asyncio
from utils.database import db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('discord_bot')

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX', '!')
VERSION = "1.0.0"

# Required intents for bot functionality
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
intents.guilds = True
intents.reactions = True


class NPNBot(commands.Bot):
    """Custom bot class for Discord NPN Bot."""
    
    def __init__(self):
        """Initialize the bot."""
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )
        self.version = VERSION
        self.initial_extensions = [
            'cogs.announcements',
            'cogs.tickets',
            'cogs.welcome',
            'cogs.antispam',
            'cogs.giveaways',
            'cogs.sticky',
            'cogs.afk',
            'cogs.reactionroles',
            'cogs.voting',
            'cogs.donations',
        ]
    
    async def setup_hook(self):
        """Async initialization - load cogs and sync commands."""
        # Initialize database
        logger.info("Initializing database...")
        await db.init_db()
        logger.info("Database initialized successfully")
        
        # Load all cogs
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Bot is in {len(self.guilds)} guild(s)")
        logger.info(f"Discord.py version: {discord.__version__}")
        logger.info(f"Bot version: {self.version}")
        logger.info("------")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | v{self.version}"
            )
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when the bot joins a guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Update presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | v{self.version}"
            )
        )
        
        # Send welcome message to system channel if available
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="👋 Thanks for adding me!",
                description=(
                    f"Hello! I'm **{self.user.name}**, a multi-purpose Discord bot.\n\n"
                    f"**Getting Started:**\n"
                    f"• Use `/help` to see all available commands\n"
                    f"• Use `{PREFIX}help` for prefix commands\n"
                    f"• Most commands require administrator permissions\n\n"
                    f"**Features:**\n"
                    f"📢 Announcements • 🎫 Tickets • 👋 Welcome Messages\n"
                    f"🛡️ Anti-Spam • 🎉 Giveaways • 📌 Sticky Messages\n"
                    f"💤 AFK System • 🎭 Reaction Roles • 📊 Polls • 💰 Donations\n\n"
                    f"Need help? Run `/help` to get started!"
                ),
                color=0x5865F2
            )
            embed.set_thumbnail(url=self.user.display_avatar.url)
            try:
                await guild.system_channel.send(embed=embed)
            except:
                pass
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when the bot leaves a guild."""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Update presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | v{self.version}"
            )
        )
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error handler for prefix commands."""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided: {error}")
        else:
            logger.error(f"Command error: {error}", exc_info=error)
            await ctx.send("❌ An error occurred while executing the command.")


async def main():
    """Main entry point for the bot."""
    # Check if token is set
    if not TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your bot token.")
        return
    
    # Create and run the bot
    bot = NPNBot()
    
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=e)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
