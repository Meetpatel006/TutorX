"""
Lesson generation tools for TutorX MCP.
"""
from typing import Dict, Any, List
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash
import json

MODEL = GeminiFlash()

def clean_json_trailing_commas(json_text: str) -> str:
    import re
    return re.sub(r',([ \t\r\n]*[}}\]])', r'\1', json_text)

def extract_json_from_text(text: str):
    import re, json
    if not text or not isinstance(text, str):
        return None
    # Remove code fences
    text = re.sub(r'^\s*```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
    text = text.strip()
    # Remove trailing commas
    cleaned = clean_json_trailing_commas(text)
    return json.loads(cleaned)

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
        data = extract_json_from_text(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data
