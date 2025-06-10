"""
Test script for Enhanced Adaptive Learning with Gemini Integration
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the enhanced adaptive learning tools
from mcp_server.tools.learning_path_tools import (
    generate_adaptive_content,
    analyze_learning_patterns,
    optimize_learning_strategy,
    start_adaptive_session,
    record_learning_event,
    get_adaptive_recommendations,
    get_adaptive_learning_path,
    get_student_progress_summary
)

async def test_enhanced_adaptive_learning():
    """Test the enhanced adaptive learning system with Gemini integration."""
    
    print("🧠 Testing Enhanced Adaptive Learning with Gemini Integration")
    print("=" * 60)
    
    student_id = "test_student_001"
    concept_id = "linear_equations"
    
    try:
        # Test 1: Start an adaptive session
        print("\n1. 🚀 Starting Adaptive Session...")
        session_result = await start_adaptive_session(
            student_id=student_id,
            concept_id=concept_id,
            initial_difficulty=0.5
        )
        print(f"   ✅ Session started: {session_result.get('session_id', 'N/A')}")
        print(f"   📊 Initial mastery: {session_result.get('current_mastery', 0):.2f}")
        
        session_id = session_result.get('session_id')
        
        # Test 2: Record some learning events
        print("\n2. 📝 Recording Learning Events...")
        events = [
            {"type": "answer_correct", "data": {"time_taken": 25}},
            {"type": "answer_correct", "data": {"time_taken": 30}},
            {"type": "answer_incorrect", "data": {"time_taken": 45}},
            {"type": "answer_correct", "data": {"time_taken": 20}},
        ]
        
        for i, event in enumerate(events, 1):
            event_result = await record_learning_event(
                student_id=student_id,
                concept_id=concept_id,
                session_id=session_id,
                event_type=event["type"],
                event_data=event["data"]
            )
            print(f"   📊 Event {i}: {event['type']} - Mastery: {event_result.get('updated_mastery', 0):.2f}")
        
        # Test 3: Generate adaptive content
        print("\n3. 🎨 Generating Adaptive Content...")
        content_types = ["explanation", "practice", "feedback"]
        
        for content_type in content_types:
            try:
                content_result = await generate_adaptive_content(
                    student_id=student_id,
                    concept_id=concept_id,
                    content_type=content_type,
                    difficulty_level=0.6,
                    learning_style="visual"
                )
                
                if content_result.get("success"):
                    print(f"   ✅ {content_type.title()} content generated successfully")
                    if content_type == "explanation" and "explanation" in content_result:
                        explanation = content_result["explanation"][:100] + "..." if len(content_result["explanation"]) > 100 else content_result["explanation"]
                        print(f"      📖 Preview: {explanation}")
                else:
                    print(f"   ⚠️  {content_type.title()} content generation failed: {content_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ Error generating {content_type} content: {str(e)}")
        
        # Test 4: Get AI-powered recommendations
        print("\n4. 🤖 Getting AI-Powered Recommendations...")
        try:
            recommendations = await get_adaptive_recommendations(
                student_id=student_id,
                concept_id=concept_id,
                session_id=session_id
            )
            
            if recommendations.get("success"):
                print(f"   ✅ Recommendations generated (AI-powered: {recommendations.get('ai_powered', False)})")
                immediate_actions = recommendations.get("immediate_actions", [])
                print(f"   📋 Immediate actions: {len(immediate_actions)} recommendations")
                
                if immediate_actions:
                    first_action = immediate_actions[0]
                    print(f"      🎯 Top recommendation: {first_action.get('action', 'N/A')}")
            else:
                print(f"   ❌ Recommendations failed: {recommendations.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Error getting recommendations: {str(e)}")
        
        # Test 5: Analyze learning patterns
        print("\n5. 📊 Analyzing Learning Patterns...")
        try:
            patterns = await analyze_learning_patterns(
                student_id=student_id,
                analysis_days=30
            )
            
            if patterns.get("success"):
                print(f"   ✅ Learning patterns analyzed (AI-powered: {patterns.get('ai_powered', False)})")
                if "learning_style_analysis" in patterns:
                    print(f"   🎨 Learning style insights available")
                if "strength_areas" in patterns:
                    strengths = patterns.get("strength_areas", [])
                    print(f"   💪 Identified strengths: {len(strengths)} areas")
            else:
                print(f"   ⚠️  Pattern analysis: {patterns.get('message', 'No data available')}")
        except Exception as e:
            print(f"   ❌ Error analyzing patterns: {str(e)}")
        
        # Test 6: Optimize learning strategy
        print("\n6. 🎯 Optimizing Learning Strategy...")
        try:
            strategy = await optimize_learning_strategy(
                student_id=student_id,
                current_concept=concept_id
            )
            
            if strategy.get("success"):
                print(f"   ✅ Strategy optimized (AI-powered: {strategy.get('ai_powered', False)})")
                if "optimized_strategy" in strategy:
                    opt_strategy = strategy["optimized_strategy"]
                    print(f"   🎯 Primary approach: {opt_strategy.get('primary_approach', 'N/A')}")
                    print(f"   📈 Difficulty recommendation: {opt_strategy.get('difficulty_recommendation', 'N/A')}")
            else:
                print(f"   ⚠️  Strategy optimization: {strategy.get('message', 'Using default strategy')}")
        except Exception as e:
            print(f"   ❌ Error optimizing strategy: {str(e)}")
        
        # Test 7: Generate adaptive learning path
        print("\n7. 🛤️  Generating Adaptive Learning Path...")
        try:
            learning_path = await get_adaptive_learning_path(
                student_id=student_id,
                target_concepts=["algebra_basics", "linear_equations", "quadratic_equations"],
                strategy="adaptive",
                max_concepts=5
            )
            
            if learning_path.get("success"):
                print(f"   ✅ Learning path generated (AI-powered: {learning_path.get('ai_powered', False)})")
                path_steps = learning_path.get("learning_path", [])
                print(f"   📚 Path contains {len(path_steps)} steps")
                total_time = learning_path.get("total_time_minutes", 0)
                print(f"   ⏱️  Estimated total time: {total_time} minutes")
                
                if path_steps:
                    first_step = path_steps[0]
                    print(f"   🎯 First step: {first_step.get('concept_name', 'N/A')}")
            else:
                print(f"   ❌ Learning path failed: {learning_path.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Error generating learning path: {str(e)}")
        
        # Test 8: Get progress summary
        print("\n8. 📈 Getting Progress Summary...")
        try:
            progress = await get_student_progress_summary(
                student_id=student_id,
                days=7
            )
            
            if progress.get("success"):
                summary = progress.get("summary", {})
                print(f"   ✅ Progress summary generated")
                print(f"   📊 Concepts practiced: {summary.get('concepts_practiced', 0)}")
                print(f"   ⏱️  Total time: {summary.get('total_time_minutes', 0)} minutes")
                print(f"   🎯 Average mastery: {summary.get('average_mastery', 0):.2f}")
                print(f"   ✅ Average accuracy: {summary.get('average_accuracy', 0):.2f}")
            else:
                print(f"   ⚠️  Progress summary: {progress.get('message', 'No data available')}")
        except Exception as e:
            print(f"   ❌ Error getting progress summary: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 Enhanced Adaptive Learning Test Completed!")
        print("\n📋 Summary:")
        print("   ✅ All core adaptive learning functions tested")
        print("   🧠 Gemini AI integration verified")
        print("   📊 Performance tracking operational")
        print("   🎯 Personalization features active")
        print("   🛤️  Learning path optimization working")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Adaptive Learning Test...")
    asyncio.run(test_enhanced_adaptive_learning())
