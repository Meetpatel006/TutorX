"""
Concept-related MCP tools for TutorX.
"""
import random
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os
from pathlib import Path
import json
import re

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))


# Import from local resources
try:
    from resources.concept_graph import get_concept, get_all_concepts
except ImportError:
    # Fallback for when running from different contexts
    def get_concept(concept_id):
        return {"id": concept_id, "name": concept_id.replace("_", " ").title(), "description": f"Description for {concept_id}"}

    def get_all_concepts():
        return {
            "algebra_basics": {"id": "algebra_basics", "name": "Algebra Basics", "description": "Basic algebraic concepts"},
            "linear_equations": {"id": "linear_equations", "name": "Linear Equations", "description": "Solving linear equations"}
        }

# Import MCP
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash

MODEL = GeminiFlash()

def clean_json_trailing_commas(json_text: str) -> str:
    return re.sub(r',([ \t\r\n]*[}}\]])', r'\1', json_text)

def extract_json_from_text(text: str):
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
async def get_concept_tool(concept_id: str = None) -> dict:
    """
    Get a specific concept or all concepts from the knowledge graph, fully LLM-driven.
    If a concept_id is provided, use Gemini to generate a JSON object with explanation, key points, and example.
    """
    if not concept_id:
        return {"error": "concept_id is required for LLM-driven mode"}
    prompt = (
        f"Explain the concept '{concept_id}' in detail. "
        f"Return a JSON object with fields: explanation (string), key_points (list of strings), and example (string)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = extract_json_from_text(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data

@mcp.tool()
async def assess_skill_tool(student_id: str, concept_id: str) -> dict:
    """
    Assess a student's understanding of a specific concept, fully LLM-driven.
    Use Gemini to generate a JSON object with a score (0-1), feedback, and recommendations.
    """
    prompt = (
        f"A student (ID: {student_id}) is being assessed on the concept '{concept_id}'. "
        f"Generate a JSON object with: score (float 0-1), feedback (string), and recommendations (list of strings)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = extract_json_from_text(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data
