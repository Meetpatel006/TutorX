"""
Quiz generation and interactive quiz tools for TutorX MCP.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp_server.mcp_instance import mcp
from model import GeminiFlash

# Load prompt template
PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / "quiz_generation.txt").read_text(encoding="utf-8")

# Initialize Gemini model
MODEL = GeminiFlash()

# In-memory storage for quiz sessions (in production, use a database)
QUIZ_SESSIONS = {}

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

        prompt = f"""Generate a {difficulty} quiz on the concept '{concept}'.
        Return a JSON object with the following structure:
        {{
          "quiz_id": "unique_quiz_id",
          "quiz_title": "Quiz about {concept}",
          "concept": "{concept}",
          "difficulty": "{difficulty}",
          "questions": [
            {{
              "question_id": "q1",
              "question": "...",
              "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
              "correct_answer": "A) ...",
              "explanation": "Detailed explanation of why this is correct and why others are wrong",
              "hint": "A helpful hint for struggling students"
            }}
          ]
        }}

        Generate 3-5 questions appropriate for {difficulty} difficulty level."""

        llm_response = await MODEL.generate_text(prompt, temperature=0.7)
        try:
            quiz_data = extract_json_from_text(llm_response)
            # Add unique quiz ID if not present
            if "quiz_id" not in quiz_data:
                quiz_data["quiz_id"] = str(uuid.uuid4())
            # Add question IDs if not present
            if "questions" in quiz_data:
                for i, question in enumerate(quiz_data["questions"]):
                    if "question_id" not in question:
                        question["question_id"] = f"q{i+1}"
        except Exception:
            quiz_data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
        return quiz_data
    except Exception as e:
        return {"error": f"Error generating quiz: {str(e)}"}


@mcp.tool()
async def start_interactive_quiz_tool(quiz_data: dict, student_id: str = "anonymous") -> dict:
    """
    Start an interactive quiz session for a student.
    """
    try:
        if not quiz_data or "questions" not in quiz_data:
            return {"error": "Invalid quiz data provided"}

        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "student_id": student_id,
            "quiz_data": quiz_data,
            "current_question": 0,
            "answers": {},
            "score": 0,
            "total_questions": len(quiz_data.get("questions", [])),
            "started_at": datetime.now().isoformat(),
            "completed": False
        }

        QUIZ_SESSIONS[session_id] = session

        # Return first question
        if session["total_questions"] > 0:
            first_question = quiz_data["questions"][0]
            return {
                "session_id": session_id,
                "quiz_title": quiz_data.get("quiz_title", "Quiz"),
                "total_questions": session["total_questions"],
                "current_question_number": 1,
                "question": {
                    "question_id": first_question.get("question_id"),
                    "question": first_question.get("question"),
                    "options": first_question.get("options", [])
                }
            }
        else:
            return {"error": "No questions found in quiz"}

    except Exception as e:
        return {"error": f"Error starting quiz session: {str(e)}"}


@mcp.tool()
async def submit_quiz_answer_tool(session_id: str, question_id: str, selected_answer: str) -> dict:
    """
    Submit an answer for a quiz question and get immediate feedback.
    """
    try:
        if session_id not in QUIZ_SESSIONS:
            return {"error": "Invalid session ID"}

        session = QUIZ_SESSIONS[session_id]
        if session["completed"]:
            return {"error": "Quiz already completed"}

        quiz_data = session["quiz_data"]
        questions = quiz_data.get("questions", [])
        current_q_index = session["current_question"]

        if current_q_index >= len(questions):
            return {"error": "No more questions available"}

        current_question = questions[current_q_index]

        # Check if this is the correct question
        if current_question.get("question_id") != question_id:
            return {"error": "Question ID mismatch"}

        # Evaluate answer
        correct_answer = current_question.get("correct_answer", "")
        is_correct = selected_answer.strip() == correct_answer.strip()

        # Store answer
        session["answers"][question_id] = {
            "selected": selected_answer,
            "correct": correct_answer,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }

        if is_correct:
            session["score"] += 1

        # Prepare feedback
        feedback = {
            "question_id": question_id,
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": current_question.get("explanation", ""),
            "score": session["score"],
            "total_questions": session["total_questions"]
        }

        # Move to next question
        session["current_question"] += 1

        # Check if quiz is completed
        if session["current_question"] >= session["total_questions"]:
            session["completed"] = True
            session["completed_at"] = datetime.now().isoformat()
            feedback["quiz_completed"] = True
            feedback["final_score"] = session["score"]
            feedback["percentage"] = round((session["score"] / session["total_questions"]) * 100, 1)
        else:
            # Get next question
            next_question = questions[session["current_question"]]
            feedback["next_question"] = {
                "question_id": next_question.get("question_id"),
                "question": next_question.get("question"),
                "options": next_question.get("options", []),
                "question_number": session["current_question"] + 1
            }

        return feedback

    except Exception as e:
        return {"error": f"Error submitting answer: {str(e)}"}


@mcp.tool()
async def get_quiz_hint_tool(session_id: str, question_id: str) -> dict:
    """
    Get a hint for the current quiz question.
    """
    try:
        if session_id not in QUIZ_SESSIONS:
            return {"error": "Invalid session ID"}

        session = QUIZ_SESSIONS[session_id]
        quiz_data = session["quiz_data"]
        questions = quiz_data.get("questions", [])

        # Find the question
        question = None
        for q in questions:
            if q.get("question_id") == question_id:
                question = q
                break

        if not question:
            return {"error": "Question not found"}

        hint = question.get("hint", "No hint available for this question.")

        return {
            "question_id": question_id,
            "hint": hint
        }

    except Exception as e:
        return {"error": f"Error getting hint: {str(e)}"}


@mcp.tool()
async def get_quiz_session_status_tool(session_id: str) -> dict:
    """
    Get the current status of a quiz session.
    """
    try:
        if session_id not in QUIZ_SESSIONS:
            return {"error": "Invalid session ID"}

        session = QUIZ_SESSIONS[session_id]

        return {
            "session_id": session_id,
            "student_id": session["student_id"],
            "quiz_title": session["quiz_data"].get("quiz_title", "Quiz"),
            "current_question": session["current_question"] + 1,
            "total_questions": session["total_questions"],
            "score": session["score"],
            "completed": session["completed"],
            "started_at": session["started_at"],
            "completed_at": session.get("completed_at"),
            "answers": session["answers"]
        }

    except Exception as e:
        return {"error": f"Error getting session status: {str(e)}"}
