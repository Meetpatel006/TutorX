"""
Learning path generation tools for TutorX with adaptive learning capabilities.
"""
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import json
import re
from dataclasses import dataclass, asdict
from enum import Enum

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

# Import from local resources
try:
    from resources.concept_graph import CONCEPT_GRAPH
except ImportError:
    # Fallback for when running from different contexts
    CONCEPT_GRAPH = {
        "algebra_basics": {"id": "algebra_basics", "name": "Algebra Basics", "description": "Basic algebraic concepts"},
        "linear_equations": {"id": "linear_equations", "name": "Linear Equations", "description": "Solving linear equations"},
        "quadratic_equations": {"id": "quadratic_equations", "name": "Quadratic Equations", "description": "Solving quadratic equations"},
        "algebra_linear_equations": {"id": "algebra_linear_equations", "name": "Linear Equations", "description": "Linear equation solving"}
    }

# Import MCP
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash

MODEL = GeminiFlash()

# Adaptive Learning Data Structures
class DifficultyLevel(Enum):
    VERY_EASY = 0.2
    EASY = 0.4
    MEDIUM = 0.6
    HARD = 0.8
    VERY_HARD = 1.0

@dataclass
class StudentPerformance:
    student_id: str
    concept_id: str
    accuracy_rate: float = 0.0
    time_spent_minutes: float = 0.0
    attempts_count: int = 0
    mastery_level: float = 0.0
    last_accessed: datetime = None
    difficulty_preference: float = 0.5

@dataclass
class LearningEvent:
    student_id: str
    concept_id: str
    event_type: str  # 'answer_correct', 'answer_incorrect', 'hint_used', 'time_spent'
    timestamp: datetime
    data: Dict[str, Any]

# In-memory storage for adaptive learning
student_performances: Dict[str, Dict[str, StudentPerformance]] = {}
learning_events: List[LearningEvent] = []
active_sessions: Dict[str, Dict[str, Any]] = {}

def get_prerequisites(concept_id: str, visited: Optional[set] = None) -> List[Dict[str, Any]]:
    """
    Get all prerequisites for a concept recursively.
    
    Args:
        concept_id: ID of the concept to get prerequisites for
        visited: Set of already visited concepts to avoid cycles
        
    Returns:
        List of prerequisite concepts in order
    """
    if visited is None:
        visited = set()
    
    if concept_id not in CONCEPT_GRAPH or concept_id in visited:
        return []
    
    visited.add(concept_id)
    prerequisites = []
    
    # Get direct prerequisites
    for prereq_id in CONCEPT_GRAPH[concept_id].get("prerequisites", []):
        if prereq_id in CONCEPT_GRAPH and prereq_id not in visited:
            prerequisites.extend(get_prerequisites(prereq_id, visited))
    
    # Add the current concept
    prerequisites.append(CONCEPT_GRAPH[concept_id])
    return prerequisites

def generate_learning_path(concept_ids: List[str], student_level: str = "beginner") -> Dict[str, Any]:
    """
    Generate a personalized learning path for a student.
    
    Args:
        concept_ids: List of concept IDs to include in the learning path
        student_level: Student's current level (beginner, intermediate, advanced)
        
    Returns:
        Dictionary containing the learning path
    """
    if not concept_ids:
        return {"error": "At least one concept ID is required"}
    
    # Get all prerequisites for each concept
    all_prerequisites = []
    visited = set()
    
    for concept_id in concept_ids:
        if concept_id in CONCEPT_GRAPH:
            prereqs = get_prerequisites(concept_id, visited)
            all_prerequisites.extend(prereqs)
    
    # Remove duplicates while preserving order
    unique_concepts = []
    seen = set()
    for concept in all_prerequisites:
        if concept["id"] not in seen:
            seen.add(concept["id"])
            unique_concepts.append(concept)
    
    # Add any target concepts not already in the path
    for concept_id in concept_ids:
        if concept_id in CONCEPT_GRAPH and concept_id not in seen:
            unique_concepts.append(CONCEPT_GRAPH[concept_id])
    
    # Estimate time required for each concept based on student level
    time_estimates = {
        "beginner": {"min": 30, "max": 60},    # 30-60 minutes per concept
        "intermediate": {"min": 20, "max": 45},  # 20-45 minutes per concept
        "advanced": {"min": 15, "max": 30}      # 15-30 minutes per concept
    }
    
    level = student_level.lower()
    if level not in time_estimates:
        level = "beginner"
    
    time_min = time_estimates[level]["min"]
    time_max = time_estimates[level]["max"]
    
    # Generate learning path with estimated times
    learning_path = []
    total_minutes = 0
    
    for i, concept in enumerate(unique_concepts, 1):
        # Random time estimate within range
        minutes = random.randint(time_min, time_max)
        total_minutes += minutes
        
        learning_path.append({
            "step": i,
            "concept_id": concept["id"],
            "concept_name": concept["name"],
            "description": concept.get("description", ""),
            "estimated_time_minutes": minutes,
            "resources": [
                f"Video tutorial on {concept['name']}",
                f"{concept['name']} documentation",
                f"Practice exercises for {concept['name']}"
            ]
        })
    
    # Calculate total time
    hours, minutes = divmod(total_minutes, 60)
    total_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    return {
        "learning_path": learning_path,
        "total_steps": len(learning_path),
        "total_time_minutes": total_minutes,
        "total_time_display": total_time,
        "student_level": student_level,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

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

# Adaptive Learning Helper Functions
def get_student_performance(student_id: str, concept_id: str) -> StudentPerformance:
    """Get or create student performance record."""
    if student_id not in student_performances:
        student_performances[student_id] = {}

    if concept_id not in student_performances[student_id]:
        student_performances[student_id][concept_id] = StudentPerformance(
            student_id=student_id,
            concept_id=concept_id,
            last_accessed=datetime.utcnow()
        )

    return student_performances[student_id][concept_id]

def update_mastery_level(performance: StudentPerformance) -> float:
    """Calculate mastery level based on performance metrics."""
    if performance.attempts_count == 0:
        return 0.0

    # Weighted calculation: accuracy (60%), consistency (20%), efficiency (20%)
    accuracy_score = performance.accuracy_rate

    # Consistency: higher attempts with stable accuracy indicate consistency
    consistency_score = min(1.0, performance.attempts_count / 5.0) if performance.accuracy_rate > 0.7 else 0.5

    # Efficiency: less time per attempt indicates better understanding
    avg_time = performance.time_spent_minutes / performance.attempts_count if performance.attempts_count > 0 else 30
    efficiency_score = max(0.1, 1.0 - (avg_time - 10) / 50)  # Normalize around 10-60 minutes

    mastery = (accuracy_score * 0.6) + (consistency_score * 0.2) + (efficiency_score * 0.2)
    performance.mastery_level = min(1.0, max(0.0, mastery))
    return performance.mastery_level

def adapt_difficulty(performance: StudentPerformance) -> float:
    """Adapt difficulty based on student performance."""
    if performance.attempts_count < 2:
        return performance.difficulty_preference

    # If accuracy is high, increase difficulty
    if performance.accuracy_rate > 0.8:
        new_difficulty = min(1.0, performance.difficulty_preference + 0.1)
    # If accuracy is low, decrease difficulty
    elif performance.accuracy_rate < 0.5:
        new_difficulty = max(0.2, performance.difficulty_preference - 0.1)
    else:
        new_difficulty = performance.difficulty_preference

    performance.difficulty_preference = new_difficulty
    return new_difficulty

# Enhanced Adaptive Learning with Gemini Integration

@mcp.tool()
async def generate_adaptive_content(student_id: str, concept_id: str, content_type: str = "explanation",
                                  difficulty_level: float = 0.5, learning_style: str = "visual") -> dict:
    """
    Generate personalized learning content using Gemini based on student profile and performance.

    Args:
        student_id: Student identifier
        concept_id: Concept to generate content for
        content_type: Type of content ('explanation', 'example', 'practice', 'summary')
        difficulty_level: Difficulty level (0.0 to 1.0)
        learning_style: Preferred learning style ('visual', 'auditory', 'kinesthetic', 'reading')

    Returns:
        Personalized learning content
    """
    try:
        # Get student performance data
        performance = get_student_performance(student_id, concept_id)
        concept_data = CONCEPT_GRAPH.get(concept_id, {"name": concept_id, "description": ""})

        # Build context for Gemini
        context = f"""
        Student Profile:
        - Student ID: {student_id}
        - Current mastery level: {performance.mastery_level:.2f}
        - Accuracy rate: {performance.accuracy_rate:.2f}
        - Attempts made: {performance.attempts_count}
        - Preferred difficulty: {difficulty_level}
        - Learning style: {learning_style}

        Concept Information:
        - Concept: {concept_data.get('name', concept_id)}
        - Description: {concept_data.get('description', '')}

        Content Requirements:
        - Content type: {content_type}
        - Target difficulty: {difficulty_level}
        - Learning style: {learning_style}
        """

        if content_type == "explanation":
            prompt = f"""{context}

            Generate a personalized explanation of {concept_data.get('name', concept_id)} that:
            1. Matches the student's current understanding level (mastery: {performance.mastery_level:.2f})
            2. Uses {learning_style} learning approaches
            3. Is appropriate for difficulty level {difficulty_level}
            4. Builds on their {performance.attempts_count} previous attempts

            Return a JSON object with:
            - "explanation": detailed explanation text
            - "key_points": list of 3-5 key concepts
            - "analogies": 2-3 relevant analogies or examples
            - "difficulty_indicators": what makes this concept challenging
            - "next_steps": suggested follow-up activities
            """
        elif content_type == "practice":
            prompt = f"""{context}

            Generate personalized practice problems for {concept_data.get('name', concept_id)} that:
            1. Match difficulty level {difficulty_level}
            2. Consider their accuracy rate of {performance.accuracy_rate:.2f}
            3. Use {learning_style} presentation style
            4. Provide appropriate scaffolding

            Return a JSON object with:
            - "problems": list of 3-5 practice problems
            - "hints": helpful hints for each problem
            - "solutions": step-by-step solutions
            - "difficulty_progression": how problems increase in complexity
            - "success_criteria": what indicates mastery
            """
        elif content_type == "feedback":
            prompt = f"""{context}

            Generate personalized feedback for the student's performance on {concept_data.get('name', concept_id)}:
            1. Acknowledge their current progress (mastery: {performance.mastery_level:.2f})
            2. Address their accuracy rate of {performance.accuracy_rate:.2f}
            3. Provide encouraging and constructive guidance
            4. Suggest specific improvement strategies

            Return a JSON object with:
            - "encouragement": positive reinforcement message
            - "areas_of_strength": what they're doing well
            - "improvement_areas": specific areas to focus on
            - "strategies": concrete learning strategies
            - "motivation": motivational message tailored to their progress
            """
        else:  # summary or other types
            prompt = f"""{context}

            Generate a personalized summary of {concept_data.get('name', concept_id)} that:
            1. Reinforces key concepts at their mastery level
            2. Uses {learning_style} presentation
            3. Connects to their learning journey

            Return a JSON object with:
            - "summary": concise concept summary
            - "key_takeaways": main points to remember
            - "connections": how this relates to other concepts
            - "review_schedule": when to review this concept
            """

        # Generate content using Gemini
        response = await MODEL.generate_text(prompt, temperature=0.7)

        try:
            content_data = extract_json_from_text(response)
            content_data.update({
                "success": True,
                "student_id": student_id,
                "concept_id": concept_id,
                "content_type": content_type,
                "difficulty_level": difficulty_level,
                "learning_style": learning_style,
                "generated_at": datetime.utcnow().isoformat(),
                "personalization_factors": {
                    "mastery_level": performance.mastery_level,
                    "accuracy_rate": performance.accuracy_rate,
                    "attempts_count": performance.attempts_count
                }
            })
            return content_data
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse Gemini response: {str(e)}",
                "raw_response": response
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def analyze_learning_patterns(student_id: str, analysis_days: int = 30) -> dict:
    """
    Use Gemini to analyze student learning patterns and provide insights.

    Args:
        student_id: Student identifier
        analysis_days: Number of days to analyze

    Returns:
        AI-powered learning pattern analysis
    """
    try:
        # Gather student data
        if student_id not in student_performances:
            return {
                "success": True,
                "student_id": student_id,
                "message": "No learning data available for analysis",
                "recommendations": ["Start learning to build your profile!"]
            }

        student_data = student_performances[student_id]

        # Get recent events
        cutoff_date = datetime.utcnow() - timedelta(days=analysis_days)
        recent_events = [e for e in learning_events
                        if e.student_id == student_id and e.timestamp >= cutoff_date]

        # Prepare data for analysis
        performance_summary = []
        for concept_id, perf in student_data.items():
            concept_name = CONCEPT_GRAPH.get(concept_id, {}).get('name', concept_id)
            performance_summary.append({
                "concept": concept_name,
                "mastery": perf.mastery_level,
                "accuracy": perf.accuracy_rate,
                "attempts": perf.attempts_count,
                "time_spent": perf.time_spent_minutes,
                "last_accessed": perf.last_accessed.isoformat() if perf.last_accessed else None
            })

        # Build analysis prompt
        prompt = f"""
        Analyze the learning patterns for Student {student_id} over the past {analysis_days} days.

        Performance Data:
        {json.dumps(performance_summary, indent=2)}

        Recent Learning Events: {len(recent_events)} events

        Please provide a comprehensive analysis including:
        1. Learning strengths and patterns
        2. Areas that need attention
        3. Optimal learning times/frequency
        4. Difficulty progression recommendations
        5. Personalized learning strategies
        6. Motivation and engagement insights

        Return a JSON object with:
        - "learning_style_analysis": identified learning preferences
        - "strength_areas": concepts/skills where student excels
        - "challenge_areas": concepts that need more work
        - "learning_velocity": how quickly student progresses
        - "engagement_patterns": when student is most/least engaged
        - "optimal_difficulty": recommended difficulty range
        - "study_schedule": suggested learning schedule
        - "personalized_strategies": specific strategies for this student
        - "motivation_factors": what motivates this student
        - "next_focus_areas": what to work on next
        - "confidence_level": assessment of student confidence
        """

        # Get AI analysis
        response = await MODEL.generate_text(prompt, temperature=0.6)

        try:
            analysis_data = extract_json_from_text(response)
            analysis_data.update({
                "success": True,
                "student_id": student_id,
                "analysis_period_days": analysis_days,
                "data_points_analyzed": len(performance_summary),
                "recent_events_count": len(recent_events),
                "generated_at": datetime.utcnow().isoformat()
            })
            return analysis_data
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse analysis: {str(e)}",
                "raw_response": response
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def optimize_learning_strategy(student_id: str, current_concept: str,
                                   performance_history: dict = None) -> dict:
    """
    Use Gemini to optimize learning strategy based on comprehensive student analysis.

    Args:
        student_id: Student identifier
        current_concept: Current concept being studied
        performance_history: Optional detailed performance history

    Returns:
        AI-optimized learning strategy recommendations
    """
    try:
        # Get comprehensive student data
        if student_id not in student_performances:
            return {
                "success": True,
                "student_id": student_id,
                "message": "No performance data available. Starting with default strategy.",
                "strategy": "beginner_friendly",
                "recommendations": ["Start with foundational concepts", "Use guided practice"]
            }

        student_data = student_performances[student_id]
        current_performance = student_data.get(current_concept, None)

        # Analyze overall learning patterns
        total_concepts = len(student_data)
        avg_mastery = sum(p.mastery_level for p in student_data.values()) / total_concepts if total_concepts > 0 else 0
        avg_accuracy = sum(p.accuracy_rate for p in student_data.values()) / total_concepts if total_concepts > 0 else 0
        total_time = sum(p.time_spent_minutes for p in student_data.values())

        # Get recent learning velocity
        recent_events = [e for e in learning_events
                        if e.student_id == student_id and
                        e.timestamp >= datetime.utcnow() - timedelta(days=7)]

        # Build comprehensive analysis prompt
        prompt = f"""
        Optimize the learning strategy for Student {student_id} studying {current_concept}.

        CURRENT PERFORMANCE DATA:
        - Current concept: {current_concept}
        - Current mastery: {current_performance.mastery_level if current_performance else 0:.2f}
        - Current accuracy: {current_performance.accuracy_rate if current_performance else 0:.2f}
        - Attempts on current concept: {current_performance.attempts_count if current_performance else 0}

        OVERALL STUDENT PROFILE:
        - Total concepts studied: {total_concepts}
        - Average mastery across all concepts: {avg_mastery:.2f}
        - Average accuracy rate: {avg_accuracy:.2f}
        - Total learning time: {total_time} minutes
        - Recent activity: {len(recent_events)} events in past 7 days

        Generate a comprehensive strategy optimization in JSON format:
        {{
            "optimized_strategy": {{
                "primary_approach": "adaptive|mastery_based|exploratory|remedial",
                "difficulty_recommendation": "current optimal difficulty level (0.0-1.0)",
                "pacing_strategy": "fast|moderate|slow|variable",
                "focus_areas": ["specific areas to emphasize"],
                "learning_modalities": ["visual|auditory|kinesthetic|reading"]
            }},
            "immediate_actions": [
                {{
                    "action": "specific action to take now",
                    "priority": "high|medium|low",
                    "expected_impact": "what this will achieve",
                    "time_estimate": "how long this will take"
                }}
            ],
            "session_optimization": {{
                "ideal_session_length": "recommended minutes per session",
                "break_frequency": "how often to take breaks",
                "review_schedule": "when to review previous concepts",
                "practice_distribution": "how to distribute practice time"
            }},
            "motivation_strategy": {{
                "achievement_recognition": "how to celebrate progress",
                "challenge_level": "optimal challenge to maintain engagement",
                "goal_setting": "short and long-term goals",
                "feedback_style": "how to provide effective feedback"
            }},
            "success_metrics": {{
                "mastery_targets": "target mastery levels",
                "accuracy_goals": "target accuracy rates",
                "time_efficiency": "optimal time per concept",
                "engagement_indicators": "signs of good engagement"
            }}
        }}
        """

        # Get AI strategy optimization
        response = await MODEL.generate_text(prompt, temperature=0.6)

        try:
            strategy_data = extract_json_from_text(response)

            # Add metadata and validation
            strategy_data.update({
                "success": True,
                "student_id": student_id,
                "current_concept": current_concept,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "data_points_analyzed": total_concepts,
                "recent_activity_level": len(recent_events),
                "ai_powered": True
            })

            return strategy_data

        except Exception as e:
            # Fallback strategy if AI parsing fails
            return {
                "success": True,
                "student_id": student_id,
                "current_concept": current_concept,
                "ai_powered": False,
                "fallback_reason": f"AI analysis failed: {str(e)}",
                "basic_strategy": {
                    "approach": "adaptive" if avg_mastery > 0.6 else "foundational",
                    "difficulty": min(0.8, max(0.3, avg_accuracy)),
                    "focus": "mastery" if avg_accuracy < 0.7 else "progression"
                },
                "recommendations": [
                    f"Current mastery level suggests {'advanced' if avg_mastery > 0.7 else 'foundational'} approach",
                    f"Accuracy rate of {avg_accuracy:.1%} indicates {'good progress' if avg_accuracy > 0.6 else 'need for more practice'}",
                    "Continue with consistent practice and regular review"
                ]
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

# Adaptive Learning MCP Tools

@mcp.tool()
async def start_adaptive_session(student_id: str, concept_id: str, initial_difficulty: float = 0.5) -> dict:
    """
    Start an adaptive learning session for a student.

    Args:
        student_id: Unique identifier for the student
        concept_id: Concept being learned
        initial_difficulty: Initial difficulty level (0.0 to 1.0)

    Returns:
        Session information and initial recommendations
    """
    try:
        session_id = f"{student_id}_{concept_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Get or create student performance
        performance = get_student_performance(student_id, concept_id)
        performance.difficulty_preference = initial_difficulty
        performance.last_accessed = datetime.utcnow()

        # Create session
        active_sessions[session_id] = {
            'student_id': student_id,
            'concept_id': concept_id,
            'start_time': datetime.utcnow(),
            'current_difficulty': initial_difficulty,
            'events': [],
            'questions_answered': 0,
            'correct_answers': 0
        }

        return {
            "success": True,
            "session_id": session_id,
            "student_id": student_id,
            "concept_id": concept_id,
            "initial_difficulty": initial_difficulty,
            "current_mastery": performance.mastery_level,
            "recommendations": [
                f"Start with difficulty level {initial_difficulty:.1f}",
                f"Current mastery level: {performance.mastery_level:.2f}",
                "System will adapt based on your performance"
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def record_learning_event(student_id: str, concept_id: str, session_id: str,
                               event_type: str, event_data: dict) -> dict:
    """
    Record a learning event for adaptive analysis.

    Args:
        student_id: Student identifier
        concept_id: Concept identifier
        session_id: Session identifier
        event_type: Type of event ('answer_correct', 'answer_incorrect', 'hint_used', 'time_spent')
        event_data: Additional event data

    Returns:
        Event recording confirmation and updated recommendations
    """
    try:
        # Record the event
        event = LearningEvent(
            student_id=student_id,
            concept_id=concept_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=event_data
        )
        learning_events.append(event)

        # Update session
        if session_id in active_sessions:
            session = active_sessions[session_id]
            session['events'].append(event)

            if event_type in ['answer_correct', 'answer_incorrect']:
                session['questions_answered'] += 1
                if event_type == 'answer_correct':
                    session['correct_answers'] += 1

        # Update student performance
        performance = get_student_performance(student_id, concept_id)
        performance.attempts_count += 1

        if event_type == 'answer_correct':
            performance.accuracy_rate = (performance.accuracy_rate * (performance.attempts_count - 1) + 1.0) / performance.attempts_count
        elif event_type == 'answer_incorrect':
            performance.accuracy_rate = (performance.accuracy_rate * (performance.attempts_count - 1) + 0.0) / performance.attempts_count
        elif event_type == 'time_spent':
            performance.time_spent_minutes += event_data.get('minutes', 0)

        # Update mastery level
        new_mastery = update_mastery_level(performance)

        # Adapt difficulty
        new_difficulty = adapt_difficulty(performance)

        # Generate recommendations
        recommendations = []
        if performance.accuracy_rate > 0.8 and performance.attempts_count >= 3:
            recommendations.append("Great job! Consider moving to a harder difficulty level.")
        elif performance.accuracy_rate < 0.5 and performance.attempts_count >= 3:
            recommendations.append("Let's try some easier questions to build confidence.")

        if new_mastery > 0.8:
            recommendations.append("You're mastering this concept! Ready for the next one?")

        return {
            "success": True,
            "event_recorded": True,
            "updated_mastery": new_mastery,
            "updated_difficulty": new_difficulty,
            "current_accuracy": performance.accuracy_rate,
            "recommendations": recommendations
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_adaptive_recommendations(student_id: str, concept_id: str, session_id: str = None) -> dict:
    """
    Get AI-powered adaptive learning recommendations using Gemini analysis.

    Args:
        student_id: Student identifier
        concept_id: Concept identifier
        session_id: Optional session identifier

    Returns:
        Intelligent adaptive learning recommendations
    """
    try:
        performance = get_student_performance(student_id, concept_id)
        concept_data = CONCEPT_GRAPH.get(concept_id, {"name": concept_id, "description": ""})

        # Get session data if available
        session_data = active_sessions.get(session_id, {}) if session_id else {}

        # Build comprehensive context for Gemini
        context = f"""
        Student Performance Analysis for {concept_data.get('name', concept_id)}:

        Current Metrics:
        - Mastery Level: {performance.mastery_level:.2f} (0.0 = no understanding, 1.0 = complete mastery)
        - Accuracy Rate: {performance.accuracy_rate:.2f} (proportion of correct answers)
        - Total Attempts: {performance.attempts_count}
        - Time Spent: {performance.time_spent_minutes} minutes
        - Current Difficulty Preference: {performance.difficulty_preference:.2f}
        - Last Accessed: {performance.last_accessed.isoformat() if performance.last_accessed else 'Never'}

        Session Information:
        - Session ID: {session_id or 'No active session'}
        - Questions Answered: {session_data.get('questions_answered', 0)}
        - Correct Answers: {session_data.get('correct_answers', 0)}

        Concept Details:
        - Concept: {concept_data.get('name', concept_id)}
        - Description: {concept_data.get('description', 'No description available')}
        """

        prompt = f"""{context}

        As an AI learning advisor, analyze this student's performance and provide personalized recommendations.

        Consider:
        1. Current mastery level and learning trajectory
        2. Accuracy patterns and difficulty appropriateness
        3. Time investment and learning efficiency
        4. Optimal next steps for continued growth
        5. Motivation and engagement strategies

        Provide specific, actionable recommendations in JSON format:
        {{
            "immediate_actions": [
                {{
                    "type": "difficulty_adjustment|content_type|study_strategy|break_recommendation",
                    "priority": "high|medium|low",
                    "action": "specific action to take",
                    "reasoning": "why this action is recommended",
                    "expected_outcome": "what this should achieve"
                }}
            ],
            "difficulty_recommendation": {{
                "current_level": {performance.difficulty_preference:.2f},
                "suggested_level": "recommended difficulty (0.0-1.0)",
                "adjustment_reason": "explanation for the change",
                "gradual_steps": ["step-by-step difficulty progression"]
            }},
            "learning_strategy": {{
                "primary_focus": "what to focus on most",
                "study_methods": ["recommended study techniques"],
                "practice_types": ["types of practice exercises"],
                "time_allocation": "suggested time distribution"
            }},
            "motivation_boosters": [
                "specific encouragement based on progress",
                "achievement recognition",
                "goal-setting suggestions"
            ],
            "next_milestones": [
                {{
                    "milestone": "specific goal",
                    "target_mastery": "target mastery level",
                    "estimated_time": "time to achieve",
                    "success_indicators": ["how to know when achieved"]
                }}
            ],
            "warning_signs": [
                "potential issues to watch for"
            ],
            "adaptive_insights": {{
                "learning_pattern": "observed learning pattern",
                "optimal_session_length": "recommended session duration",
                "best_practice_times": "when student learns best",
                "engagement_level": "current engagement assessment"
            }}
        }}
        """

        # Get AI recommendations
        response = await MODEL.generate_text(prompt, temperature=0.7)

        try:
            ai_recommendations = extract_json_from_text(response)

            # Add basic fallback recommendations if AI parsing fails
            if not ai_recommendations or "immediate_actions" not in ai_recommendations:
                ai_recommendations = _generate_fallback_recommendations(performance)

            # Enhance with computed metrics
            ai_recommendations.update({
                "success": True,
                "student_id": student_id,
                "concept_id": concept_id,
                "session_id": session_id,
                "current_metrics": {
                    "mastery_level": performance.mastery_level,
                    "accuracy_rate": performance.accuracy_rate,
                    "attempts_count": performance.attempts_count,
                    "time_spent_minutes": performance.time_spent_minutes,
                    "difficulty_preference": performance.difficulty_preference
                },
                "ai_powered": True,
                "generated_at": datetime.utcnow().isoformat()
            })

            return ai_recommendations

        except Exception as e:
            # Fallback to basic recommendations if AI parsing fails
            return _generate_fallback_recommendations(performance, student_id, concept_id, session_id, str(e))

    except Exception as e:
        return {"success": False, "error": str(e)}

def _generate_fallback_recommendations(performance: StudentPerformance, student_id: str = None,
                                     concept_id: str = None, session_id: str = None,
                                     ai_error: str = None) -> dict:
    """Generate basic recommendations when AI analysis fails."""
    recommendations = []

    # Difficulty recommendations
    if performance.accuracy_rate > 0.8:
        recommendations.append({
            "type": "difficulty_increase",
            "priority": "medium",
            "action": "Increase difficulty level",
            "reasoning": "High accuracy indicates readiness for more challenge",
            "expected_outcome": "Maintain engagement and continued growth"
        })
    elif performance.accuracy_rate < 0.5:
        recommendations.append({
            "type": "difficulty_decrease",
            "priority": "high",
            "action": "Decrease difficulty level",
            "reasoning": "Low accuracy suggests current level is too challenging",
            "expected_outcome": "Build confidence and foundational understanding"
        })

    # Mastery recommendations
    if performance.mastery_level > 0.8:
        recommendations.append({
            "type": "concept_advancement",
            "priority": "high",
            "action": "Move to next concept",
            "reasoning": "High mastery level achieved",
            "expected_outcome": "Continue learning progression"
        })
    elif performance.mastery_level < 0.3 and performance.attempts_count >= 5:
        recommendations.append({
            "type": "additional_practice",
            "priority": "high",
            "action": "Focus on additional practice",
            "reasoning": "Low mastery despite multiple attempts",
            "expected_outcome": "Strengthen foundational understanding"
        })

    return {
        "success": True,
        "student_id": student_id,
        "concept_id": concept_id,
        "session_id": session_id,
        "immediate_actions": recommendations,
        "ai_powered": False,
        "fallback_reason": f"AI analysis failed: {ai_error}" if ai_error else "Using basic recommendation engine",
        "current_metrics": {
            "mastery_level": performance.mastery_level,
            "accuracy_rate": performance.accuracy_rate,
            "attempts_count": performance.attempts_count,
            "difficulty_preference": performance.difficulty_preference
        },
        "generated_at": datetime.utcnow().isoformat()
    }

@mcp.tool()
async def get_learning_path(student_id: str, concept_ids: list, student_level: str = "beginner") -> dict:
    """
    Generate a personalized learning path for a student, fully LLM-driven.
    Use Gemini to generate a JSON object with a list of steps, each with concept name, description, estimated time, and recommended resources.
    """
    prompt = (
        f"A student (ID: {student_id}) with level '{student_level}' needs a learning path for these concepts: {concept_ids}. "
        f"Return a JSON object with a 'learning_path' field: a list of steps, each with concept_name, description, estimated_time_minutes, and resources (list)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = extract_json_from_text(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data

@mcp.tool()
async def get_adaptive_learning_path(student_id: str, target_concepts: list,
                                   strategy: str = "adaptive", max_concepts: int = 10) -> dict:
    """
    Generate an AI-powered adaptive learning path using Gemini analysis.

    Args:
        student_id: Student identifier
        target_concepts: List of target concept IDs
        strategy: Learning strategy ('adaptive', 'mastery_focused', 'breadth_first', 'depth_first', 'remediation')
        max_concepts: Maximum number of concepts in the path

    Returns:
        Intelligent adaptive learning path optimized by AI
    """
    try:
        # Get comprehensive student performance data
        student_data = {}
        overall_stats = {
            'total_concepts': 0,
            'average_mastery': 0,
            'average_accuracy': 0,
            'total_time': 0,
            'total_attempts': 0
        }

        for concept_id in target_concepts:
            concept_name = CONCEPT_GRAPH.get(concept_id, {}).get('name', concept_id)
            if student_id in student_performances and concept_id in student_performances[student_id]:
                perf = student_performances[student_id][concept_id]
                student_data[concept_id] = {
                    'concept_name': concept_name,
                    'mastery_level': perf.mastery_level,
                    'accuracy_rate': perf.accuracy_rate,
                    'difficulty_preference': perf.difficulty_preference,
                    'attempts_count': perf.attempts_count,
                    'time_spent': perf.time_spent_minutes,
                    'last_accessed': perf.last_accessed.isoformat() if perf.last_accessed else None
                }
                overall_stats['total_concepts'] += 1
                overall_stats['average_mastery'] += perf.mastery_level
                overall_stats['average_accuracy'] += perf.accuracy_rate
                overall_stats['total_time'] += perf.time_spent_minutes
                overall_stats['total_attempts'] += perf.attempts_count
            else:
                # New concept - no performance data
                student_data[concept_id] = {
                    'concept_name': concept_name,
                    'mastery_level': 0.0,
                    'accuracy_rate': 0.0,
                    'difficulty_preference': 0.5,
                    'attempts_count': 0,
                    'time_spent': 0,
                    'last_accessed': None,
                    'is_new': True
                }

        # Calculate averages
        if overall_stats['total_concepts'] > 0:
            overall_stats['average_mastery'] /= overall_stats['total_concepts']
            overall_stats['average_accuracy'] /= overall_stats['total_concepts']

        # Build comprehensive prompt for Gemini
        prompt = f"""
        Create an optimal adaptive learning path for Student {student_id} using advanced AI analysis.

        STUDENT PERFORMANCE DATA:
        {json.dumps(student_data, indent=2)}

        OVERALL STATISTICS:
        - Total concepts with data: {overall_stats['total_concepts']}
        - Average mastery level: {overall_stats['average_mastery']:.2f}
        - Average accuracy rate: {overall_stats['average_accuracy']:.2f}
        - Total learning time: {overall_stats['total_time']} minutes
        - Total attempts: {overall_stats['total_attempts']}

        LEARNING STRATEGY: {strategy}
        MAX CONCEPTS: {max_concepts}

        STRATEGY DEFINITIONS:
        - adaptive: AI-optimized path balancing challenge and success
        - mastery_focused: Deep understanding before progression
        - breadth_first: Cover many concepts quickly for overview
        - depth_first: Thorough exploration of fewer concepts
        - remediation: Focus on filling knowledge gaps

        REQUIREMENTS:
        1. Analyze student's learning patterns and preferences
        2. Consider concept dependencies and prerequisites
        3. Optimize for engagement and learning efficiency
        4. Provide personalized difficulty progression
        5. Include time estimates based on student's pace
        6. Add motivational elements and milestones

        Generate a JSON response with this structure:
        {{
            "learning_path": [
                {{
                    "step": 1,
                    "concept_id": "concept_id",
                    "concept_name": "Human readable name",
                    "description": "What student will learn",
                    "estimated_time_minutes": 30,
                    "difficulty_level": 0.6,
                    "mastery_target": 0.8,
                    "prerequisites_met": true,
                    "learning_objectives": ["specific objective 1", "objective 2"],
                    "recommended_activities": ["activity 1", "activity 2"],
                    "success_criteria": ["how to know when mastered"],
                    "adaptive_notes": "Personalized guidance",
                    "motivation_boost": "Encouraging message"
                }}
            ],
            "path_analysis": {{
                "strategy_rationale": "Why this strategy was chosen",
                "difficulty_progression": "How difficulty increases",
                "estimated_completion": "Total time estimate",
                "learning_velocity": "Expected pace",
                "challenge_level": "Overall difficulty assessment"
            }},
            "personalization": {{
                "student_strengths": ["identified strengths"],
                "focus_areas": ["areas needing attention"],
                "learning_style_adaptations": ["how path is adapted"],
                "motivation_factors": ["what will keep student engaged"]
            }},
            "milestones": [
                {{
                    "milestone_name": "Achievement name",
                    "concepts_completed": 3,
                    "expected_mastery": 0.75,
                    "celebration": "How to celebrate achievement"
                }}
            ],
            "adaptive_features": [
                "Real-time difficulty adjustment",
                "Performance-based pacing",
                "Personalized content delivery"
            ]
        }}
        """

        # Get AI-generated learning path
        response = await MODEL.generate_text(prompt, temperature=0.6)

        try:
            ai_path = extract_json_from_text(response)

            # Validate and enhance the AI response
            if not ai_path or "learning_path" not in ai_path:
                # Fallback to basic path generation
                ai_path = _generate_basic_adaptive_path(student_data, target_concepts, strategy, max_concepts)

            # Add metadata
            ai_path.update({
                "success": True,
                "student_id": student_id,
                "strategy": strategy,
                "max_concepts": max_concepts,
                "ai_powered": True,
                "total_steps": len(ai_path.get("learning_path", [])),
                "total_time_minutes": sum(step.get("estimated_time_minutes", 30)
                                        for step in ai_path.get("learning_path", [])),
                "generated_at": datetime.utcnow().isoformat()
            })

            return ai_path

        except Exception as e:
            # Fallback to basic path if AI parsing fails
            return _generate_basic_adaptive_path(student_data, target_concepts, strategy, max_concepts, str(e))

    except Exception as e:
        return {"success": False, "error": str(e)}

def _generate_basic_adaptive_path(student_data: dict, target_concepts: list,
                                strategy: str, max_concepts: int, ai_error: str = None) -> dict:
    """Generate basic adaptive path when AI analysis fails."""
    # Simple sorting based on strategy
    if strategy == "mastery_focused":
        sorted_concepts = sorted(target_concepts,
                               key=lambda c: student_data.get(c, {}).get('mastery_level', 0))
    elif strategy == "breadth_first":
        # Mix of new and partially learned concepts
        sorted_concepts = sorted(target_concepts,
                               key=lambda c: (student_data.get(c, {}).get('attempts_count', 0),
                                             1 - student_data.get(c, {}).get('mastery_level', 0)))
    else:  # adaptive or other
        def adaptive_score(concept_id):
            data = student_data.get(concept_id, {})
            mastery = data.get('mastery_level', 0)
            attempts = data.get('attempts_count', 0)
            return (1 - mastery) * (1 + min(attempts / 10, 1))
        sorted_concepts = sorted(target_concepts, key=adaptive_score, reverse=True)

    # Limit to max_concepts
    selected_concepts = sorted_concepts[:max_concepts]

    # Generate learning path with adaptive recommendations
    learning_path = []
    for i, concept_id in enumerate(selected_concepts, 1):
        concept_data = CONCEPT_GRAPH.get(concept_id, {"name": concept_id, "description": ""})
        perf_data = student_data.get(concept_id, {})

        # Estimate time based on mastery level
        base_time = 30  # Base 30 minutes
        mastery = perf_data.get('mastery_level', 0)
        if mastery > 0.8:
            estimated_time = base_time * 0.5  # Quick review
        elif mastery > 0.5:
            estimated_time = base_time * 0.8  # Moderate practice
        else:
            estimated_time = base_time * 1.2  # More practice needed

        learning_path.append({
            "step": i,
            "concept_id": concept_id,
            "concept_name": concept_data.get("name", concept_id),
            "description": concept_data.get("description", ""),
            "estimated_time_minutes": int(estimated_time),
            "current_mastery": perf_data.get('mastery_level', 0),
            "recommended_difficulty": perf_data.get('difficulty_preference', 0.5),
            "adaptive_notes": _get_adaptive_notes(perf_data),
            "resources": [
                f"Adaptive practice for {concept_data.get('name', concept_id)}",
                f"Personalized exercises at {perf_data.get('difficulty_preference', 0.5):.1f} difficulty",
                f"Progress tracking and real-time feedback"
            ]
        })

    total_time = sum(step["estimated_time_minutes"] for step in learning_path)

    return {
        "success": True,
        "learning_path": learning_path,
        "strategy": strategy,
        "total_steps": len(learning_path),
        "total_time_minutes": total_time,
        "ai_powered": False,
        "fallback_reason": f"AI analysis failed: {ai_error}" if ai_error else "Using basic adaptive algorithm",
        "adaptive_features": [
            "Performance-based ordering",
            "Mastery-level time estimation",
            "Basic difficulty adaptation"
        ],
        "generated_at": datetime.utcnow().isoformat()
    }

def _get_adaptive_notes(perf_data: dict) -> str:
    """Generate adaptive notes based on performance data."""
    mastery = perf_data.get('mastery_level', 0)
    accuracy = perf_data.get('accuracy_rate', 0)
    attempts = perf_data.get('attempts_count', 0)

    if attempts == 0:
        return "New concept - start with guided practice"
    elif mastery > 0.8:
        return "Well mastered - quick review recommended"
    elif mastery > 0.5:
        return "Good progress - continue with current difficulty"
    elif accuracy < 0.5:
        return "Needs more practice - consider easier difficulty"
    else:
        return "Building understanding - maintain current approach"

@mcp.tool()
async def get_student_progress_summary(student_id: str, days: int = 7) -> dict:
    """
    Get a comprehensive progress summary for a student.

    Args:
        student_id: Student identifier
        days: Number of days to analyze

    Returns:
        Progress summary with analytics
    """
    try:
        # Get student performance data
        if student_id not in student_performances:
            return {
                "success": True,
                "student_id": student_id,
                "message": "No performance data available",
                "concepts_practiced": 0,
                "total_time_minutes": 0,
                "average_mastery": 0.0
            }

        student_data = student_performances[student_id]

        # Calculate summary statistics
        total_concepts = len(student_data)
        total_time = sum(perf.time_spent_minutes for perf in student_data.values())
        total_attempts = sum(perf.attempts_count for perf in student_data.values())
        average_mastery = sum(perf.mastery_level for perf in student_data.values()) / total_concepts if total_concepts > 0 else 0
        average_accuracy = sum(perf.accuracy_rate for perf in student_data.values()) / total_concepts if total_concepts > 0 else 0

        # Get recent events
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_events = [e for e in learning_events
                        if e.student_id == student_id and e.timestamp >= cutoff_date]

        # Concept breakdown
        concept_summary = []
        for concept_id, perf in student_data.items():
            concept_summary.append({
                "concept_id": concept_id,
                "mastery_level": perf.mastery_level,
                "accuracy_rate": perf.accuracy_rate,
                "time_spent_minutes": perf.time_spent_minutes,
                "attempts_count": perf.attempts_count,
                "last_accessed": perf.last_accessed.isoformat() if perf.last_accessed else None,
                "status": _get_concept_status(perf.mastery_level)
            })

        return {
            "success": True,
            "student_id": student_id,
            "analysis_period_days": days,
            "summary": {
                "concepts_practiced": total_concepts,
                "total_time_minutes": total_time,
                "total_attempts": total_attempts,
                "average_mastery": round(average_mastery, 2),
                "average_accuracy": round(average_accuracy, 2),
                "recent_events_count": len(recent_events)
            },
            "concept_breakdown": concept_summary,
            "recommendations": _generate_progress_recommendations(student_data),
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def _get_concept_status(mastery_level: float) -> str:
    """Get concept status based on mastery level."""
    if mastery_level >= 0.8:
        return "Mastered"
    elif mastery_level >= 0.6:
        return "Good Progress"
    elif mastery_level >= 0.4:
        return "Learning"
    elif mastery_level >= 0.2:
        return "Struggling"
    else:
        return "Needs Attention"

def _generate_progress_recommendations(student_data: Dict[str, StudentPerformance]) -> List[str]:
    """Generate recommendations based on student progress."""
    recommendations = []

    mastered_concepts = [cid for cid, perf in student_data.items() if perf.mastery_level >= 0.8]
    struggling_concepts = [cid for cid, perf in student_data.items() if perf.mastery_level < 0.4]

    if len(mastered_concepts) > 0:
        recommendations.append(f"Great job! You've mastered {len(mastered_concepts)} concepts.")

    if len(struggling_concepts) > 0:
        recommendations.append(f"Focus on {len(struggling_concepts)} concepts that need more practice.")

    # Check for concepts that haven't been accessed recently
    week_ago = datetime.utcnow() - timedelta(days=7)
    stale_concepts = [cid for cid, perf in student_data.items()
                     if perf.last_accessed and perf.last_accessed < week_ago]

    if len(stale_concepts) > 0:
        recommendations.append(f"Consider reviewing {len(stale_concepts)} concepts you haven't practiced recently.")

    return recommendations
