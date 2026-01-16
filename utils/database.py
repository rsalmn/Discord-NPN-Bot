"""Database helper module for SQLite operations."""
import aiosqlite
import os
from typing import Optional, List, Dict, Any


class Database:
    """SQLite database manager for the bot."""
    
    def __init__(self, db_path: str = "data/bot.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    async def connect(self) -> aiosqlite.Connection:
        """Create a database connection.
        
        Returns:
            Database connection object
        """
        return await aiosqlite.connect(self.db_path)
    
    async def init_db(self):
        """Initialize database tables."""
        async with await self.connect() as db:
            # Guild configuration table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    welcome_channel_id INTEGER,
                    welcome_message TEXT,
                    leave_channel_id INTEGER,
                    leave_message TEXT
                )
            """)
            
            # Tickets table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    status TEXT DEFAULT 'open'
                )
            """)
            
            # Anti-spam configuration
            await db.execute("""
                CREATE TABLE IF NOT EXISTS antispam_config (
                    guild_id INTEGER PRIMARY KEY,
                    enabled INTEGER DEFAULT 0,
                    max_messages INTEGER DEFAULT 5,
                    time_window INTEGER DEFAULT 10,
                    action TEXT DEFAULT 'warn'
                )
            """)
            
            # Giveaways table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    giveaway_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_id INTEGER,
                    prize TEXT,
                    winners_count INTEGER DEFAULT 1,
                    end_time TIMESTAMP,
                    ended INTEGER DEFAULT 0,
                    host_id INTEGER
                )
            """)
            
            # Sticky messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sticky_messages (
                    channel_id INTEGER PRIMARY KEY,
                    guild_id INTEGER,
                    content TEXT,
                    last_message_id INTEGER
                )
            """)
            
            # AFK users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS afk_users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    reason TEXT,
                    set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # Reaction roles table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    message_id INTEGER,
                    emoji TEXT,
                    role_id INTEGER,
                    guild_id INTEGER,
                    PRIMARY KEY (message_id, emoji)
                )
            """)
            
            # Polls table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS polls (
                    poll_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_id INTEGER,
                    question TEXT,
                    options TEXT,
                    end_time TIMESTAMP,
                    ended INTEGER DEFAULT 0,
                    creator_id INTEGER
                )
            """)
            
            # Poll votes table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS poll_votes (
                    poll_id INTEGER,
                    user_id INTEGER,
                    option_index INTEGER,
                    PRIMARY KEY (poll_id, user_id)
                )
            """)
            
            # Donations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    message_id INTEGER,
                    channel_id INTEGER,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def get_guild_config(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get configuration for a guild.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Guild configuration dictionary or None
        """
        async with await self.connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def set_guild_config(self, guild_id: int, **kwargs):
        """Set configuration for a guild.
        
        Args:
            guild_id: Discord guild ID
            **kwargs: Configuration parameters to set
        """
        async with await self.connect() as db:
            # Check if config exists
            async with db.execute(
                "SELECT guild_id FROM guild_config WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                exists = await cursor.fetchone()
            
            if exists:
                # Update existing config
                set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
                values = list(kwargs.values()) + [guild_id]
                await db.execute(
                    f"UPDATE guild_config SET {set_clause} WHERE guild_id = ?",
                    values
                )
            else:
                # Insert new config
                columns = ["guild_id"] + list(kwargs.keys())
                placeholders = ", ".join(["?"] * len(columns))
                values = [guild_id] + list(kwargs.values())
                await db.execute(
                    f"INSERT INTO guild_config ({', '.join(columns)}) VALUES ({placeholders})",
                    values
                )
            
            await db.commit()
    
    async def execute(self, query: str, parameters: tuple = ()) -> None:
        """Execute a query without returning results.
        
        Args:
            query: SQL query string
            parameters: Query parameters
        """
        async with await self.connect() as db:
            await db.execute(query, parameters)
            await db.commit()
    
    async def fetchone(self, query: str, parameters: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one row from a query.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            Row as dictionary or None
        """
        async with await self.connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, parameters) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def fetchall(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows from a query.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            List of rows as dictionaries
        """
        async with await self.connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, parameters) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


# Global database instance
db = Database()
