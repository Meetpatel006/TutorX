"""
Text interaction and submission checking tools for TutorX.
"""
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash
import json

MODEL = GeminiFlash()

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate the similarity ratio between two texts."""
    return 0.0  # No longer used, LLM-driven

@mcp.tool()
async def text_interaction(query: str, student_id: str) -> dict:
    """
    Process a text query from a student and provide an educational response, fully LLM-driven.
    Use Gemini to generate a JSON object with a response and suggested actions/resources.
    """
    prompt = (
        f"A student (ID: {student_id}) asked: '{query}'. "
        f"Return a JSON object with fields: response (string), suggested_actions (list of strings), and suggested_resources (list of strings)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = json.loads(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data

@mcp.tool()
async def check_submission_originality(submission: str, reference_sources: list) -> dict:
    """
    Check a student's submission for potential plagiarism, fully LLM-driven.
    Use Gemini to generate a JSON object with originality_score (0-1), is_original (bool), and recommendations (list of strings).
    """
    prompt = (
        f"Given the following student submission: '{submission}' and reference sources: {reference_sources}, "
        f"return a JSON object with fields: originality_score (float 0-1), is_original (bool), and recommendations (list of strings)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = json.loads(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data
