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
from mcp_server.tools import ai_tutor_tools
from mcp_server.tools import content_generation_tools


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

# API endpoints - Document OCR
@api_app.post("/api/document-ocr")
async def document_ocr_endpoint(
    file: UploadFile = File(...)
):
    try:
        # Save the uploaded file to a temporary location
        import tempfile
        import os
        
        # Get the file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Create a temporary file with the same extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Upload the file to storage and get the URL
            from mcp_server.utils.azure_upload import upload_to_azure
            document_url = upload_to_azure(temp_file_path)
            
            # Process the document with OCR
            result = await ocr_tools.mistral_document_ocr(document_url)
            return result
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

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
from mcp_server.tools.concept_tools import assess_skill_tool
@api_app.post("/api/assess-skill")
async def assess_skill_endpoint(request: dict):
    student_id = request.get("student_id")
    concept_id = request.get("concept_id")
    if not student_id or not concept_id:
        raise HTTPException(status_code=400, detail="Both student_id and concept_id are required")
    return await assess_skill_tool(student_id, concept_id)

# API endpoints - Generate Lesson
from mcp_server.tools.lesson_tools import generate_lesson_tool
@api_app.post("/api/generate-lesson")
async def generate_lesson_endpoint(request: dict):
    topic = request.get("topic")
    grade_level = request.get("grade_level")
    duration_minutes = request.get("duration_minutes")
    if not topic or grade_level is None or duration_minutes is None:
        raise HTTPException(status_code=400, detail="topic, grade_level, and duration_minutes are required")
    return await generate_lesson_tool(topic, grade_level, duration_minutes)

# API endpoints - Generate Quiz
from mcp_server.tools.quiz_tools import (
    generate_quiz_tool,
    start_interactive_quiz_tool,
    submit_quiz_answer_tool,
    get_quiz_hint_tool,
    get_quiz_session_status_tool
)

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

@api_app.post("/api/start-interactive-quiz")
async def start_interactive_quiz_endpoint(request: dict):
    quiz_data = request.get("quiz_data")
    student_id = request.get("student_id", "anonymous")
    if not quiz_data:
        raise HTTPException(status_code=400, detail="quiz_data is required")
    return await start_interactive_quiz_tool(quiz_data, student_id)

@api_app.post("/api/submit-quiz-answer")
async def submit_quiz_answer_endpoint(request: dict):
    session_id = request.get("session_id")
    question_id = request.get("question_id")
    selected_answer = request.get("selected_answer")
    if not all([session_id, question_id, selected_answer]):
        raise HTTPException(status_code=400, detail="session_id, question_id, and selected_answer are required")
    return await submit_quiz_answer_tool(session_id, question_id, selected_answer)

@api_app.post("/api/get-quiz-hint")
async def get_quiz_hint_endpoint(request: dict):
    session_id = request.get("session_id")
    question_id = request.get("question_id")
    if not all([session_id, question_id]):
        raise HTTPException(status_code=400, detail="session_id and question_id are required")
    return await get_quiz_hint_tool(session_id, question_id)

@api_app.post("/api/get-quiz-session-status")
async def get_quiz_session_status_endpoint(request: dict):
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return await get_quiz_session_status_tool(session_id)

# API endpoints - AI Tutoring
from mcp_server.tools.ai_tutor_tools import (
    start_tutoring_session,
    ai_tutor_chat,
    get_step_by_step_guidance,
    get_alternative_explanations,
    update_student_understanding,
    get_tutoring_session_status,
    end_tutoring_session,
    list_active_tutoring_sessions
)

@api_app.post("/api/start-tutoring-session")
async def start_tutoring_session_endpoint(request: dict):
    student_id = request.get("student_id")
    subject = request.get("subject", "general")
    learning_objectives = request.get("learning_objectives", [])
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id is required")
    return await start_tutoring_session(student_id, subject, learning_objectives)

@api_app.post("/api/ai-tutor-chat")
async def ai_tutor_chat_endpoint(request: dict):
    session_id = request.get("session_id")
    student_query = request.get("student_query")
    request_type = request.get("request_type", "explanation")
    if not session_id or not student_query:
        raise HTTPException(status_code=400, detail="session_id and student_query are required")
    return await ai_tutor_chat(session_id, student_query, request_type)

@api_app.post("/api/step-by-step-guidance")
async def step_by_step_guidance_endpoint(request: dict):
    session_id = request.get("session_id")
    concept = request.get("concept")
    current_step = request.get("current_step", 1)
    if not session_id or not concept:
        raise HTTPException(status_code=400, detail="session_id and concept are required")
    return await get_step_by_step_guidance(session_id, concept, current_step)

@api_app.post("/api/alternative-explanations")
async def alternative_explanations_endpoint(request: dict):
    session_id = request.get("session_id")
    concept = request.get("concept")
    explanation_types = request.get("explanation_types", [])
    if not session_id or not concept:
        raise HTTPException(status_code=400, detail="session_id and concept are required")
    return await get_alternative_explanations(session_id, concept, explanation_types)

@api_app.post("/api/update-student-understanding")
async def update_student_understanding_endpoint(request: dict):
    session_id = request.get("session_id")
    concept = request.get("concept")
    understanding_level = request.get("understanding_level")
    feedback = request.get("feedback", "")
    if not session_id or not concept or understanding_level is None:
        raise HTTPException(status_code=400, detail="session_id, concept, and understanding_level are required")
    return await update_student_understanding(session_id, concept, understanding_level, feedback)

@api_app.get("/api/tutoring-session-status/{session_id}")
async def tutoring_session_status_endpoint(session_id: str):
    return await get_tutoring_session_status(session_id)

@api_app.post("/api/end-tutoring-session")
async def end_tutoring_session_endpoint(request: dict):
    session_id = request.get("session_id")
    session_summary = request.get("session_summary", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return await end_tutoring_session(session_id, session_summary)

@api_app.get("/api/active-tutoring-sessions")
async def active_tutoring_sessions_endpoint(student_id: str = None):
    return await list_active_tutoring_sessions(student_id)

# API endpoints - Content Generation
from mcp_server.tools.content_generation_tools import (
    generate_interactive_exercise,
    generate_adaptive_content_sequence,
    generate_scenario_based_learning,
    generate_multimodal_content,
    generate_adaptive_assessment,
    generate_gamified_content,
    validate_generated_content
)

@api_app.post("/api/generate-interactive-exercise")
async def generate_interactive_exercise_endpoint(request: dict):
    concept = request.get("concept")
    exercise_type = request.get("exercise_type", "problem_solving")
    difficulty_level = request.get("difficulty_level", 0.5)
    student_level = request.get("student_level", "intermediate")
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    return await generate_interactive_exercise(concept, exercise_type, difficulty_level, student_level)

@api_app.post("/api/generate-adaptive-content-sequence")
async def generate_adaptive_content_sequence_endpoint(request: dict):
    topic = request.get("topic")
    student_profile = request.get("student_profile", {})
    sequence_length = request.get("sequence_length", 5)
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    return await generate_adaptive_content_sequence(topic, student_profile, sequence_length)

@api_app.post("/api/generate-scenario-based-learning")
async def generate_scenario_based_learning_endpoint(request: dict):
    concept = request.get("concept")
    scenario_type = request.get("scenario_type", "real_world")
    complexity_level = request.get("complexity_level", "moderate")
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    return await generate_scenario_based_learning(concept, scenario_type, complexity_level)

@api_app.post("/api/generate-multimodal-content")
async def generate_multimodal_content_endpoint(request: dict):
    concept = request.get("concept")
    modalities = request.get("modalities", ["visual", "auditory", "kinesthetic", "reading"])
    target_audience = request.get("target_audience", "general")
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    return await generate_multimodal_content(concept, modalities, target_audience)

@api_app.post("/api/generate-adaptive-assessment")
async def generate_adaptive_assessment_endpoint(request: dict):
    concept = request.get("concept")
    assessment_type = request.get("assessment_type", "formative")
    student_data = request.get("student_data", {})
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    return await generate_adaptive_assessment(concept, assessment_type, student_data)

@api_app.post("/api/generate-gamified-content")
async def generate_gamified_content_endpoint(request: dict):
    concept = request.get("concept")
    game_type = request.get("game_type", "quest")
    target_age_group = request.get("target_age_group", "teen")
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    return await generate_gamified_content(concept, game_type, target_age_group)

@api_app.post("/api/validate-content")
async def validate_content_endpoint(request: dict):
    content_data = request.get("content_data")
    validation_criteria = request.get("validation_criteria", {})
    if not content_data:
        raise HTTPException(status_code=400, detail="content_data is required")
    return await validate_generated_content(content_data, validation_criteria)

# Entrypoint for running with MCP SSE transport
if __name__ == "__main__":
    mcp.run(transport="sse")
