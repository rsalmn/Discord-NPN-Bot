# Discord NPN Bot

A feature-rich, production-ready Discord bot built with Python 3.10+ and discord.py 2.x. This bot provides comprehensive server management, moderation, and engagement features.

## 🌟 Features

### 📢 Announcement System
- Create beautiful announcement embeds with custom titles and messages
- Choose specific channels for announcements
- Optional @everyone mentions
- Admin-only command for security

### 🎫 Ticket System (Improved!)
- **Button-Based Ticket Panel**: Users click a button to open tickets (no commands needed!)
- **Configurable Ticket Panels**: Admins can post ticket panels in any channel
- **Role-Based Access**: Configure specific support roles who can access tickets
- **Organized Tickets**: Numbered tickets (ticket-0001, ticket-0002, etc.)
- **Custom Categories**: Set custom category for ticket channels
- **Support Role Access**: Only configured support roles + ticket creator can see tickets
- **Auto-Close**: Tickets automatically delete after closing
- **Legacy Command Support**: Still supports `/ticket` command for backward compatibility

### 📝 Forum Management
- **Create Forum Posts**: Create new threads in forum channels with titles and content
- **Edit Forum Posts**: Edit the initial message of forum threads
- **Delete Forum Posts**: Delete forum threads
- **Thread Management**: Lock, unlock, archive, unarchive, pin, and unpin forum threads
- **Tag Support**: Apply tags when creating forum posts
- **Staff-Only**: All commands require `manage_threads` permission

### 👋 Welcome/Leave Messages
- Customizable welcome messages when users join
- Customizable leave messages when users leave
- Set dedicated channels for welcome/leave messages
- Use placeholders: `{user}`, `{username}`, `{server}`, `{membercount}`
- Test your welcome messages before going live

### 🛡️ Anti-Spam System
- Configurable rate limiting (messages per time period)
- Duplicate message detection
- Multiple moderation actions: warn, mute, or kick
- Adjustable thresholds per server
- Automatic message deletion for spam

### 🎉 Giveaway System
- Create timed giveaways with custom prizes
- Users enter by reacting with 🎉
- Automatic winner selection when time expires
- Support for multiple winners
- Reroll functionality if needed
- End giveaways early if required

### 📌 Sticky Messages
- Set messages that automatically repost when others send messages
- Perfect for channel rules or important information
- One sticky message per channel
- Easy to enable/disable

### 💤 AFK System
- Users can set AFK status with a custom reason
- Automatically adds [AFK] prefix to nickname
- Removes AFK status when user sends a message
- Notifies others when they mention AFK users
- Manual AFK removal option

### 🎭 Reaction Roles
- Users get roles by reacting to messages
- Remove reaction to remove role
- Support for multiple reaction roles per message
- Works with custom and default emojis
- Easy setup with message ID

### 📊 Voting/Poll System
- Create polls with up to 10 options
- Optional time limits on polls
- Automatic vote counting and results display
- Visual bar graphs for results
- One vote per user with vote changing allowed
- Early poll ending option

### 💰 Donation Management
- Create donation announcement messages
- Edit existing donation announcements
- Track donation messages per server
- Optional goal amounts
- Beautiful gold-colored embeds
- List all donation announcements

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- A Discord Bot Token
- Basic knowledge of Discord server management

### Creating Your Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "Privileged Gateway Intents", enable:
   - **Presence Intent**
   - **Server Members Intent**
   - **Message Content Intent**
6. Click "Reset Token" and copy your bot token (keep this secret!)

### Inviting Your Bot

1. In the Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select bot permissions:
   - Administrator (or specific permissions based on your needs)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

## 💻 Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/rsalmn/Discord-NPN-Bot.git
cd Discord-NPN-Bot
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_bot_token_here
PREFIX=!
```

Replace `your_bot_token_here` with your actual bot token from the Discord Developer Portal.

### 5. Run the Bot

```bash
python bot.py
```

You should see:
```
Logged in as YourBotName (ID: ...)
Bot is in X guild(s)
Discord.py version: 2.3.2
Bot version: 1.0.0
------
```

## 🌐 Render.com Deployment

Deploy your bot to Render.com for 24/7 uptime (free tier available).

### Step-by-Step Deployment

1. **Create a Render Account**
   - Go to [Render.com](https://render.com)
   - Sign up with GitHub

2. **Connect Your Repository**
   - Push your code to GitHub
   - In Render Dashboard, click "New +"
   - Select "Background Worker"
   - Connect your GitHub repository

3. **Configure the Service**
   - **Name:** `discord-npn-bot` (or your choice)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** Free

4. **Set Environment Variables**
   - Click "Environment" tab
   - Add variables:
     - `DISCORD_TOKEN` = your bot token
     - `PREFIX` = `!` (or your preferred prefix)

5. **Deploy**
   - Click "Create Background Worker"
   - Wait for deployment (usually 2-3 minutes)
   - Check logs to confirm bot is online

### Automatic Deployments

The included `render.yaml` enables automatic deployments:
- Push to your main branch
- Render automatically redeploys your bot
- Zero downtime updates

## 📖 Commands Documentation

### Slash Commands (/)

#### Announcements
- `/announce <channel> <title> <message> [mention_everyone]` - Create an announcement

#### Tickets (Improved!)
- `/ticket_setup <channel> [title] [description]` - Setup a ticket panel with button in a channel
- `/ticket_config [category] [support_roles]` - Configure ticket system (category and support roles)
- `/ticket [reason]` - Create a support ticket (legacy command)
- `/closeticket [reason]` - Close the current ticket

#### Forum Management
- `/forum_create <forum> <title> <content> [tags]` - Create a new forum post/thread
- `/forum_edit <thread> <new_content>` - Edit a forum post's initial message
- `/forum_delete <thread>` - Delete a forum post/thread
- `/forum_manage <thread> <action>` - Manage thread (lock, unlock, archive, unarchive, pin, unpin)

#### Welcome/Leave
- `/setwelcome <channel> [message]` - Configure welcome messages
- `/setleave <channel> [message]` - Configure leave messages
- `/testwelcome` - Test welcome message

#### Anti-Spam
- `/antispam <enabled> [max_messages] [time_window] [action]` - Configure anti-spam

#### Giveaways
- `/gstart <duration> <winners> <prize>` - Start a giveaway
- `/gend <message_id>` - End a giveaway early
- `/greroll <message_id>` - Reroll giveaway winners

#### Sticky Messages
- `/sticky <message>` - Set a sticky message in the channel
- `/unsticky` - Remove sticky message from the channel

#### AFK
- `/afk [reason]` - Set your AFK status
- `/removeafk` - Remove your AFK status

#### Reaction Roles
- `/reactionrole <message_id> <emoji> <role>` - Create a reaction role
- `/removereactionrole <message_id> <emoji>` - Remove a reaction role

#### Polls
- `/poll <question> <options> [duration]` - Create a poll (options separated by `;`)
- `/endpoll <message_id>` - End a poll early

#### Donations
- `/donation <channel> <title> <content> [goal]` - Create donation announcement
- `/editdonation <message_id> <content> [title] [goal]` - Edit donation
- `/listdonations` - List all donation announcements

### Prefix Commands (!)

- `!announce <channel> <content>` - Create announcement (use `|` to separate title and message)
- `!ticket [reason]` - Create a support ticket
- `!help` - Show help message

## ⚙️ Configuration Guide

### Setting Up the New Ticket System

The improved ticket system uses buttons instead of commands for a better user experience!

#### Step 1: Configure Ticket Settings (Optional but Recommended)

```
/ticket_config category:#tickets-category support_roles:Support Staff,Moderator
```

- **category**: Select or create a category where ticket channels will be created
- **support_roles**: Comma-separated list of role names that should have access to all tickets

#### Step 2: Post a Ticket Panel

```
/ticket_setup channel:#support title:Support Tickets description:Need help? Click the button below!
```

This will post a beautiful embed with an "Open Ticket" button in your chosen channel.

#### Step 3: Users Click the Button!

Users simply click the "Open Ticket" button and a private ticket channel is automatically created with:
- Access for the ticket creator
- Access for configured support roles
- Access for administrators
- Numbered ticket names (ticket-0001, ticket-0002, etc.)

#### Benefits of the New System:
- ✅ No need to remember commands
- ✅ Professional-looking ticket panel
- ✅ Role-based access control
- ✅ Better organization with numbered tickets
- ✅ Can post multiple panels in different channels

### Managing Forum Posts

Forum management commands allow you to manage forum channels effectively.

#### Creating a Forum Post

```
/forum_create forum:#announcements title:Important Update content:Check out our new features! tags:News,Important
```

#### Managing Forum Threads

```
/forum_manage thread:[select thread] action:lock
```

Available actions: lock, unlock, archive, unarchive, pin, unpin

### Setting Up Welcome Messages

1. Run `/setwelcome #welcome-channel Your custom message here`
2. Use placeholders:
   - `{user}` - Mentions the user
   - `{username}` - User's name without mention
   - `{server}` - Server name
   - `{membercount}` - Current member count
3. Test with `/testwelcome`

Example:
```
/setwelcome #welcome Welcome {user} to {server}! You are member #{membercount}! 🎉
```

### Configuring Anti-Spam

1. Run `/antispam enabled:True max_messages:5 time_window:10 action:warn`
2. Parameters:
   - `enabled` - Turn on/off
   - `max_messages` - Max messages allowed
   - `time_window` - Time period in seconds
   - `action` - warn, mute, or kick

### Creating Reaction Roles

1. Create an embed message in your channel
2. Copy the message ID (enable Developer Mode in Discord settings)
3. Run `/reactionrole message_id:123456 emoji:🎮 role:@Gamer`
4. Users can now react to get the role!

### Starting a Giveaway

1. Run `/gstart duration:60 winners:1 prize:Discord Nitro`
2. The bot posts the giveaway and adds 🎉 reaction
3. Users react to enter
4. Winners are automatically selected when time ends

### Creating Polls

1. Run `/poll question:"What's your favorite color?" options:"Red;Blue;Green;Yellow" duration:30`
2. Use semicolons (`;`) to separate options
3. Duration is in minutes (optional)
4. Users vote with number reactions

## 🔧 Troubleshooting

### Bot Not Responding to Commands

**Issue:** Bot doesn't respond to slash commands  
**Solution:**
- Make sure bot has `applications.commands` scope
- Wait a few minutes after adding bot (commands need to sync)
- Try kicking and re-inviting the bot

### Permission Errors

**Issue:** "I don't have permission to..."  
**Solution:**
- Check bot role is high enough in role hierarchy
- Verify bot has required permissions in that channel
- Give bot Administrator permission (or specific permissions)

### Bot Not Seeing Messages

**Issue:** Bot doesn't respond to prefix commands  
**Solution:**
- Enable "Message Content Intent" in Discord Developer Portal
- Restart the bot after enabling

### Database Errors

**Issue:** Database-related errors  
**Solution:**
- Ensure `data/` directory exists
- Check file permissions
- Delete `data/bot.db` and restart bot (fresh database)

### Bot Goes Offline

**Issue:** Bot stops running on Render  
**Solution:**
- Check Render logs for errors
- Verify `DISCORD_TOKEN` environment variable is set
- Free tier may sleep after inactivity (upgrade to keep alive)

### Giveaway/Poll Not Ending

**Issue:** Timed features don't auto-complete  
**Solution:**
- Bot must stay online for background tasks
- Check bot logs for errors
- Tasks check every 30 seconds (slight delays are normal)

## 📝 Advanced Configuration

### Changing Bot Prefix

Edit `.env` file:
```env
PREFIX=?
```
Restart the bot.

### Custom Embed Colors

Edit `utils/embeds.py` to customize embed colors:
```python
SUCCESS = 0x00FF00  # Green
ERROR = 0xFF0000    # Red
INFO = 0x3498DB     # Blue
```

### Database Management

SQLite database is stored in `data/bot.db`

To reset the database:
```bash
rm data/bot.db
python bot.py  # Recreates database
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2024 Discord NPN Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Support

If you need help or have questions:
- Check the troubleshooting section above
- Review the commands documentation
- Check bot logs for error messages
- Open an issue on GitHub

## 🔗 Links

- [Discord Developer Portal](https://discord.com/developers/applications)
- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Render.com](https://render.com)

---

**Made with ❤️ for the Discord community**