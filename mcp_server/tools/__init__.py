"""
TutorX MCP Tools

This module contains all the MCP tools for the TutorX application.
"""

# Import all tools to make them available when importing the package
from .concept_tools import get_concept_tool, assess_skill_tool  # noqa
from .concept_graph_tools import get_concept_graph_tool  # noqa
from .lesson_tools import generate_lesson_tool  # noqa
from .quiz_tools import (  # noqa
    generate_quiz_tool,
    start_interactive_quiz_tool,
    submit_quiz_answer_tool,
    get_quiz_hint_tool,
    get_quiz_session_status_tool
)
from .interaction_tools import text_interaction, check_submission_originality  # noqa
from .ocr_tools import mistral_document_ocr  # noqa
from .learning_path_tools import (  # noqa
    get_learning_path,
    # Enhanced Adaptive Learning Tools with Gemini Integration
    generate_adaptive_content,
    analyze_learning_patterns,
    optimize_learning_strategy,
    start_adaptive_session,
    record_learning_event,
    get_adaptive_recommendations,
    get_adaptive_learning_path,
    get_student_progress_summary
)

__all__ = [
    # Concept tools
    'get_concept_tool',
    'assess_skill_tool',
    'get_concept_graph_tool',

    # Lesson tools
    'generate_lesson_tool',

    # Quiz tools
    'generate_quiz_tool',

    # Interaction tools
    'text_interaction',
    'check_submission_originality',

    # OCR tools
    'mistral_document_ocr',

    # Learning path tools
    'get_learning_path',

    # Enhanced Adaptive Learning Tools with Gemini Integration
    'generate_adaptive_content',
    'analyze_learning_patterns',
    'optimize_learning_strategy',
    'start_adaptive_session',
    'record_learning_event',
    'get_adaptive_recommendations',
    'get_adaptive_learning_path',
    'get_student_progress_summary',
]
