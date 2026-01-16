"""Forum post management cog."""
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db
from typing import Optional


class Forums(commands.Cog):
    """Forum post management system."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the forums cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
    
    @app_commands.command(name="forum_create", description="Create a new forum post/thread")
    @app_commands.describe(
        forum="The forum channel to create the post in",
        title="Title of the forum post",
        content="Content of the forum post",
        tags="Comma-separated list of tag names (optional)"
    )
    @app_commands.checks.has_permissions(manage_threads=True)
    async def forum_create(
        self,
        interaction: discord.Interaction,
        forum: discord.ForumChannel,
        title: str,
        content: str,
        tags: Optional[str] = None
    ):
        """Create a new forum post/thread.
        
        Args:
            interaction: Discord interaction
            forum: The forum channel
            title: Post title
            content: Post content
            tags: Optional comma-separated tag names
        """
        try:
            # Parse tags if provided
            applied_tags = []
            if tags:
                tag_names = [t.strip() for t in tags.split(',')]
                available_tags = {tag.name.lower(): tag for tag in forum.available_tags}
                
                for tag_name in tag_names:
                    tag_name_lower = tag_name.lower()
                    if tag_name_lower in available_tags:
                        applied_tags.append(available_tags[tag_name_lower])
            
            # Create the forum post (thread)
            thread = await forum.create_thread(
                name=title,
                content=content,
                applied_tags=applied_tags[:5] if applied_tags else None,  # Max 5 tags
                reason=f"Forum post created by {interaction.user.name}"
            )
            
            await interaction.response.send_message(
                f"✅ Forum post created successfully! {thread.thread.mention}",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create posts in that forum!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create forum post: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="forum_edit", description="Edit a forum post's initial message")
    @app_commands.describe(
        thread="The forum thread to edit",
        new_content="New content for the post"
    )
    @app_commands.checks.has_permissions(manage_threads=True)
    async def forum_edit(
        self,
        interaction: discord.Interaction,
        thread: discord.Thread,
        new_content: str
    ):
        """Edit a forum post's initial message.
        
        Args:
            interaction: Discord interaction
            thread: The forum thread
            new_content: New content for the post
        """
        try:
            # Check if it's a forum thread
            if not isinstance(thread.parent, discord.ForumChannel):
                await interaction.response.send_message(
                    "❌ This is not a forum thread!",
                    ephemeral=True
                )
                return
            
            # Get the starter message
            starter_message = await thread.fetch_message(thread.id)
            
            # Edit the message
            await starter_message.edit(content=new_content)
            
            await interaction.response.send_message(
                f"✅ Forum post edited successfully! {thread.mention}",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to edit that post!",
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Thread or message not found!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to edit forum post: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="forum_delete", description="Delete a forum post/thread")
    @app_commands.describe(thread="The forum thread to delete")
    @app_commands.checks.has_permissions(manage_threads=True)
    async def forum_delete(
        self,
        interaction: discord.Interaction,
        thread: discord.Thread
    ):
        """Delete a forum post/thread.
        
        Args:
            interaction: Discord interaction
            thread: The forum thread to delete
        """
        try:
            # Check if it's a forum thread
            if not isinstance(thread.parent, discord.ForumChannel):
                await interaction.response.send_message(
                    "❌ This is not a forum thread!",
                    ephemeral=True
                )
                return
            
            thread_name = thread.name
            
            # Delete the thread
            await thread.delete(reason=f"Deleted by {interaction.user.name}")
            
            await interaction.response.send_message(
                f"✅ Forum post '{thread_name}' deleted successfully!",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to delete that thread!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to delete forum post: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="forum_manage", description="Manage forum thread (lock, unlock, archive, etc.)")
    @app_commands.describe(
        thread="The forum thread to manage",
        action="Action to perform on the thread"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Lock", value="lock"),
        app_commands.Choice(name="Unlock", value="unlock"),
        app_commands.Choice(name="Archive", value="archive"),
        app_commands.Choice(name="Unarchive", value="unarchive"),
        app_commands.Choice(name="Pin", value="pin"),
        app_commands.Choice(name="Unpin", value="unpin"),
    ])
    @app_commands.checks.has_permissions(manage_threads=True)
    async def forum_manage(
        self,
        interaction: discord.Interaction,
        thread: discord.Thread,
        action: str
    ):
        """Manage a forum thread.
        
        Args:
            interaction: Discord interaction
            thread: The forum thread
            action: Action to perform
        """
        try:
            # Check if it's a forum thread
            if not isinstance(thread.parent, discord.ForumChannel):
                await interaction.response.send_message(
                    "❌ This is not a forum thread!",
                    ephemeral=True
                )
                return
            
            action_performed = ""
            
            if action == "lock":
                await thread.edit(locked=True, reason=f"Locked by {interaction.user.name}")
                action_performed = "locked"
            elif action == "unlock":
                await thread.edit(locked=False, reason=f"Unlocked by {interaction.user.name}")
                action_performed = "unlocked"
            elif action == "archive":
                await thread.edit(archived=True, reason=f"Archived by {interaction.user.name}")
                action_performed = "archived"
            elif action == "unarchive":
                await thread.edit(archived=False, reason=f"Unarchived by {interaction.user.name}")
                action_performed = "unarchived"
            elif action == "pin":
                await thread.edit(pinned=True, reason=f"Pinned by {interaction.user.name}")
                action_performed = "pinned"
            elif action == "unpin":
                await thread.edit(pinned=False, reason=f"Unpinned by {interaction.user.name}")
                action_performed = "unpinned"
            
            await interaction.response.send_message(
                f"✅ Thread {thread.mention} has been {action_performed}!",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage that thread!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to manage forum thread: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Load the Forums cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Forums(bot))
