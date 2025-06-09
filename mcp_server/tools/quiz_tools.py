"""
Quiz generation tools for TutorX MCP.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp_server.mcp_instance import mcp
from model import GeminiFlash

# Load prompt template
PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / "quiz_generation.txt").read_text(encoding="utf-8")

# Initialize Gemini model
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
async def generate_quiz_tool(concept: str, difficulty: str = "medium") -> dict:
    """
    Generate a quiz based on a concept and difficulty using Gemini, fully LLM-driven.
    The JSON should include a list of questions, each with options and the correct answer.
    """
    try:
        if not concept or not isinstance(concept, str):
            return {"error": "concept must be a non-empty string"}
        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty.lower() not in valid_difficulties:
            return {"error": f"difficulty must be one of {valid_difficulties}"}
        prompt = (
            f"Generate a {difficulty} quiz on the concept '{concept}'. "
            f"Return a JSON object with a 'questions' field: a list of questions, each with 'question', 'options' (list), and 'answer'."
        )
        llm_response = await MODEL.generate_text(prompt, temperature=0.7)
        try:
            quiz_data = extract_json_from_text(llm_response)
        except Exception:
            quiz_data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
        return quiz_data
    except Exception as e:
        return {"error": f"Error generating quiz: {str(e)}"}
