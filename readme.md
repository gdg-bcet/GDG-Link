# GD Bot - Google Cloud Study Jams 2025

A Discord bot and REST API for tracking Google Cloud Skills Boost badge progress during the Google Cloud Study Jams 2025 program.

## Features

- 🎯 Automated badge verification and tracking
- 📊 Real-time leaderboards and statistics
- 🌐 RESTful API for frontend integration
- 👥 User profile management
- 🔒 Secure with rate limiting and CORS protection

## Quick Start

### Prerequisites

- Python 3.8+
- Discord Bot Token
- MySQL Database

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd "GD Bot"
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the bot:

```bash
python bot.py
```

5. Run the API (optional):

```bash
python api_database.py
```

6. Run both together:

```bash
python integrated_main.py
```

## Configuration

Create a `.env` file with the following variables:

```env
# Discord
TOKEN=your_discord_bot_token
VERIFICATION_CHANNEL_ID=channel_id
VERIFIED_ROLE_ID=role_id
COMPLETION_ROLE_ID=role_id

# Database
DATABASE_HOST=your_host
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password
DATABASE_NAME=your_database

# API
FASTAPI_PORT=30103
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
API_RATE_LIMIT=100
```

See `.env.example` for a complete template.

## API Endpoints

| Endpoint              | Method | Description                      |
| --------------------- | ------ | -------------------------------- |
| `/health`             | GET    | Health check                     |
| `/api/progress`       | GET    | All user progress with filtering |
| `/api/stats`          | GET    | Program statistics               |
| `/api/user/{user_id}` | GET    | User profile details             |
| `/api/leaderboard`    | GET    | Top 10 performers                |

## Discord Commands

### User Commands

- `.profile [user]` - View badge progress
- `.leaderboard` - View top performers
- `.stats` - View program statistics

### Admin Commands

- `.sync` - Sync slash commands
- `.reload [cog]` - Reload cog modules
- `.add_member <user> <profile_url>` - Manually verify user
- `.add_badge <user> <badge_url>` - Manually add badge
- `.export_users` - Export user data
- `.export_badges` - Export badge data

## Project Structure

```
GD Bot/
├── bot.py                 # Discord bot
├── api_database.py        # FastAPI server
├── integrated_main.py     # Combined runner
├── database.py            # Database operations
├── config.py              # Configuration
├── cogs/                  # Bot commands
│   ├── admin.py
│   ├── profile.py
│   ├── stats.py
│   └── events.py
└── .env                   # Environment variables (not committed)
```

## Documentation

- [Security Notice](SECURITY_NOTICE.md) - Important security information
- [Security Fixes Summary](SECURITY_FIXES_SUMMARY.md) - Recent security improvements
- [Database Reference](DATABASE_REFERENCE.md) - Database schema
- [Frontend Development Plan](FRONTEND_DEVELOPMENT_PLAN.md) - Frontend integration guide

## License

MIT License

## Support

For issues and questions, please open an issue in the repository.

---

**Developed for Google Cloud Study Jams 2025 by GDG BCET**
