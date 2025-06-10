"""
Contextualized AI Tutoring tools for TutorX.
Provides step-by-step guidance, alternative explanations, and conversational AI tutoring.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash

MODEL = GeminiFlash()

# Tutoring session storage
tutoring_sessions = {}

def extract_json_from_text(text: str):
    """Extract JSON from text response"""
    import re
    if not text or not isinstance(text, str):
        return None
    # Remove code fences
    text = re.sub(r'^\s*```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
    text = text.strip()
    # Remove trailing commas
    text = re.sub(r',([ \t\r\n]*[}}\]])', r'\1', text)
    return json.loads(text)

class TutoringSession:
    """Manages a tutoring session with context and memory"""
    
    def __init__(self, session_id: str, student_id: str, subject: str = "general"):
        self.session_id = session_id
        self.student_id = student_id
        self.subject = subject
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.conversation_history = []
        self.current_topic = None
        self.learning_objectives = []
        self.student_understanding_level = 0.5  # 0.0 to 1.0
        self.preferred_explanation_style = "detailed"  # detailed, simple, visual, step-by-step
        self.difficulty_preference = 0.5  # 0.0 to 1.0
        
    def add_interaction(self, query: str, response: str, interaction_type: str = "question"):
        """Add an interaction to the session history"""
        self.conversation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "type": interaction_type,
            "understanding_level": self.student_understanding_level
        })
        self.last_activity = datetime.utcnow()
        
    def get_context_summary(self) -> str:
        """Generate a context summary for the AI tutor"""
        recent_interactions = self.conversation_history[-5:]  # Last 5 interactions
        
        context = f"""
        Session Context:
        - Student ID: {self.student_id}
        - Subject: {self.subject}
        - Current Topic: {self.current_topic or 'Not specified'}
        - Understanding Level: {self.student_understanding_level:.2f}/1.0
        - Preferred Style: {self.preferred_explanation_style}
        - Session Duration: {(datetime.utcnow() - self.created_at).total_seconds() / 60:.1f} minutes
        
        Recent Conversation:
        """
        
        for interaction in recent_interactions:
            context += f"\nStudent: {interaction['query']}\nTutor: {interaction['response'][:100]}...\n"
            
        return context

@mcp.tool()
async def start_tutoring_session(student_id: str, subject: str = "general", 
                               learning_objectives: List[str] = None) -> dict:
    """
    Start a new AI tutoring session with context management.
    
    Args:
        student_id: Student identifier
        subject: Subject area for tutoring
        learning_objectives: List of learning objectives for the session
        
    Returns:
        Dictionary with session information
    """
    try:
        session_id = str(uuid.uuid4())
        session = TutoringSession(session_id, student_id, subject)
        
        if learning_objectives:
            session.learning_objectives = learning_objectives
            
        tutoring_sessions[session_id] = session
        
        # Generate welcome message
        prompt = f"""
        You are an expert AI tutor starting a new tutoring session.
        
        Student ID: {student_id}
        Subject: {subject}
        Learning Objectives: {learning_objectives or 'To be determined based on student needs'}
        
        Generate a welcoming introduction that:
        1. Welcomes the student warmly
        2. Explains your role as their AI tutor
        3. Asks about their current understanding or what they'd like to learn
        4. Sets expectations for the tutoring session
        
        Return a JSON object with:
        - "welcome_message": friendly welcome text
        - "suggested_topics": list of 3-5 topics they might want to explore
        - "session_guidelines": brief explanation of how the tutoring works
        """
        
        response = await MODEL.generate_text(prompt, temperature=0.7)
        welcome_data = extract_json_from_text(response)
        
        return {
            "success": True,
            "session_id": session_id,
            "student_id": student_id,
            "subject": subject,
            "created_at": session.created_at.isoformat(),
            **welcome_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start tutoring session: {str(e)}"
        }

@mcp.tool()
async def ai_tutor_chat(session_id: str, student_query: str, 
                       request_type: str = "explanation") -> dict:
    """
    Process student query with contextualized AI tutoring.
    
    Args:
        session_id: Active tutoring session ID
        student_query: Student's question or request
        request_type: Type of request ('explanation', 'step_by_step', 'alternative', 'practice', 'clarification')
        
    Returns:
        Dictionary with tutor response and guidance
    """
    try:
        if session_id not in tutoring_sessions:
            return {
                "success": False,
                "error": "Invalid session ID. Please start a new tutoring session."
            }
            
        session = tutoring_sessions[session_id]
        context = session.get_context_summary()
        
        # Analyze student query to understand their needs
        analysis_prompt = f"""
        Analyze this student query in the context of their tutoring session:
        
        {context}
        
        Student Query: "{student_query}"
        Request Type: {request_type}
        
        Analyze and return JSON with:
        - "topic_identified": main topic/concept the student is asking about
        - "difficulty_level": estimated difficulty (0.0 to 1.0)
        - "understanding_gaps": potential areas where student might be confused
        - "prerequisite_concepts": concepts student should know first
        - "confidence_level": how confident the student seems (0.0 to 1.0)
        """
        
        analysis_response = await MODEL.generate_text(analysis_prompt, temperature=0.3)
        analysis = extract_json_from_text(analysis_response)
        
        # Update session context based on analysis
        if analysis and "topic_identified" in analysis:
            session.current_topic = analysis["topic_identified"]
            if "difficulty_level" in analysis:
                session.difficulty_preference = analysis["difficulty_level"]
        
        # Generate appropriate response based on request type
        if request_type == "step_by_step":
            response_prompt = f"""
            {context}
            
            The student asked: "{student_query}"
            
            Provide a detailed step-by-step explanation that:
            1. Breaks down the concept into manageable steps
            2. Uses simple, clear language appropriate for their level
            3. Includes examples for each step
            4. Checks understanding at key points
            5. Provides encouragement and support
            
            Return JSON with:
            - "step_by_step_explanation": detailed step-by-step guide
            - "key_steps": list of main steps with brief descriptions
            - "examples": relevant examples for each step
            - "check_points": questions to verify understanding
            - "encouragement": supportive message
            """
        elif request_type == "alternative":
            response_prompt = f"""
            {context}
            
            The student asked: "{student_query}"
            
            Provide alternative explanations using different approaches:
            1. Visual/spatial explanation
            2. Analogy-based explanation
            3. Real-world application
            4. Simplified version
            
            Return JSON with:
            - "visual_explanation": explanation using visual/spatial concepts
            - "analogy_explanation": explanation using familiar analogies
            - "real_world_application": how this applies in real life
            - "simplified_version": very simple explanation
            - "which_works_best": question asking which explanation resonates
            """
        else:  # Default explanation
            response_prompt = f"""
            {context}
            
            The student asked: "{student_query}"
            
            Provide a comprehensive, personalized explanation that:
            1. Addresses their specific question directly
            2. Builds on their current understanding level
            3. Uses their preferred explanation style
            4. Includes relevant examples
            5. Suggests next steps for learning
            
            Return JSON with:
            - "main_explanation": comprehensive answer to their question
            - "key_concepts": important concepts to remember
            - "examples": relevant examples
            - "next_steps": suggested follow-up activities
            - "related_topics": topics they might want to explore next
            """
        
        tutor_response = await MODEL.generate_text(response_prompt, temperature=0.7)
        response_data = extract_json_from_text(tutor_response)
        
        # Add interaction to session history
        session.add_interaction(
            student_query, 
            response_data.get("main_explanation", str(response_data)), 
            request_type
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "request_type": request_type,
            "analysis": analysis,
            "response": response_data,
            "session_stats": {
                "interactions_count": len(session.conversation_history),
                "current_topic": session.current_topic,
                "understanding_level": session.student_understanding_level
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process tutoring request: {str(e)}"
        }

@mcp.tool()
async def get_step_by_step_guidance(session_id: str, concept: str,
                                  current_step: int = 1) -> dict:
    """
    Provide detailed step-by-step guidance for learning a specific concept.

    Args:
        session_id: Active tutoring session ID
        concept: The concept to provide guidance for
        current_step: Current step the student is on (1-based)

    Returns:
        Dictionary with step-by-step guidance
    """
    try:
        if session_id not in tutoring_sessions:
            return {
                "success": False,
                "error": "Invalid session ID. Please start a new tutoring session."
            }

        session = tutoring_sessions[session_id]
        context = session.get_context_summary()

        prompt = f"""
        {context}

        Provide comprehensive step-by-step guidance for learning: "{concept}"
        Current step: {current_step}

        Create a structured learning path that:
        1. Breaks the concept into logical, sequential steps
        2. Provides clear explanations for each step
        3. Includes practice exercises for each step
        4. Offers multiple ways to understand each step
        5. Includes checkpoints to verify understanding

        Return JSON with:
        - "total_steps": total number of steps needed
        - "current_step_details": detailed information about the current step
        - "step_explanation": clear explanation of the current step
        - "practice_exercises": 2-3 practice problems for this step
        - "key_points": important points to remember
        - "common_mistakes": common mistakes students make at this step
        - "next_step_preview": brief preview of what comes next
        - "prerequisite_check": what student should know before this step
        - "mastery_indicators": how to know if student has mastered this step
        """

        response = await MODEL.generate_text(prompt, temperature=0.6)
        guidance_data = extract_json_from_text(response)

        return {
            "success": True,
            "session_id": session_id,
            "concept": concept,
            "current_step": current_step,
            "guidance": guidance_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate step-by-step guidance: {str(e)}"
        }

@mcp.tool()
async def get_alternative_explanations(session_id: str, concept: str,
                                     explanation_types: List[str] = None) -> dict:
    """
    Generate alternative explanations for a concept using different approaches.

    Args:
        session_id: Active tutoring session ID
        concept: The concept to explain
        explanation_types: Types of explanations to generate

    Returns:
        Dictionary with alternative explanations
    """
    try:
        if session_id not in tutoring_sessions:
            return {
                "success": False,
                "error": "Invalid session ID. Please start a new tutoring session."
            }

        session = tutoring_sessions[session_id]
        context = session.get_context_summary()

        if not explanation_types:
            explanation_types = ["visual", "analogy", "real_world", "simplified", "technical"]

        prompt = f"""
        {context}

        Generate multiple alternative explanations for: "{concept}"

        Create explanations using these approaches: {explanation_types}

        For each explanation type, provide:
        1. A complete explanation using that approach
        2. Key benefits of this explanation style
        3. When this explanation works best
        4. Supporting examples or analogies

        Return JSON with:
        - "visual_explanation": explanation using visual/spatial concepts and imagery
        - "analogy_explanation": explanation using familiar analogies and metaphors
        - "real_world_explanation": explanation showing real-world applications
        - "simplified_explanation": very simple, basic explanation
        - "technical_explanation": detailed, technical explanation
        - "story_explanation": explanation told as a story or narrative
        - "comparison_explanation": explanation comparing to similar concepts
        - "recommendation": which explanation might work best for this student
        """

        response = await MODEL.generate_text(prompt, temperature=0.7)
        explanations_data = extract_json_from_text(response)

        return {
            "success": True,
            "session_id": session_id,
            "concept": concept,
            "explanation_types": explanation_types,
            "explanations": explanations_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate alternative explanations: {str(e)}"
        }

@mcp.tool()
async def update_student_understanding(session_id: str, concept: str,
                                     understanding_level: float,
                                     feedback: str = "") -> dict:
    """
    Update student's understanding level and adapt tutoring accordingly.

    Args:
        session_id: Active tutoring session ID
        concept: The concept being learned
        understanding_level: Student's understanding level (0.0 to 1.0)
        feedback: Optional feedback from student

    Returns:
        Dictionary with updated session information and recommendations
    """
    try:
        if session_id not in tutoring_sessions:
            return {
                "success": False,
                "error": "Invalid session ID. Please start a new tutoring session."
            }

        session = tutoring_sessions[session_id]

        # Update session understanding level
        session.student_understanding_level = understanding_level
        session.current_topic = concept

        # Generate adaptive recommendations based on understanding level
        prompt = f"""
        Student understanding update:
        - Concept: {concept}
        - Understanding Level: {understanding_level:.2f}/1.0
        - Student Feedback: {feedback or 'No feedback provided'}
        - Session Context: {session.get_context_summary()}

        Based on this understanding level, provide adaptive recommendations:

        Return JSON with:
        - "understanding_assessment": assessment of student's current understanding
        - "next_actions": recommended next steps based on understanding level
        - "difficulty_adjustment": how to adjust difficulty (easier/harder/same)
        - "focus_areas": specific areas that need more attention
        - "encouragement": encouraging message appropriate for their level
        - "study_strategies": personalized study strategies
        - "time_estimate": estimated time to reach mastery
        """

        response = await MODEL.generate_text(prompt, temperature=0.6)
        recommendations_data = extract_json_from_text(response)

        # Add this update to conversation history
        session.add_interaction(
            f"Understanding update for {concept}: {understanding_level:.2f}",
            f"Updated understanding and provided recommendations",
            "understanding_update"
        )

        return {
            "success": True,
            "session_id": session_id,
            "concept": concept,
            "updated_understanding_level": understanding_level,
            "recommendations": recommendations_data,
            "session_stats": {
                "interactions_count": len(session.conversation_history),
                "current_topic": session.current_topic,
                "understanding_level": session.student_understanding_level
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update understanding: {str(e)}"
        }

@mcp.tool()
async def get_tutoring_session_status(session_id: str) -> dict:
    """
    Get the current status and context of a tutoring session.

    Args:
        session_id: Tutoring session ID

    Returns:
        Dictionary with session status and statistics
    """
    try:
        if session_id not in tutoring_sessions:
            return {
                "success": False,
                "error": "Session not found"
            }

        session = tutoring_sessions[session_id]

        return {
            "success": True,
            "session_id": session_id,
            "student_id": session.student_id,
            "subject": session.subject,
            "current_topic": session.current_topic,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "duration_minutes": (datetime.utcnow() - session.created_at).total_seconds() / 60,
            "understanding_level": session.student_understanding_level,
            "preferred_style": session.preferred_explanation_style,
            "learning_objectives": session.learning_objectives,
            "interaction_count": len(session.conversation_history),
            "recent_topics": list(set([
                interaction.get("query", "")[:50]
                for interaction in session.conversation_history[-5:]
            ]))
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get session status: {str(e)}"
        }

@mcp.tool()
async def end_tutoring_session(session_id: str, session_summary: str = "") -> dict:
    """
    End a tutoring session and generate a summary.

    Args:
        session_id: Tutoring session ID
        session_summary: Optional summary from student

    Returns:
        Dictionary with session summary and recommendations
    """
    try:
        if session_id not in tutoring_sessions:
            return {
                "success": False,
                "error": "Session not found"
            }

        session = tutoring_sessions[session_id]

        # Generate session summary
        prompt = f"""
        Generate a comprehensive summary for this tutoring session:

        {session.get_context_summary()}

        Session Details:
        - Duration: {(datetime.utcnow() - session.created_at).total_seconds() / 60:.1f} minutes
        - Interactions: {len(session.conversation_history)}
        - Final Understanding Level: {session.student_understanding_level:.2f}/1.0
        - Student Summary: {session_summary or 'No summary provided'}

        Return JSON with:
        - "session_summary": comprehensive summary of what was covered
        - "learning_achievements": what the student accomplished
        - "areas_covered": topics and concepts discussed
        - "understanding_progress": how understanding evolved during session
        - "recommendations": recommendations for future study
        - "next_session_suggestions": suggestions for next tutoring session
        - "study_plan": personalized study plan based on session
        - "strengths_identified": student strengths observed
        - "areas_for_improvement": areas that need more work
        """

        response = await MODEL.generate_text(prompt, temperature=0.6)
        summary_data = extract_json_from_text(response)

        # Store session summary before removing
        session_data = {
            "session_id": session_id,
            "student_id": session.student_id,
            "subject": session.subject,
            "duration_minutes": (datetime.utcnow() - session.created_at).total_seconds() / 60,
            "interaction_count": len(session.conversation_history),
            "final_understanding": session.student_understanding_level,
            "summary": summary_data
        }

        # Remove session from active sessions
        del tutoring_sessions[session_id]

        return {
            "success": True,
            "session_ended": True,
            **session_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to end session: {str(e)}"
        }

@mcp.tool()
async def list_active_tutoring_sessions(student_id: str = None) -> dict:
    """
    List all active tutoring sessions, optionally filtered by student.

    Args:
        student_id: Optional student ID to filter sessions

    Returns:
        Dictionary with list of active sessions
    """
    try:
        active_sessions = []

        for session_id, session in tutoring_sessions.items():
            if student_id is None or session.student_id == student_id:
                active_sessions.append({
                    "session_id": session_id,
                    "student_id": session.student_id,
                    "subject": session.subject,
                    "current_topic": session.current_topic,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "duration_minutes": (datetime.utcnow() - session.created_at).total_seconds() / 60,
                    "understanding_level": session.student_understanding_level,
                    "interaction_count": len(session.conversation_history)
                })

        return {
            "success": True,
            "active_sessions": active_sessions,
            "total_sessions": len(active_sessions),
            "filtered_by_student": student_id is not None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list sessions: {str(e)}"
        }
