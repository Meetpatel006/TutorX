"""
Test script for the new adaptive learning implementation.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the adaptive learning tools
from mcp_server.tools.learning_path_tools import (
    start_adaptive_session,
    record_learning_event,
    get_adaptive_recommendations,
    get_adaptive_learning_path,
    get_student_progress_summary
)

async def test_adaptive_learning():
    """Test the new adaptive learning system."""
    print("🧠 Testing New Adaptive Learning System")
    print("=" * 50)
    
    # Test 1: Start an adaptive session
    print("\n1. Starting adaptive session...")
    session_result = await start_adaptive_session(
        student_id="test_student_001",
        concept_id="algebra_linear_equations",
        initial_difficulty=0.5
    )
    print(f"Session Result: {session_result}")
    
    if session_result.get("success"):
        session_id = session_result.get("session_id")
        print(f"✅ Session started successfully: {session_id}")
        
        # Test 2: Record some learning events
        print("\n2. Recording learning events...")
        
        # Record a correct answer
        event_result1 = await record_learning_event(
            student_id="test_student_001",
            concept_id="algebra_linear_equations",
            session_id=session_id,
            event_type="answer_correct",
            event_data={"time_taken": 25, "difficulty": 0.5}
        )
        print(f"Event 1 (correct): {event_result1}")
        
        # Record an incorrect answer
        event_result2 = await record_learning_event(
            student_id="test_student_001",
            concept_id="algebra_linear_equations",
            session_id=session_id,
            event_type="answer_incorrect",
            event_data={"time_taken": 45, "difficulty": 0.5}
        )
        print(f"Event 2 (incorrect): {event_result2}")
        
        # Record another correct answer
        event_result3 = await record_learning_event(
            student_id="test_student_001",
            concept_id="algebra_linear_equations",
            session_id=session_id,
            event_type="answer_correct",
            event_data={"time_taken": 20, "difficulty": 0.5}
        )
        print(f"Event 3 (correct): {event_result3}")
        
        # Test 3: Get adaptive recommendations
        print("\n3. Getting adaptive recommendations...")
        recommendations = await get_adaptive_recommendations(
            student_id="test_student_001",
            concept_id="algebra_linear_equations",
            session_id=session_id
        )
        print(f"Recommendations: {recommendations}")
        
        # Test 4: Get adaptive learning path
        print("\n4. Getting adaptive learning path...")
        learning_path = await get_adaptive_learning_path(
            student_id="test_student_001",
            target_concepts=["algebra_basics", "linear_equations", "quadratic_equations"],
            strategy="adaptive",
            max_concepts=5
        )
        print(f"Learning Path: {learning_path}")
        
        # Test 5: Get progress summary
        print("\n5. Getting progress summary...")
        progress = await get_student_progress_summary(
            student_id="test_student_001",
            days=7
        )
        print(f"Progress Summary: {progress}")
        
        print("\n✅ All tests completed successfully!")
        
    else:
        print("❌ Failed to start session")

if __name__ == "__main__":
    asyncio.run(test_adaptive_learning())
