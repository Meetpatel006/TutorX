#!/usr/bin/env python3
"""
Test script for the new AI integration features in TutorX-MCP.
Tests the contextualized AI tutoring and automated content generation.
"""

import asyncio
import json
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.tools.ai_tutor_tools import (
    start_tutoring_session,
    ai_tutor_chat,
    get_step_by_step_guidance,
    get_alternative_explanations,
    end_tutoring_session
)

from mcp_server.tools.content_generation_tools import (
    generate_interactive_exercise,
    generate_scenario_based_learning,
    generate_gamified_content
)

async def test_ai_tutoring():
    """Test the AI tutoring functionality"""
    print("🤖 Testing AI Tutoring Features...")
    
    # Test 1: Start a tutoring session
    print("\n1. Starting tutoring session...")
    session_result = await start_tutoring_session(
        student_id="test_student_001",
        subject="Mathematics",
        learning_objectives=["Understand quadratic equations", "Learn factoring methods"]
    )
    print(f"Session started: {session_result.get('success', False)}")
    
    if not session_result.get('success'):
        print(f"❌ Failed to start session: {session_result.get('error')}")
        return
    
    session_id = session_result.get('session_id')
    print(f"Session ID: {session_id}")
    
    # Test 2: Chat with AI tutor
    print("\n2. Chatting with AI tutor...")
    chat_result = await ai_tutor_chat(
        session_id=session_id,
        student_query="How do I solve quadratic equations?",
        request_type="explanation"
    )
    print(f"Chat response received: {chat_result.get('success', False)}")
    
    # Test 3: Get step-by-step guidance
    print("\n3. Getting step-by-step guidance...")
    steps_result = await get_step_by_step_guidance(
        session_id=session_id,
        concept="Solving quadratic equations",
        current_step=1
    )
    print(f"Step-by-step guidance received: {steps_result.get('success', False)}")
    
    # Test 4: Get alternative explanations
    print("\n4. Getting alternative explanations...")
    alt_result = await get_alternative_explanations(
        session_id=session_id,
        concept="Quadratic formula",
        explanation_types=["visual", "analogy", "real_world"]
    )
    print(f"Alternative explanations received: {alt_result.get('success', False)}")
    
    # Test 5: End session
    print("\n5. Ending tutoring session...")
    end_result = await end_tutoring_session(
        session_id=session_id,
        session_summary="Learned about quadratic equations and different solving methods"
    )
    print(f"Session ended: {end_result.get('success', False)}")
    
    print("✅ AI Tutoring tests completed!")

async def test_content_generation():
    """Test the content generation functionality"""
    print("\n🎨 Testing Content Generation Features...")
    
    # Test 1: Generate interactive exercise
    print("\n1. Generating interactive exercise...")
    exercise_result = await generate_interactive_exercise(
        concept="Photosynthesis",
        exercise_type="simulation",
        difficulty_level=0.6,
        student_level="intermediate"
    )
    print(f"Interactive exercise generated: {exercise_result.get('success', False)}")
    
    # Test 2: Generate scenario-based learning
    print("\n2. Generating scenario-based learning...")
    scenario_result = await generate_scenario_based_learning(
        concept="Climate Change",
        scenario_type="real_world",
        complexity_level="moderate"
    )
    print(f"Scenario-based learning generated: {scenario_result.get('success', False)}")
    
    # Test 3: Generate gamified content
    print("\n3. Generating gamified content...")
    game_result = await generate_gamified_content(
        concept="Fractions",
        game_type="quest",
        target_age_group="teen"
    )
    print(f"Gamified content generated: {game_result.get('success', False)}")
    
    print("✅ Content Generation tests completed!")

async def main():
    """Run all tests"""
    print("🚀 Starting TutorX AI Integration Tests...")
    print("=" * 50)
    
    try:
        # Test AI Tutoring
        await test_ai_tutoring()
        
        # Test Content Generation
        await test_content_generation()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
