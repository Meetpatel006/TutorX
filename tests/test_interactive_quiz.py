"""
Test script for Interactive Quiz functionality
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the interactive quiz tools
from mcp_server.tools.quiz_tools import (
    generate_quiz_tool,
    start_interactive_quiz_tool,
    submit_quiz_answer_tool,
    get_quiz_hint_tool,
    get_quiz_session_status_tool
)

async def test_interactive_quiz():
    """Test the complete interactive quiz workflow"""
    print("🧪 Testing Interactive Quiz Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Generate a quiz
        print("\n1. 📝 Generating Quiz...")
        quiz_data = await generate_quiz_tool("Linear Equations", "medium")
        print(f"   ✅ Quiz generated: {quiz_data.get('quiz_title', 'N/A')}")
        
        if "error" in quiz_data:
            print(f"   ❌ Error generating quiz: {quiz_data['error']}")
            return
        
        # Test 2: Start interactive quiz session
        print("\n2. 🚀 Starting Interactive Quiz Session...")
        session_result = await start_interactive_quiz_tool(quiz_data, "test_student_001")
        print(f"   ✅ Session started: {session_result.get('session_id', 'N/A')}")
        
        if "error" in session_result:
            print(f"   ❌ Error starting session: {session_result['error']}")
            return
        
        session_id = session_result.get('session_id')
        first_question = session_result.get('question', {})
        
        print(f"   📊 Total questions: {session_result.get('total_questions', 0)}")
        print(f"   ❓ First question: {first_question.get('question', 'N/A')[:50]}...")
        
        # Test 3: Get a hint for the first question
        print("\n3. 💡 Getting Hint...")
        question_id = first_question.get('question_id')
        hint_result = await get_quiz_hint_tool(session_id, question_id)
        print(f"   ✅ Hint: {hint_result.get('hint', 'N/A')[:50]}...")
        
        # Test 4: Submit an answer (let's try the first option)
        print("\n4. ✍️ Submitting Answer...")
        options = first_question.get('options', [])
        if options:
            selected_answer = options[0]  # Select first option
            answer_result = await submit_quiz_answer_tool(session_id, question_id, selected_answer)
            
            print(f"   ✅ Answer submitted: {selected_answer}")
            print(f"   📊 Correct: {answer_result.get('is_correct', False)}")
            print(f"   💯 Score: {answer_result.get('score', 0)}/{answer_result.get('total_questions', 0)}")
            
            if answer_result.get('explanation'):
                print(f"   📖 Explanation: {answer_result['explanation'][:100]}...")
            
            # Check if there's a next question
            if answer_result.get('next_question'):
                next_q = answer_result['next_question']
                print(f"   ➡️ Next question: {next_q.get('question', 'N/A')[:50]}...")
                
                # Test 5: Submit answer for second question
                print("\n5. ✍️ Submitting Second Answer...")
                next_question_id = next_q.get('question_id')
                next_options = next_q.get('options', [])
                if next_options:
                    # Try the second option this time
                    selected_answer2 = next_options[1] if len(next_options) > 1 else next_options[0]
                    answer_result2 = await submit_quiz_answer_tool(session_id, next_question_id, selected_answer2)
                    
                    print(f"   ✅ Answer submitted: {selected_answer2}")
                    print(f"   📊 Correct: {answer_result2.get('is_correct', False)}")
                    print(f"   💯 Score: {answer_result2.get('score', 0)}/{answer_result2.get('total_questions', 0)}")
        
        # Test 6: Check session status
        print("\n6. 📊 Checking Session Status...")
        status_result = await get_quiz_session_status_tool(session_id)
        print(f"   ✅ Session status retrieved")
        print(f"   📈 Progress: {status_result.get('current_question', 0)}/{status_result.get('total_questions', 0)}")
        print(f"   💯 Final Score: {status_result.get('score', 0)}")
        print(f"   ✅ Completed: {status_result.get('completed', False)}")
        
        print("\n🎉 Interactive Quiz Test Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_interactive_quiz())
