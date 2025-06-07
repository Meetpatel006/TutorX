# TutorX MCP Server
from mcp.server.fastmcp import FastMCP
import json
import os
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

# Filter out the tool registration warning
warnings.filterwarnings("ignore", message="Tool already exists")

# Import utility functions
from utils.multimodal import (
    process_text_query,
    process_voice_input,
    process_handwriting,
    generate_speech_response
)
from utils.assessment import (
    generate_question,
    evaluate_student_answer,
    generate_performance_analytics,
    detect_plagiarism
)

# Get server configuration from environment variables with defaults
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")  # Allow connections from any IP
SERVER_PORT = int(os.getenv("MCP_PORT", "8001"))
SERVER_TRANSPORT = os.getenv("MCP_TRANSPORT", "http")

# Create the TutorX MCP server with explicit configuration
mcp = FastMCP(
    "TutorX",
    dependencies=["mcp[cli]>=1.9.3", "gradio>=4.19.0", "numpy>=1.24.0", "pillow>=10.0.0"],
    host=SERVER_HOST,
    port=SERVER_PORT,
    transport=SERVER_TRANSPORT,
    cors_origins=["*"]  # Allow CORS from any origin
)

# Create FastAPI app
api_app = FastAPI()

# ------------------ Core Features ------------------

# Adaptive Learning Engine
@mcp.tool()
async def assess_skill(student_id: str, concept_id: str) -> Dict[str, Any]:
    """
    Assess student's skill level on a specific concept
    
    Args:
        student_id: The unique identifier for the student
        concept_id: The concept to assess
        
    Returns:
        Dictionary containing skill level and recommendations
    """
    try:
        # Simulated skill assessment
        return {
            "student_id": student_id,
            "concept_id": concept_id,
            "skill_level": 0.75,
            "confidence": 0.85,
            "recommendations": [
                "Practice more complex problems",
                "Review related concept: algebra_linear_equations"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@mcp.resource("concept-graph://")
async def get_concept_graph() -> Dict[str, Any]:
    """Get the full knowledge concept graph"""
    return {
        "nodes": [
            {"id": "math_algebra_basics", "name": "Algebra Basics", "difficulty": 1},
            {"id": "math_algebra_linear_equations", "name": "Linear Equations", "difficulty": 2},
            {"id": "math_algebra_quadratic_equations", "name": "Quadratic Equations", "difficulty": 3},
        ],
        "edges": [
            {"from": "math_algebra_basics", "to": "math_algebra_linear_equations", "weight": 1.0},
            {"from": "math_algebra_linear_equations", "to": "math_algebra_quadratic_equations", "weight": 0.8},
        ]
    }

@mcp.resource("learning-path://{student_id}")
async def get_learning_path(student_id: str) -> Dict[str, Any]:
    """Get personalized learning path for a student"""
    return {
        "student_id": student_id,
        "current_concepts": ["math_algebra_linear_equations"],
        "recommended_next": ["math_algebra_quadratic_equations"],
        "mastered": ["math_algebra_basics"],
        "estimated_completion_time": "2 weeks"
    }

# Assessment Suite
@mcp.tool()
async def generate_quiz(concept_ids: List[str], difficulty: int = 2) -> Dict[str, Any]:
    """
    Generate a quiz based on specified concepts and difficulty
    
    Args:
        concept_ids: List of concept IDs to include in the quiz
        difficulty: Difficulty level from 1-5
        
    Returns:
        Quiz object with questions and answers
    """
    return {
        "quiz_id": "q12345",
        "concept_ids": concept_ids,
        "difficulty": difficulty,
        "questions": [
            {
                "id": "q1",
                "text": "Solve for x: 2x + 3 = 7",
                "type": "algebraic_equation",
                "answer": "x = 2",
                "solution_steps": [
                    "2x + 3 = 7",
                    "2x = 7 - 3",
                    "2x = 4",
                    "x = 4/2 = 2"
                ]
            }
        ]
    }

@api_app.get("/api/assess_skill")
async def assess_skill_api(student_id: str = Query(...), concept_id: str = Query(...)):
    result = await assess_skill(student_id, concept_id)
    return JSONResponse(content=result)

@api_app.post("/api/generate_quiz")
async def generate_quiz_api(concept_ids: list[str], difficulty: int = 2):
    result = await generate_quiz(concept_ids, difficulty)
    return JSONResponse(content=result)

# Mount FastAPI app to MCP server
mcp.app = api_app

# Function to run the server
def run_server():
    """Run the MCP server with configured transport and port"""
    print(f"Starting TutorX MCP Server on {SERVER_HOST}:{SERVER_PORT} using {SERVER_TRANSPORT} transport...")
    try:
        mcp.run(transport="sse")
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise

if __name__ == "__main__":
    run_server()