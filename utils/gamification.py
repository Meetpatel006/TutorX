"""
Gamification utilities for the TutorX MCP server
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import random


# Dictionary to store badges for students
# In a real application, this would be stored in a database
BADGES_DB = {}

# Dictionary to store leaderboards
# In a real application, this would be stored in a database
LEADERBOARDS_DB = {
    "weekly_points": {},
    "monthly_streak": {},
    "problem_solving_speed": {}
}

# Badge definitions
BADGES = {
    "beginner": {
        "name": "Beginner",
        "description": "Completed your first lesson",
        "icon": "🔰",
        "points": 10
    },
    "persistent": {
        "name": "Persistent Learner",
        "description": "Completed 5 lessons in a row",
        "icon": "🔄",
        "points": 25
    },
    "math_whiz": {
        "name": "Math Whiz",
        "description": "Scored 100% on a math assessment",
        "icon": "🧮",
        "points": 50
    },
    "science_explorer": {
        "name": "Science Explorer",
        "description": "Completed 10 science modules",
        "icon": "🔬",
        "points": 50
    },
    "speed_demon": {
        "name": "Speed Demon",
        "description": "Solved 5 problems in under 2 minutes each",
        "icon": "⚡",
        "points": 35
    },
    "accuracy_master": {
        "name": "Accuracy Master",
        "description": "Maintained 90% accuracy over 20 problems",
        "icon": "🎯",
        "points": 40
    },
    "helping_hand": {
        "name": "Helping Hand",
        "description": "Helped 5 other students in the forum",
        "icon": "🤝",
        "points": 30
    },
    "night_owl": {
        "name": "Night Owl",
        "description": "Studied for 3 hours after 8 PM",
        "icon": "🌙",
        "points": 20
    },
    "early_bird": {
        "name": "Early Bird",
        "description": "Studied for 3 hours before 9 AM",
        "icon": "🌅",
        "points": 20
    },
    "perfect_streak": {
        "name": "Perfect Streak",
        "description": "Logged in for 7 days straight",
        "icon": "🔥",
        "points": 45
    }
}


def award_badge(student_id: str, badge_id: str) -> Dict[str, Any]:
    """
    Award a badge to a student
    
    Args:
        student_id: The student's unique identifier
        badge_id: The badge's unique identifier
        
    Returns:
        Badge information
    """
    if badge_id not in BADGES:
        return {
            "error": "Invalid badge ID",
            "timestamp": datetime.now().isoformat()
        }
    
    if student_id not in BADGES_DB:
        BADGES_DB[student_id] = {}
    
    # Check if student already has the badge
    if badge_id in BADGES_DB[student_id]:
        return {
            "message": "Badge already awarded",
            "badge": BADGES[badge_id],
            "timestamp": BADGES_DB[student_id][badge_id]["timestamp"]
        }
    
    # Award the badge
    BADGES_DB[student_id][badge_id] = {
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "message": "Badge awarded!",
        "badge": BADGES[badge_id],
        "timestamp": datetime.now().isoformat()
    }


def get_student_badges(student_id: str) -> Dict[str, Any]:
    """
    Get all badges for a student
    
    Args:
        student_id: The student's unique identifier
        
    Returns:
        Dictionary of badges and points
    """
    if student_id not in BADGES_DB or not BADGES_DB[student_id]:
        return {
            "student_id": student_id,
            "badges": [],
            "total_points": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    badges_list = []
    total_points = 0
    
    for badge_id in BADGES_DB[student_id]:
        if badge_id in BADGES:
            badge_info = BADGES[badge_id].copy()
            badge_info["awarded_at"] = BADGES_DB[student_id][badge_id]["timestamp"]
            badges_list.append(badge_info)
            total_points += badge_info["points"]
    
    return {
        "student_id": student_id,
        "badges": badges_list,
        "total_points": total_points,
        "timestamp": datetime.now().isoformat()
    }


def update_leaderboard(leaderboard_id: str, student_id: str, score: float) -> Dict[str, Any]:
    """
    Update a leaderboard with a new score for a student
    
    Args:
        leaderboard_id: The leaderboard to update
        student_id: The student's unique identifier
        score: The score to record
        
    Returns:
        Updated leaderboard information
    """
    if leaderboard_id not in LEADERBOARDS_DB:
        return {
            "error": "Invalid leaderboard ID",
            "timestamp": datetime.now().isoformat()
        }
    
    # Update student's score
    LEADERBOARDS_DB[leaderboard_id][student_id] = {
        "score": score,
        "timestamp": datetime.now().isoformat()
    }
    
    # Get top 10 students
    top_students = sorted(
        LEADERBOARDS_DB[leaderboard_id].items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:10]
    
    # Format leaderboard
    leaderboard = []
    for i, (sid, data) in enumerate(top_students):
        leaderboard.append({
            "rank": i + 1,
            "student_id": sid,
            "score": data["score"],
            "last_updated": data["timestamp"]
        })
    
    # Find student's rank
    student_rank = next(
        (i + 1 for i, (sid, _) in enumerate(top_students) if sid == student_id),
        len(LEADERBOARDS_DB[leaderboard_id]) + 1
    )
    
    return {
        "leaderboard_id": leaderboard_id,
        "leaderboard": leaderboard,
        "student_rank": student_rank,
        "student_score": score,
        "timestamp": datetime.now().isoformat()
    }


def get_leaderboard(leaderboard_id: str) -> Dict[str, Any]:
    """
    Get the current state of a leaderboard
    
    Args:
        leaderboard_id: The leaderboard to get
        
    Returns:
        Leaderboard information
    """
    if leaderboard_id not in LEADERBOARDS_DB:
        return {
            "error": "Invalid leaderboard ID",
            "timestamp": datetime.now().isoformat()
        }
    
    # Get top 10 students
    top_students = sorted(
        LEADERBOARDS_DB[leaderboard_id].items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:10]
    
    # Format leaderboard
    leaderboard = []
    for i, (sid, data) in enumerate(top_students):
        leaderboard.append({
            "rank": i + 1,
            "student_id": sid,
            "score": data["score"],
            "last_updated": data["timestamp"]
        })
    
    return {
        "leaderboard_id": leaderboard_id,
        "leaderboard": leaderboard,
        "total_students": len(LEADERBOARDS_DB[leaderboard_id]),
        "timestamp": datetime.now().isoformat()
    }


def check_achievements(student_id: str, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check if a student's activity unlocks any new badges
    
    Args:
        student_id: The student's unique identifier
        activity_data: Data about the student's activity
        
    Returns:
        List of newly awarded badges
    """
    new_badges = []
    
    # Initialize student badge record if needed
    if student_id not in BADGES_DB:
        BADGES_DB[student_id] = {}
    
    # Check for potential badge earnings based on activity
    if "activity_type" in activity_data:
        activity_type = activity_data["activity_type"]
        
        # Beginner badge - first lesson
        if activity_type == "lesson_completed" and "beginner" not in BADGES_DB[student_id]:
            badge_result = award_badge(student_id, "beginner")
            if "error" not in badge_result:
                new_badges.append(badge_result)
        
        # Math Whiz - perfect math assessment
        if (activity_type == "assessment_completed" and 
            activity_data.get("subject") == "math" and 
            activity_data.get("score") == 1.0 and
            "math_whiz" not in BADGES_DB[student_id]):
            badge_result = award_badge(student_id, "math_whiz")
            if "error" not in badge_result:
                new_badges.append(badge_result)
        
        # Speed Demon - fast problem solving
        if (activity_type == "problem_solved" and 
            activity_data.get("time_seconds", 999) < 120):
            # In a real system, we'd track the count over time
            # Here we'll simulate it
            if random.random() < 0.2 and "speed_demon" not in BADGES_DB[student_id]:
                badge_result = award_badge(student_id, "speed_demon")
                if "error" not in badge_result:
                    new_badges.append(badge_result)
    
    return new_badges
