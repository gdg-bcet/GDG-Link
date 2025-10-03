#!/usr/bin/env python3
"""
🏆 Google Cloud Study Jams 2025 Badge Tracking API
==================================================

A comprehensive REST API for managing badge tracking in the Google Cloud Study Jams 2025 program.
This standalone API provides endpoints for user management, badge submission, progress tracking,
and comprehensive statistics with beautiful Swagger UI documentation.

Features:
- 🚀 Real-time user progress tracking
- 📊 Comprehensive statistics and analytics
- 🏆 Dynamic leaderboards
- 👤 Detailed user profiles with badge timestamps
- 📈 Progress timeline and completion analytics
- 🌐 CORS-enabled for web applications
- 📚 Interactive API documentation

Run this file directly to start the API server:
    python api_database.py

Or use uvicorn for production:
    uvicorn api_database:app --host 0.0.0.0 --port 8001

Author: Sayan Barma
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import db
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import pytz
import os

# Kolkata timezone
KOLKATA_TZ = pytz.timezone('Asia/Kolkata')


def get_kolkata_time():
    """Get current time in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment
PORT = int(os.getenv("FASTAPI_PORT", "30103"))
HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{RATE_LIMIT}/minute"])

# Initialize FastAPI with enhanced metadata
app = FastAPI(
    title="🏆 Google Cloud Study Jams 2025 API",
    description="""
A modern REST API for the Google Cloud Study Jams 2025 program, designed to manage participants,
track badge completion progress, and provide comprehensive analytics for educational programs.

🎯 **Core Functionality:**
- User registration and verification system
- Badge completion tracking across 20+ Google Cloud badges
- Real-time progress monitoring and leaderboards
- Advanced filtering, search, and sorting capabilities
- Comprehensive program statistics and analytics

🚀 **Built With:**
- FastAPI framework for high-performance API development
- MySQL database with optimized queries
- Interactive Swagger UI and ReDoc documentation
- CORS support for seamless web integration

✨ **Perfect For:**
- Educational program administrators
- Learning management systems
- Progress tracking dashboards
- Badge completion monitoring
- Program analytics and reporting

🔧 **Quick Start:**
```bash
python api_database.py
```

For production deployment:
```bash
uvicorn api_database:app --host 0.0.0.0 --port 8001
```
""",
    version="2.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Use environment variable for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["System"],
    summary="🔍 Health Check",
    response_description="API health status and system information",
    responses={
        200: {
            "description": "API is healthy and database is connected",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "message": "API is running",
                        "timestamp": "2025-09-27T14:30:00Z",
                        "database": "connected",
                        "version": "2.0.0"
                    }
                }
            }
        }
    }
)
@limiter.limit("10/minute")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    ## 🔍 Health Check Endpoint

    Returns the current health status of the API server and database connection.

    **Use this endpoint to:**
    - Monitor API availability
    - Check database connectivity
    - Verify system status for monitoring tools
    - Test basic API functionality

    **Response includes:**
    - Server status
    - Database connection status
    - Current timestamp
    - API version information
    """
    try:
        # Test database connection
        db.ensure_connection()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "message": "API is running",
        "timestamp": get_kolkata_time().isoformat(),
        "database": db_status,
        "version": "2.0.0",
        "program": "Google Cloud Study Jams 2025"
    }


@app.get(
    "/api/progress",
    tags=["Progress Tracking"],
    summary="📊 All User Progress with Filters",
    response_description="Complete participant progress with rankings and badge status",
    responses={
        200: {
            "description": "Successfully retrieved all user progress data",
            "content": {
                "application/json": {
                    "example": {
                        "program_name": "Google Cloud Study Jams 2025",
                        "total_badges": 20,
                        "total_users": 46,
                        "filtered_users": 23,
                        "query_info": {
                            "search": "sayan",
                            "sort_by": "badge_count",
                            "sort_order": "desc",
                            "filter_badge_count": ">5"
                        },
                        "users": [
                            {
                                "Rank": 1,
                                "Discord ID": "1291470987958812743",
                                "Name": "SANJEEV KUMAR PANDIT",
                                "Profile URL": "https://www.cloudskillsboost.google/public_profiles/...",
                                "Profile Color": "#1F2937",
                                "Badge Count": 7,
                                "badges": {
                                    "The Basics of Google Cloud Compute": "Done",
                                    "Get Started with Cloud Storage": "",
                                    "Get Started with Pub/Sub": "Done"
                                }
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def get_all_progress(
    request: Request,
    search: Optional[str] = None,
    sort_by: str = "badge_count",
    sort_order: str = "desc",
    filter_badge_count: Optional[str] = None
) -> Dict[str, Any]:
    """
    ## 📊 Get All User Progress with Advanced Filtering

    Retrieves comprehensive progress data for all verified participants with powerful search, sort, and filter capabilities.

    **📋 Query Parameters:**

    ### 🔍 Search
    - **search** (optional): Search by participant name (case-insensitive)
    - Example: `?search=sayan` finds users with "sayan" in their name

    ### 📈 Sort Options
    - **sort_by**: Field to sort by (`badge_count`, `name`)
    - **sort_order**: Sort direction (`asc`, `desc`)
    - Example: `?sort_by=name&sort_order=asc` sorts alphabetically

    ### 🎯 Filter Options
    - **filter_badge_count**: Badge count filter with logic operators
    - Supported operators: `>`, `<`, `=`, `>=`, `<=`
    - Examples:
      - `?filter_badge_count=>5` - Users with more than 5 badges
      - `?filter_badge_count=0` - Users with exactly 0 badges
      - `?filter_badge_count>=10` - Users with 10 or more badges

    **🔄 Combined Usage:**
    ```
    /api/progress?search=kumar&sort_by=badge_count&sort_order=desc&filter_badge_count=>3
    ```
    Find users with "kumar" in name, having >3 badges, sorted by badge count descending

    **This endpoint provides:**
    - 🏆 **User Rankings** - Participants sorted by your criteria
    - 📋 **Complete Badge Status** - All 20 badges with completion status
    - 👤 **User Information** - Names, Discord IDs, and profile URLs
    - 📊 **Progress Statistics** - Total and filtered user counts
    - 🎨 **Profile Colors** - Dark colors optimized for white text

    **Badge Status Values:**
    - `"Done"` - Badge completed by user
    - `""` (empty) - Badge not yet completed

    **Profile Colors:**
    - All colors are dark and optimized for white text (WCAG AA compliant)
    - Perfect for frontend profile image generation
    - Consistent across all API endpoints

    **Use Cases:**
    - Display filterable/sortable program leaderboard
    - Show participant progress dashboard with search
    - Generate filtered progress reports
    - Monitor program engagement by badge count ranges

    **Performance:** Optimized with database-level filtering and sorting

    ```json
    {
      "program_name": "Google Cloud Study Jams 2025",
      "total_badges": 20,
      "total_users": 46,
      "filtered_users": 12,
      "query_info": {
        "search": "kumar",
        "sort_by": "badge_count",
        "sort_order": "desc",
        "filter_badge_count": ">3"
      },
      "users": [
        {
          "Rank": 1,
          "Discord ID": "1291470987958812743",
          "Name": "SANJEEV KUMAR PANDIT",
          "Profile URL": "https://www.cloudskillsboost.google/...",
          "Profile Color": "#1F2937",
          "Badge Count": 7,
          "badges": {
            "The Basics of Google Cloud Compute": "Done",
            "Get Started with Cloud Storage": "",
            "Get Started with Pub/Sub": "Done"
          }
        }
      ]
    }
    ```
    """
    try:
        # Validate and sanitize parameters
        valid_sort_fields = ["badge_count", "name"]
        valid_sort_orders = ["asc", "desc"]

        if sort_by not in valid_sort_fields:
            sort_by = "badge_count"
        if sort_order not in valid_sort_orders:
            sort_order = "desc"

        # Parse badge count filter
        badge_count_condition = ""
        badge_count_value = None

        if filter_badge_count:
            import re
            # Match patterns like ">5", "<=10", "=3", etc.
            match = re.match(r'^(>=|<=|>|<|=)(\d+)$', filter_badge_count.strip())
            if match:
                operator, value = match.groups()
                badge_count_value = int(value)

                # Convert to SQL condition
                if operator == "=":
                    badge_count_condition = f" AND badge_count = {badge_count_value}"
                elif operator == ">":
                    badge_count_condition = f" AND badge_count > {badge_count_value}"
                elif operator == "<":
                    badge_count_condition = f" AND badge_count < {badge_count_value}"
                elif operator == ">=":
                    badge_count_condition = f" AND badge_count >= {badge_count_value}"
                elif operator == "<=":
                    badge_count_condition = f" AND badge_count <= {badge_count_value}"

        # Get filtered and sorted data from database
        result = db.get_all_user_progress_filtered(
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            badge_count_condition=badge_count_condition
        )

        # Add query info to response
        result["query_info"] = {
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "filter_badge_count": filter_badge_count
        }
        result["filtered_users"] = len(result.get("users", []))

        logger.info(f"Retrieved filtered progress: {result['filtered_users']} of {result.get('total_users', 0)} users")
        return result
    except Exception as e:
        logger.error(f"Error retrieving filtered user progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user progress: {str(e)}")


@app.get(
    "/api/stats",
    tags=["Analytics"],
    summary="📈 Program Statistics",
    response_description="Complete program statistics and analytics",
    responses={
        200: {
            "description": "Successfully retrieved program statistics",
            "content": {
                "application/json": {
                    "example": {
                        "program_name": "Google Cloud Study Jams 2025",
                        "total_users": 46,
                        "completed_users": 0,
                        "total_badges": 20,
                        "completion_percentage": 0,
                        "average_badges": 2,
                        "badge_completion_stats": {
                            "The Basics of Google Cloud Compute": 18,
                            "Get Started with Cloud Storage": 11,
                            "Get Started with Pub/Sub": 7
                        },
                        "completion_distribution": {
                            "0": 6, "1": 18, "2": 8, "3": 5
                        },
                        "top_performer": {
                            "discord_id": "1291470987958812743",
                            "name": "SANJEEV KUMAR PANDIT",
                            "badge_count": 7,
                            "profile_url": "https://www.cloudskillsboost.google/...",
                            "profile_color": "#1F2937"
                        },
                        "progress_timeline": {
                            "2024-10-15": 1, "2024-10-16": 44
                        }
                    }
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def get_stats(request: Request) -> Dict[str, Any]:
    """
    ## 📈 Program Statistics & Analytics

    Provides comprehensive analytics and statistics for the Google Cloud Study Jams 2025 program.

    **📊 Analytics Included:**

    ### User Metrics
    - 👥 **Total Users** - All verified participants
    - 🏅 **Completed Users** - Participants with all 20 badges
    - 📊 **Completion Percentage** - Overall program completion rate
    - 🎯 **Average Badges** - Mean badges per participant

    ### Badge Analytics
    - 🏆 **Badge Completion Stats** - Individual badge completion counts
    - 📈 **Completion Distribution** - Users grouped by badge count (0-20)
    - 🥇 **Top Performer** - Highest achieving participant

    ### Timeline Data
    - 📅 **Progress Timeline** - Daily badge submission counts
    - 📈 **Submission Patterns** - Activity trends over time

    **Perfect for:**
    - Program dashboard metrics
    - Progress reporting
    - Engagement analysis
    - Performance tracking

    ```json
    {
      "program_name": "Google Cloud Study Jams 2025",
      "total_users": 46,
      "completed_users": 0,
      "total_badges": 20,
      "completion_percentage": 0,
      "average_badges": 2,
      "badge_completion_stats": {
        "The Basics of Google Cloud Compute": 18,
        "Get Started with Cloud Storage": 11,
        "Get Started with Pub/Sub": 7
      },
      "completion_distribution": {
        "0": 6, "1": 18, "2": 8, "3": 5
      },
      "top_performer": {
        "discord_id": "1291470987958812743",
        "name": "SANJEEV KUMAR PANDIT",
        "badge_count": 7,
        "profile_url": "https://..."
      },
      "progress_timeline": {
        "2024-10-15": 1,
        "2024-10-16": 44,
        "2024-10-17": 6
      },
      "last_updated": "2025-09-27T10:40:29.108493",
      "mode": "production-ready"
    }
    ```
    """
    try:
        stats = db.get_stats()
        logger.info(f"Retrieved statistics for {stats.get('total_users', 0)} users")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@app.get(
    "/api/user/{user_id}",
    tags=["User Profiles"],
    summary="👤 User Profile",
    response_description="Complete user profile with detailed badge information and timestamps",
    responses={
        200: {
            "description": "Successfully retrieved user profile",
            "content": {
                "application/json": {
                    "example": {
                        "discord_id": "549415697726439434",
                        "name": "Sayan Barma",
                        "profile": "https://www.cloudskillsboost.google/public_profiles/...",
                        "profile_color": "#1F2937",
                        "badge_count": 4,
                        "total_badges": 20,
                        "completion_percentage": 20,
                        "badges": [
                            {
                                "name": "The Basics of Google Cloud Compute",
                                "completed": True,
                                "url": "https://www.cloudskillsboost.google/...",
                                "timestamp": "2024-10-16 05:50:16"
                            },
                            {
                                "name": "Get Started with Looker",
                                "completed": False,
                                "url": None,
                                "timestamp": None
                            }
                        ],
                        "mode": "production-ready"
                    }
                }
            }
        },
        404: {"description": "User not found or not verified"},
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def get_user(
    request: Request,
    user_id: str = Path(
        ...,
        description="Discord User ID",
        examples=["549415697726439434"],
        pattern=r'^\d+$'
    )
) -> Dict[str, Any]:
    """
    ## 👤 Get User Profile

    Retrieves detailed profile information and badge progress for a specific participant.

    **🎯 User Profile Includes:**

    ### Basic Information
    - 👤 **Name** - Participant's display name
    - 🆔 **Discord ID** - Unique Discord identifier
    - 🔗 **Profile URL** - Google Cloud Skills Boost profile link
    - 🎨 **Profile Color** - Dark color optimized for white text (WCAG AA)
    - 📊 **Progress Stats** - Badge counts and completion percentage

    ### Detailed Badge Information
    - 🏆 **All 20 Badges** - Complete list with status
    - ✅ **Completion Status** - Boolean completion flag
    - 🔗 **Badge URLs** - Direct links to earned badges
    - ⏰ **Timestamps** - Exact completion times

    **Perfect for:**
    - Individual progress tracking
    - Personal dashboards
    - Badge verification
    - Progress history

    **Badge Object Structure:**
    - `completed: true/false` - Badge completion status
    - `url: string/null` - Badge URL if completed
    - `timestamp: string/null` - Completion timestamp if completed

    ```json
    {
      "discord_id": "549415697726439434",
      "name": "Sayan Barma",
      "profile": "https://www.cloudskillsboost.google/public_profiles/...",
      "badge_count": 4,
      "total_badges": 20,
      "completion_percentage": 20,
      "badges": [
        {
          "name": "The Basics of Google Cloud Compute",
          "completed": true,
          "url": "https://www.cloudskillsboost.google/...",
          "timestamp": "2024-10-16 05:50:16"
        },
        {
          "name": "Get Started with Looker",
          "completed": false,
          "url": null,
          "timestamp": null
        }
      ],
      "mode": "production-ready"
    }
    ```
    """
    try:
        user_data = db.get_user_progress(user_id)
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail=f"User with Discord ID '{user_id}' not found or not verified"
            )
        logger.info(f"Retrieved profile for user {user_id} ({user_data.get('name', 'Unknown')})")
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user profile: {str(e)}")


@app.get(
    "/api/leaderboard",
    tags=["Leaderboards"],
    summary="🏆 Top Performers",
    response_description="Top 10 participants ranked by badge count with complete badge details",
    responses={
        200: {
            "description": "Successfully retrieved leaderboard",
            "content": {
                "application/json": {
                    "example": {
                        "program_name": "Google Cloud Study Jams 2025",
                        "top_performers": [
                            {
                                "Rank": 1,
                                "Discord ID": "1291470987958812743",
                                "Name": "SANJEEV KUMAR PANDIT",
                                "Profile URL": "https://www.cloudskillsboost.google/...",
                                "Profile Color": "#1F2937",
                                "Badge Count": 7,
                                "badges": {
                                    "The Basics of Google Cloud Compute": "Done",
                                    "Get Started with Cloud Storage": "",
                                    "Get Started with Pub/Sub": "Done"
                                }
                            }
                        ],
                        "total_participants": 46,
                        "last_updated": "2025-09-27T11:07:45.982326",
                        "mode": "production-ready"
                    }
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def get_leaderboard(request: Request) -> Dict[str, Any]:
    """
    ## 🏆 Top Performers Leaderboard

    Get the **top 10 performing participants** in the Google Cloud Study Jams 2025 program.

    **🥇 Leaderboard Features:**

    ### Ranking System
    - 🏆 **Top 10 Only** - Highest performing participants
    - 📊 **Badge Count Sorting** - Ranked by total badges earned
    - 🎯 **Tie Breaking** - Alphabetical by name for equal badge counts

    ### Participant Details
    - 👤 **Full Profile** - Name, Discord ID, Profile URL
    - 🏅 **Badge Progress** - Complete badge status for each participant
    - 📊 **Performance Metrics** - Badge counts and rankings

    ### Program Context
    - 📈 **Total Participants** - Full program participation count
    - ⏰ **Last Updated** - Real-time update timestamp
    - 🎯 **Program Status** - Production readiness indicator

    **Perfect for:**
    - Competition dashboards
    - Recognition displays
    - Progress motivation
    - Community highlights

    **Ranking Logic:**
    1. Primary: Badge count (descending)
    2. Secondary: Name (alphabetical)

    ```json
    {
      "program_name": "Google Cloud Study Jams 2025",
      "top_performers": [
        {
          "Rank": 1,
          "Discord ID": "1291470987958812743",
          "Name": "SANJEEV KUMAR PANDIT",
          "Profile URL": "https://www.cloudskillsboost.google/...",
          "Badge Count": 7,
          "badges": {
            "The Basics of Google Cloud Compute": "Done",
            "Get Started with Cloud Storage": "",
            "Get Started with Pub/Sub": "Done",
            "Get Started with API Gateway": "Done",
            "Get Started with Looker": "Done",
            "Get Started with Dataplex": "Done"
          }
        },
        {
          "Rank": 2,
          "Discord ID": "1295990916317839381",
          "Name": "Suraj Mahto",
          "Profile URL": "https://www.cloudskillsboost.google/...",
          "Badge Count": 6,
          "badges": {
            "The Basics of Google Cloud Compute": "Done",
            "Get Started with Cloud Storage": "Done"
          }
        }
      ],
      "total_participants": 46,
      "last_updated": "2025-09-27T11:07:45.982326",
      "mode": "production-ready"
    }
    ```
    """
    try:
        leaderboard = db.get_leaderboard()
        logger.info(f"Retrieved leaderboard with {len(leaderboard.get('top_performers', []))} top performers")
        return leaderboard
    except Exception as e:
        logger.error(f"Error retrieving leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leaderboard: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": get_kolkata_time().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": get_kolkata_time().isoformat(),
            "path": str(request.url.path)
        }
    )


# Main execution
if __name__ == "__main__":
    """
    🚀 Direct execution entry point

    Run this file directly to start the API server:
        python api_database.py

    The server will start on http://127.0.0.1:8001 with:
    - Hot reloading enabled for development
    - Interactive documentation at /docs and /redoc
    - CORS enabled for web application integration
    """
    print("🏆 Starting Google Cloud Study Jams 2025 API Server...")
    print(f"📚 Documentation available at: http://127.0.0.1:{PORT}/docs")
    print(f"🔍 Alternative docs at: http://127.0.0.1:{PORT}/redoc")
    print(f"💓 Health check at: http://127.0.0.1:{PORT}/health")
    print(f"🔒 CORS Origins: {CORS_ORIGINS}")
    print(f"⚡ Rate Limit: {RATE_LIMIT} requests/minute")
    print("🚀 Starting server...")

    uvicorn.run(
        "api_database:app",
        host=HOST,
        port=PORT,
        # reload=True,
        reload_dirs=["./"],
        log_level="info"
    )
