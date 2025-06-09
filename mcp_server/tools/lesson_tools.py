"""
Lesson generation tools for TutorX MCP.
"""
from typing import Dict, Any, List
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash
import json

MODEL = GeminiFlash()

@mcp.tool()
async def generate_lesson_tool(topic: str, grade_level: int, duration_minutes: int) -> dict:
    """
    Generate a lesson plan for the given topic, grade level, and duration, fully LLM-driven.
    Use Gemini to generate a JSON object with objectives, activities, materials, assessment, differentiation, and homework.
    """
    prompt = (
        f"Generate a detailed lesson plan as a JSON object for the topic '{topic}', grade {grade_level}, duration {duration_minutes} minutes. "
        f"Include fields: objectives (list), activities (list), materials (list), assessment (dict), differentiation (dict), and homework (dict)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = json.loads(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data
