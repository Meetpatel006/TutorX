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

@mcp.tool()
async def generate_quiz_tool(concept: str, difficulty: str = "medium") -> Dict[str, Any]:
    """
    Generate a quiz based on a concept and difficulty using Gemini.
    
    Args:
        concept: The concept to generate a quiz about
        difficulty: Difficulty level (easy, medium, hard)
        
    Returns:
        Dict containing the generated quiz in JSON format
    """
    try:
        # Validate inputs
        if not concept or not isinstance(concept, str):
            return {"error": "concept must be a non-empty string"}
            
        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty.lower() not in valid_difficulties:
            return {"error": f"difficulty must be one of {valid_difficulties}"}
            
        # Format the prompt
        prompt = PROMPT_TEMPLATE.format(
            concept=concept,
            difficulty=difficulty.lower()
        )
        
        # Generate quiz using Gemini
        response = await MODEL.generate_text(prompt, temperature=0.7)
        
        # Try to parse the JSON response
        try:
            # Extract JSON from markdown code block if present
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            else:
                json_str = response
                
            quiz_data = json.loads(json_str)
            return quiz_data
            
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse quiz response: {str(e)}", "raw_response": response}
            
    except Exception as e:
        return {"error": f"Error generating quiz: {str(e)}"}
