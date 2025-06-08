"""
TutorX MCP Server

This is the main entry point for the TutorX MCP server.
"""
import base64
import os
import sys
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# Import all tools to register them with MCP
from tools import (
    concept_tools,
    lesson_tools,
    quiz_tools,
    interaction_tools,
    ocr_tools,
    learning_path_tools
)

# Import resources
from resources import concept_graph, curriculum_standards

# Create FastAPI app
api_app = FastAPI(
    title="TutorX MCP Server",
    description="Model Context Protocol server for TutorX educational platform",
    version="1.0.0"
)

# Add CORS middleware
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the shared mcp instance
from mcp_server.mcp_instance import mcp

# Explicitly import all tool modules so their @mcp.tool() decorators run
from mcp_server.tools import concept_tools
from mcp_server.tools import lesson_tools
from mcp_server.tools import quiz_tools
from mcp_server.tools import interaction_tools
from mcp_server.tools import ocr_tools
from mcp_server.tools import learning_path_tools
from mcp_server.tools import concept_graph_tools

# Mount the SSE transport for MCP at '/sse/' (with trailing slash)
api_app.mount("/sse", mcp.sse_app())

# Health check endpoint
@api_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tutorx-mcp"}

# API endpoints - Concepts
@api_app.get("/api/concept_graph")
async def get_concept_graph(concept_id: str = None):
    if concept_id:
        concept = concept_graph.get_concept(concept_id)
        if not concept:
            raise HTTPException(status_code=404, detail={"error": f"Concept {concept_id} not found"})
        return concept
    return {"concepts": list(concept_graph.get_concept_graph().values())}

@api_app.get("/api/concept/{concept_id}")
async def get_concept_endpoint(concept_id: str):
    concept = concept_graph.get_concept(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept {concept_id} not found")
    return concept

@api_app.get("/api/concepts")
async def list_concepts():
    return concept_graph.get_all_concepts()

# API endpoints - Curriculum Standards
@api_app.get("/api/curriculum-standards")
async def get_curriculum_standards(country: str = "us"):
    return curriculum_standards.get_curriculum_standards(country)

# API endpoints - Text Interaction
@api_app.post("/api/text-interaction")
async def text_interaction_endpoint(request: dict):
    query = request.get("query")
    student_id = request.get("student_id")
    if not query or not student_id:
        raise HTTPException(status_code=400, detail="Both query and student_id are required")
    return await interaction_tools.text_interaction(query, student_id)

# API endpoints - Submission Originality Check
@api_app.post("/api/check-originality")
async def check_originality_endpoint(request: dict):
    submission = request.get("submission")
    reference_sources = request.get("reference_sources", [])
    if not submission or not isinstance(reference_sources, list):
        raise HTTPException(status_code=400, detail="submission (string) and reference_sources (array) are required")
    return await interaction_tools.check_submission_originality(submission, reference_sources)

# API endpoints - PDF OCR
@api_app.post("/api/pdf-ocr")
async def pdf_ocr_endpoint(
    file: UploadFile = File(...),
    filename: str = Form(None)
):
    try:
        pdf_data = await file.read()
        pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
        result = await ocr_tools.pdf_ocr({
            "pdf_data": pdf_b64,
            "filename": filename or file.filename
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API endpoints - Learning Path
@api_app.post("/api/learning-path")
async def learning_path_endpoint(request: dict):
    student_id = request.get("student_id")
    concept_ids = request.get("concept_ids", [])
    student_level = request.get("student_level")
    if not student_id or not concept_ids:
        raise HTTPException(status_code=400, detail="student_id and concept_ids are required")
    return await learning_path_tools.get_learning_path(
        student_id=student_id,
        concept_ids=concept_ids,
        student_level=student_level
    )

# API endpoints - Assess Skill
from tools.concept_tools import assess_skill_tool
@api_app.post("/api/assess-skill")
async def assess_skill_endpoint(request: dict):
    student_id = request.get("student_id")
    concept_id = request.get("concept_id")
    if not student_id or not concept_id:
        raise HTTPException(status_code=400, detail="Both student_id and concept_id are required")
    return await assess_skill_tool(student_id, concept_id)

# API endpoints - Generate Lesson
from tools.lesson_tools import generate_lesson_tool
@api_app.post("/api/generate-lesson")
async def generate_lesson_endpoint(request: dict):
    topic = request.get("topic")
    grade_level = request.get("grade_level")
    duration_minutes = request.get("duration_minutes")
    if not topic or grade_level is None or duration_minutes is None:
        raise HTTPException(status_code=400, detail="topic, grade_level, and duration_minutes are required")
    return await generate_lesson_tool(topic, grade_level, duration_minutes)

# API endpoints - Generate Quiz
from tools.quiz_tools import generate_quiz_tool
@api_app.post("/api/generate-quiz")
async def generate_quiz_endpoint(request: dict):
    concept = request.get("concept", "")
    difficulty = request.get("difficulty", 2)
    if not concept or not isinstance(concept, str) or not concept.strip():
        raise HTTPException(status_code=400, detail="concept must be a non-empty string")
    if isinstance(difficulty, (int, float)):
        if difficulty <= 2:
            difficulty = "easy"
        elif difficulty <= 4:
            difficulty = "medium"
        else:
            difficulty = "hard"
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"
    return await generate_quiz_tool(concept.strip(), difficulty)

# Entrypoint for running with MCP SSE transport
if __name__ == "__main__":
    mcp.run(transport="sse")
