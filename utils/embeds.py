"""Embed templates for consistent bot responses."""
import discord
from typing import Optional
from datetime import datetime


class EmbedTemplates:
    """Pre-configured embed templates for the bot."""
    
    # Color scheme
    SUCCESS = 0x00FF00  # Green
    ERROR = 0xFF0000    # Red
    INFO = 0x3498DB     # Blue
    WARNING = 0xFFA500  # Orange
    PRIMARY = 0x5865F2  # Discord Blurple
    
    @staticmethod
    def success(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a success embed.
        
        Args:
            title: Embed title
            description: Embed description
            **kwargs: Additional embed parameters
            
        Returns:
            Discord embed object
        """
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=EmbedTemplates.SUCCESS,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def error(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an error embed.
        
        Args:
            title: Embed title
            description: Embed description
            **kwargs: Additional embed parameters
            
        Returns:
            Discord embed object
        """
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=EmbedTemplates.ERROR,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def info(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an info embed.
        
        Args:
            title: Embed title
            description: Embed description
            **kwargs: Additional embed parameters
            
        Returns:
            Discord embed object
        """
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=EmbedTemplates.INFO,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def warning(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a warning embed.
        
        Args:
            title: Embed title
            description: Embed description
            **kwargs: Additional embed parameters
            
        Returns:
            Discord embed object
        """
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=EmbedTemplates.WARNING,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def custom(
        title: str,
        description: str,
        color: int = PRIMARY,
        emoji: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Create a custom embed.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            emoji: Optional emoji prefix for title
            **kwargs: Additional embed parameters
            
        Returns:
            Discord embed object
        """
        if emoji:
            title = f"{emoji} {title}"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def announcement(title: str, description: str, author: discord.Member) -> discord.Embed:
        """Create an announcement embed.
        
        Args:
            title: Announcement title
            description: Announcement content
            author: Member who created the announcement
            
        Returns:
            Discord embed object
        """
        embed = discord.Embed(
            title=f"📢 {title}",
            description=description,
            color=EmbedTemplates.PRIMARY,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(
            text=f"Announced by {author.display_name}",
            icon_url=author.display_avatar.url
        )
        return embed
    
    @staticmethod
    def giveaway(prize: str, end_time: datetime, host: discord.Member) -> discord.Embed:
        """Create a giveaway embed.
        
        Args:
            prize: Giveaway prize
            end_time: When the giveaway ends
            host: Member hosting the giveaway
            
        Returns:
            Discord embed object
        """
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n\n**Ends:** <t:{int(end_time.timestamp())}:R>\n\nReact with 🎉 to enter!",
            color=EmbedTemplates.PRIMARY,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(
            text=f"Hosted by {host.display_name}",
            icon_url=host.display_avatar.url
        )
        return embed
    
    @staticmethod
    def poll(question: str, options: list, creator: discord.Member) -> discord.Embed:
        """Create a poll embed.
        
        Args:
            question: Poll question
            options: List of poll options
            creator: Member who created the poll
            
        Returns:
            Discord embed object
        """
        options_text = "\n".join([f"{i+1}️⃣ {option}" for i, option in enumerate(options)])
        embed = discord.Embed(
            title=f"📊 {question}",
            description=options_text,
            color=EmbedTemplates.PRIMARY,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(
            text=f"Poll by {creator.display_name}",
            icon_url=creator.display_avatar.url
        )
        return embed
