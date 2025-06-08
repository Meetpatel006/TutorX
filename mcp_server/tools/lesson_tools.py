"""
Lesson generation tools for TutorX MCP.
"""
from typing import Dict, Any, List
from mcp_server.mcp_instance import mcp

@mcp.tool()
async def generate_lesson_tool(topic: str, grade_level: int, duration_minutes: int) -> Dict[str, Any]:
    """
    Generate a lesson plan for the given topic, grade level, and duration.
    
    Args:
        topic: The topic for the lesson
        grade_level: The grade level (1-12)
        duration_minutes: Duration of the lesson in minutes
        
    Returns:
        Dictionary containing the generated lesson plan
    """
    # Validate inputs
    if not topic or not isinstance(topic, str):
        return {"error": "Topic must be a non-empty string"}
    
    if not isinstance(grade_level, int) or grade_level < 1 or grade_level > 12:
        return {"error": "Grade level must be an integer between 1 and 12"}
    
    if not isinstance(duration_minutes, (int, float)) or duration_minutes <= 0:
        return {"error": "Duration must be a positive number"}
    
    # Calculate time allocation (example: 10% intro, 30% instruction, 40% practice, 20% review)
    intro_time = max(5, duration_minutes * 0.1)  # At least 5 minutes
    instruction_time = duration_minutes * 0.3
    practice_time = duration_minutes * 0.4
    review_time = duration_minutes - (intro_time + instruction_time + practice_time)
    
    # Generate learning objectives based on grade level and topic
    difficulty = {
        1: "basic",
        2: "basic",
        3: "basic",
        4: "intermediate",
        5: "intermediate",
        6: "intermediate",
        7: "advanced",
        8: "advanced",
        9: "advanced",
        10: "expert",
        11: "expert",
        12: "expert"
    }.get(grade_level, "intermediate")
    
    # Create lesson plan
    lesson_plan = {
        "topic": topic,
        "grade_level": grade_level,
        "duration_minutes": duration_minutes,
        "difficulty": difficulty,
        "objectives": [
            f"Understand the {difficulty} concepts of {topic}",
            f"Apply {topic} concepts to solve problems",
            f"Analyze and evaluate {topic} in different contexts"
        ],
        "materials": [
            "Whiteboard and markers",
            "Printed worksheets",
            "Example code snippets",
            "Interactive coding environment"
        ],
        "activities": [
            {
                "type": "introduction",
                "duration_minutes": intro_time,
                "description": f"Introduce the topic of {topic} and its importance"
            },
            {
                "type": "direct_instruction",
                "duration_minutes": instruction_time,
                "description": f"Teach the core concepts of {topic}"
            },
            {
                "type": "guided_practice",
                "duration_minutes": practice_time,
                "description": "Work through examples together"
            },
            {
                "type": "independent_practice",
                "duration_minutes": practice_time,
                "description": "Students work on exercises independently"
            },
            {
                "type": "review",
                "duration_minutes": review_time,
                "description": "Review key concepts and answer questions"
            }
        ],
        "assessment": {
            "type": "formative",
            "methods": ["Exit ticket", "Class participation", "Worksheet completion"]
        },
        "differentiation": {
            "for_struggling_students": [
                "Provide additional examples",
                "Offer one-on-one support",
                "Use visual aids"
            ],
            "for_advanced_students": [
                "Provide extension activities",
                "Challenge with advanced problems",
                "Encourage to help peers"
            ]
        },
        "homework": {
            "description": f"Complete practice problems on {topic}",
            "estimated_time_minutes": 20,
            "resources": [
                f"{topic} practice worksheet",
                "Online practice problems",
                "Reading assignment"
            ]
        }
    }
    
    return lesson_plan
