"""
Advanced Automated Content Generation tools for TutorX.
Generates interactive content, exercises, and adaptive learning materials.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash

MODEL = GeminiFlash()

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

@mcp.tool()
async def generate_interactive_exercise(concept: str, exercise_type: str = "problem_solving",
                                      difficulty_level: float = 0.5, 
                                      student_level: str = "intermediate") -> dict:
    """
    Generate interactive exercises with multiple components and adaptive features.
    
    Args:
        concept: The concept to create exercises for
        exercise_type: Type of exercise ('problem_solving', 'simulation', 'case_study', 'lab', 'project')
        difficulty_level: Difficulty level (0.0 to 1.0)
        student_level: Student's academic level
        
    Returns:
        Dictionary with interactive exercise content
    """
    try:
        prompt = f"""
        Create an interactive {exercise_type} exercise for the concept: "{concept}"
        
        Exercise Parameters:
        - Difficulty Level: {difficulty_level:.2f}/1.0
        - Student Level: {student_level}
        - Exercise Type: {exercise_type}
        
        Generate a comprehensive interactive exercise that includes:
        1. Clear learning objectives
        2. Step-by-step instructions
        3. Interactive components that engage the student
        4. Multiple difficulty levels within the exercise
        5. Real-time feedback mechanisms
        6. Assessment criteria
        7. Extension activities for advanced students
        
        Return JSON with:
        - "exercise_id": unique identifier
        - "title": engaging title for the exercise
        - "learning_objectives": list of specific learning goals
        - "introduction": engaging introduction to the exercise
        - "instructions": detailed step-by-step instructions
        - "interactive_components": list of interactive elements
        - "materials_needed": required materials or resources
        - "estimated_time": estimated completion time in minutes
        - "difficulty_variations": easier and harder versions
        - "assessment_rubric": criteria for evaluating student work
        - "feedback_prompts": questions for self-reflection
        - "extension_activities": additional challenges for advanced students
        - "real_world_connections": how this relates to real-world applications
        """
        
        response = await MODEL.generate_text(prompt, temperature=0.7)
        exercise_data = extract_json_from_text(response)
        
        # Add metadata
        exercise_data.update({
            "success": True,
            "concept": concept,
            "exercise_type": exercise_type,
            "difficulty_level": difficulty_level,
            "student_level": student_level,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        })
        
        return exercise_data
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate interactive exercise: {str(e)}"
        }

@mcp.tool()
async def generate_adaptive_content_sequence(topic: str, student_profile: dict,
                                           sequence_length: int = 5) -> dict:
    """
    Generate a sequence of adaptive content that adjusts based on student profile.
    
    Args:
        topic: Main topic for the content sequence
        student_profile: Student's learning profile and preferences
        sequence_length: Number of content pieces in the sequence
        
    Returns:
        Dictionary with adaptive content sequence
    """
    try:
        prompt = f"""
        Create an adaptive content sequence for the topic: "{topic}"
        
        Student Profile:
        {json.dumps(student_profile, indent=2)}
        
        Generate a sequence of {sequence_length} interconnected content pieces that:
        1. Build upon each other progressively
        2. Adapt to the student's learning style and preferences
        3. Include multiple content types (text, visual descriptions, interactive elements)
        4. Provide branching paths based on understanding
        5. Include assessment checkpoints
        6. Offer remediation and enrichment options
        
        Return JSON with:
        - "sequence_id": unique identifier for the sequence
        - "topic": main topic
        - "total_pieces": number of content pieces
        - "estimated_total_time": total estimated time in minutes
        - "content_sequence": array of content pieces, each with:
          - "piece_id": unique identifier
          - "title": content title
          - "content_type": type of content (explanation, example, practice, assessment)
          - "content": main content text
          - "visual_elements": descriptions of visual components
          - "interactive_elements": interactive components
          - "difficulty_level": difficulty rating
          - "prerequisites": what student should know
          - "learning_objectives": specific objectives for this piece
          - "assessment_questions": questions to check understanding
          - "branching_options": different paths based on performance
          - "estimated_time": time for this piece
        - "adaptation_rules": rules for how content adapts to student responses
        - "success_criteria": criteria for successful completion
        """
        
        response = await MODEL.generate_text(prompt, temperature=0.6)
        sequence_data = extract_json_from_text(response)
        
        # Add metadata
        sequence_data.update({
            "success": True,
            "topic": topic,
            "student_profile": student_profile,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        })
        
        return sequence_data
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate adaptive content sequence: {str(e)}"
        }

@mcp.tool()
async def generate_scenario_based_learning(concept: str, scenario_type: str = "real_world",
                                         complexity_level: str = "moderate") -> dict:
    """
    Generate scenario-based learning content with realistic situations.
    
    Args:
        concept: The concept to teach through scenarios
        scenario_type: Type of scenario ('real_world', 'historical', 'futuristic', 'problem_solving')
        complexity_level: Complexity of the scenario ('simple', 'moderate', 'complex')
        
    Returns:
        Dictionary with scenario-based learning content
    """
    try:
        prompt = f"""
        Create a {scenario_type} scenario-based learning experience for: "{concept}"
        
        Scenario Parameters:
        - Type: {scenario_type}
        - Complexity: {complexity_level}
        
        Design a realistic scenario that:
        1. Presents the concept in a meaningful context
        2. Requires students to apply their knowledge
        3. Includes decision points and consequences
        4. Provides multiple solution paths
        5. Connects to real-world applications
        6. Engages students emotionally and intellectually
        
        Return JSON with:
        - "scenario_id": unique identifier
        - "title": compelling scenario title
        - "setting": detailed description of the scenario setting
        - "background_story": engaging background narrative
        - "main_challenge": primary challenge students must solve
        - "characters": key characters in the scenario (if applicable)
        - "decision_points": critical decisions students must make
        - "possible_outcomes": different outcomes based on decisions
        - "learning_integration": how the concept is woven into the scenario
        - "assessment_criteria": how to evaluate student responses
        - "discussion_questions": questions for reflection and discussion
        - "extension_scenarios": related scenarios for further exploration
        - "real_world_connections": connections to actual situations
        - "resources": additional resources students might need
        """
        
        response = await MODEL.generate_text(prompt, temperature=0.8)
        scenario_data = extract_json_from_text(response)
        
        # Add metadata
        scenario_data.update({
            "success": True,
            "concept": concept,
            "scenario_type": scenario_type,
            "complexity_level": complexity_level,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        })
        
        return scenario_data
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate scenario-based learning: {str(e)}"
        }

@mcp.tool()
async def generate_multimodal_content(concept: str, modalities: List[str] = None,
                                    target_audience: str = "general") -> dict:
    """
    Generate multi-modal content that appeals to different learning styles.
    
    Args:
        concept: The concept to create content for
        modalities: List of modalities to include ('visual', 'auditory', 'kinesthetic', 'reading')
        target_audience: Target audience description
        
    Returns:
        Dictionary with multi-modal content
    """
    try:
        if not modalities:
            modalities = ["visual", "auditory", "kinesthetic", "reading"]
            
        prompt = f"""
        Create multi-modal content for the concept: "{concept}"
        
        Target Audience: {target_audience}
        Modalities to include: {modalities}
        
        Generate content that appeals to different learning styles:
        
        Return JSON with:
        - "content_id": unique identifier
        - "concept": the main concept
        - "visual_content": content for visual learners (descriptions of diagrams, charts, images)
        - "auditory_content": content for auditory learners (descriptions of sounds, music, verbal explanations)
        - "kinesthetic_content": content for kinesthetic learners (hands-on activities, movement, manipulation)
        - "reading_content": content for reading/writing learners (text-based materials, written exercises)
        - "integrated_activities": activities that combine multiple modalities
        - "accessibility_features": features for students with different abilities
        - "technology_integration": how technology can enhance each modality
        - "assessment_variations": different ways to assess understanding for each modality
        - "adaptation_guidelines": how to adapt content for different needs
        """
        
        response = await MODEL.generate_text(prompt, temperature=0.7)
        content_data = extract_json_from_text(response)
        
        # Add metadata
        content_data.update({
            "success": True,
            "concept": concept,
            "modalities": modalities,
            "target_audience": target_audience,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        })
        
        return content_data
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate multimodal content: {str(e)}"
        }

@mcp.tool()
async def generate_adaptive_assessment(concept: str, assessment_type: str = "formative",
                                     student_data: dict = None) -> dict:
    """
    Generate adaptive assessments that adjust based on student responses.

    Args:
        concept: The concept to assess
        assessment_type: Type of assessment ('formative', 'summative', 'diagnostic', 'peer')
        student_data: Optional student performance data

    Returns:
        Dictionary with adaptive assessment content
    """
    try:
        prompt = f"""
        Create an adaptive {assessment_type} assessment for: "{concept}"

        Student Data: {json.dumps(student_data or {}, indent=2)}

        Design an assessment that:
        1. Adapts difficulty based on student responses
        2. Provides immediate feedback
        3. Identifies learning gaps
        4. Offers multiple question types
        5. Includes branching logic
        6. Provides detailed analytics

        Return JSON with:
        - "assessment_id": unique identifier
        - "title": assessment title
        - "instructions": clear instructions for students
        - "question_pool": large pool of questions with metadata:
          - "question_id": unique identifier
          - "question_text": the question
          - "question_type": type (multiple_choice, short_answer, essay, etc.)
          - "difficulty_level": difficulty rating (0.0 to 1.0)
          - "cognitive_level": Bloom's taxonomy level
          - "options": answer options (if applicable)
          - "correct_answer": correct answer
          - "explanation": detailed explanation
          - "hints": progressive hints
          - "common_misconceptions": common wrong answers and why
        - "adaptive_rules": rules for question selection and difficulty adjustment
        - "feedback_templates": templates for different types of feedback
        - "scoring_rubric": detailed scoring criteria
        - "analytics_tracking": what data to track for analysis
        - "remediation_suggestions": suggestions based on performance
        """

        response = await MODEL.generate_text(prompt, temperature=0.6)
        assessment_data = extract_json_from_text(response)

        # Add metadata
        assessment_data.update({
            "success": True,
            "concept": concept,
            "assessment_type": assessment_type,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        })

        return assessment_data

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate adaptive assessment: {str(e)}"
        }

@mcp.tool()
async def generate_gamified_content(concept: str, game_type: str = "quest",
                                  target_age_group: str = "teen") -> dict:
    """
    Generate gamified learning content with game mechanics and engagement features.

    Args:
        concept: The concept to gamify
        game_type: Type of game ('quest', 'puzzle', 'simulation', 'competition', 'story')
        target_age_group: Target age group ('child', 'teen', 'adult')

    Returns:
        Dictionary with gamified content
    """
    try:
        prompt = f"""
        Create gamified learning content for: "{concept}"

        Game Parameters:
        - Game Type: {game_type}
        - Target Age Group: {target_age_group}

        Design engaging game-based learning that includes:
        1. Clear game objectives aligned with learning goals
        2. Progressive difficulty levels
        3. Reward systems and achievements
        4. Interactive challenges
        5. Narrative elements (if applicable)
        6. Social features for collaboration/competition

        Return JSON with:
        - "game_id": unique identifier
        - "title": engaging game title
        - "theme": game theme and setting
        - "storyline": narrative framework (if applicable)
        - "learning_objectives": educational goals
        - "game_mechanics": core game mechanics and rules
        - "levels": progressive levels with increasing difficulty
        - "challenges": specific challenges and tasks
        - "reward_system": points, badges, achievements
        - "character_progression": how players advance
        - "social_features": multiplayer or collaborative elements
        - "assessment_integration": how learning is assessed within the game
        - "feedback_mechanisms": how players receive feedback
        - "customization_options": ways to personalize the experience
        - "accessibility_features": features for different abilities
        """

        response = await MODEL.generate_text(prompt, temperature=0.8)
        game_data = extract_json_from_text(response)

        # Add metadata
        game_data.update({
            "success": True,
            "concept": concept,
            "game_type": game_type,
            "target_age_group": target_age_group,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        })

        return game_data

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate gamified content: {str(e)}"
        }

@mcp.tool()
async def validate_generated_content(content_data: dict, validation_criteria: dict = None) -> dict:
    """
    Validate and quality-check generated educational content.

    Args:
        content_data: The content to validate
        validation_criteria: Specific criteria for validation

    Returns:
        Dictionary with validation results and suggestions
    """
    try:
        default_criteria = {
            "educational_alignment": True,
            "age_appropriateness": True,
            "clarity": True,
            "engagement": True,
            "accessibility": True,
            "accuracy": True
        }

        criteria = {**default_criteria, **(validation_criteria or {})}

        prompt = f"""
        Validate this educational content against quality criteria:

        Content to Validate:
        {json.dumps(content_data, indent=2)}

        Validation Criteria:
        {json.dumps(criteria, indent=2)}

        Perform comprehensive validation and return JSON with:
        - "overall_quality_score": score from 0.0 to 1.0
        - "validation_results": detailed results for each criterion
        - "strengths": identified strengths in the content
        - "areas_for_improvement": specific areas that need work
        - "suggestions": concrete suggestions for improvement
        - "compliance_check": compliance with educational standards
        - "accessibility_assessment": accessibility for different learners
        - "engagement_analysis": analysis of engagement potential
        - "accuracy_verification": verification of factual accuracy
        - "recommended_modifications": specific modifications to make
        """

        response = await MODEL.generate_text(prompt, temperature=0.3)
        validation_data = extract_json_from_text(response)

        return {
            "success": True,
            "content_validated": True,
            "validation_timestamp": datetime.utcnow().isoformat(),
            **validation_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to validate content: {str(e)}"
        }
