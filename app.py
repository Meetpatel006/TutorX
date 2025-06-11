"""
Gradio web interface for the TutorX MCP Server with SSE support
"""

import os
import json
import asyncio
import gradio as gr
from typing import Optional, Dict,  List, Tuple
import requests
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime

# Set matplotlib to use 'Agg' backend to avoid GUI issues in Gradio
matplotlib.use('Agg')

# Import MCP client components
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

# Server configuration
# SERVER_URL = "http://localhost:8000/sse"  # Ensure this is the SSE endpoint
SERVER_URL = "https://tutorx-mcp.onrender.com/sse"
# Utility functions

async def ping_mcp_server() -> None:
    """Send a ping request to the MCP server"""
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully pinged MCP server")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error pinging MCP server: {str(e)}")

async def start_periodic_ping(interval_minutes: int = 10) -> None:
    """Start a background task to ping the MCP server periodically"""
    while True:
        await ping_mcp_server()
        await asyncio.sleep(interval_minutes * 60)

# Store the ping task reference
ping_task = None

async def check_plagiarism_async(submission, reference):
    """Check submission for plagiarism against reference sources"""
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool(
                "check_submission_originality",
                {
                    "submission": submission,
                    "reference_sources": [reference] if isinstance(reference, str) else reference
                }
            )
            return await extract_response_content(response)

def start_ping_task():
    """Start the ping task when the Gradio app launches"""
    global ping_task
    try:
        if ping_task is None:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                ping_task = loop.create_task(start_periodic_ping())
                print("Started periodic ping task")
            else:
                # If loop is not running, we'll start it in a separate thread
                import threading
                def start_loop():
                    asyncio.set_event_loop(loop)
                    loop.run_forever()
                
                thread = threading.Thread(target=start_loop, daemon=True)
                thread.start()
                ping_task = asyncio.run_coroutine_threadsafe(start_periodic_ping(), loop)
                print("Started periodic ping task in new thread")
    except Exception as e:
        print(f"Error starting ping task: {e}")

# Only run this code when the module is executed directly
if __name__ == "__main__" and not hasattr(gr, 'blocks'):
    # This ensures we don't start the task when imported by Gradio
    start_ping_task()



async def load_concept_graph(concept_id: str = None) -> Tuple[Optional[plt.Figure], Dict, List]:
    """
    Load and visualize the concept graph for a given concept ID.
    If no concept_id is provided, returns the first available concept.

    Args:
        concept_id: The ID or name of the concept to load

    Returns:
        tuple: (figure, concept_details, related_concepts) or (None, error_dict, [])
    """
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()

                # Call the concept graph tool
                result = await session.call_tool(
                    "get_concept_graph_tool",
                    {"concept_id": concept_id} if concept_id else {}
                )
                
                # Extract content if it's a TextContent object
                if hasattr(result, 'content') and isinstance(result.content, list):
                    for item in result.content:
                        if hasattr(item, 'text') and item.text:
                            try:
                                result = json.loads(item.text)
                                break
                            except json.JSONDecodeError as e:
                                return None, {"error": f"Failed to parse JSON from TextContent: {str(e)}"}, []

                # If result is a string, try to parse it as JSON
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError as e:
                        return None, {"error": f"Failed to parse concept graph data: {str(e)}"}, []
                
                # Handle backend error response
                if isinstance(result, dict) and "error" in result:
                    error_msg = f"Backend error: {result['error']}"
                    return None, {"error": error_msg}, []
                
                concept = None
                
                # Handle different response formats
                if isinstance(result, dict):
                    # Case 1: Direct concept object
                    if "id" in result or "name" in result:
                        concept = result
                    # Case 2: Response with 'concepts' list
                    elif "concepts" in result:
                        if result["concepts"]:
                            concept = result["concepts"][0] if not concept_id else None
                            # Try to find the requested concept by ID or name
                            if concept_id:
                                for c in result["concepts"]:
                                    if (isinstance(c, dict) and
                                        (c.get("id") == concept_id or
                                         str(c.get("name", "")).lower() == concept_id.lower())):
                                        concept = c
                                        break
                                if not concept:
                                    error_msg = f"Concept '{concept_id}' not found in the concept graph"
                                    return None, {"error": error_msg}, []
                        else:
                            error_msg = "No concepts found in the concept graph"
                            return None, {"error": error_msg}, []

                # If we still don't have a valid concept
                if not concept or not isinstance(concept, dict):
                    error_msg = "Could not extract valid concept data from response"
                    return None, {"error": error_msg}, []

                # Ensure required fields exist with defaults
                concept.setdefault('related_concepts', [])
                concept.setdefault('prerequisites', [])
                
                # Create a new directed graph
                G = nx.DiGraph()
                
                # Add the main concept node
                main_node_id = concept["id"]
                G.add_node(main_node_id, 
                          label=concept["name"], 
                          type="main",
                          description=concept["description"])
                
                # Add related concepts and edges
                all_related = []
                
                # Process related concepts
                for rel in concept.get('related_concepts', []):
                    if isinstance(rel, dict):
                        rel_id = rel.get('id', str(hash(str(rel.get('name', '')))))
                        rel_name = rel.get('name', 'Unnamed')
                        rel_desc = rel.get('description', 'Related concept')
                        
                        G.add_node(rel_id, 
                                 label=rel_name, 
                                 type="related",
                                 description=rel_desc)
                        G.add_edge(main_node_id, rel_id, type="related_to")
                        
                        all_related.append(["Related", rel_name, rel_desc])
                
                # Process prerequisites
                for prereq in concept.get('prerequisites', []):
                    if isinstance(prereq, dict):
                        prereq_id = prereq.get('id', str(hash(str(prereq.get('name', '')))))
                        prereq_name = f"[Prerequisite] {prereq.get('name', 'Unnamed')}"
                        prereq_desc = prereq.get('description', 'Prerequisite concept')
                        
                        G.add_node(prereq_id,
                                 label=prereq_name,
                                 type="prerequisite",
                                 description=prereq_desc)
                        G.add_edge(prereq_id, main_node_id, type="prerequisite_for")
                        
                        all_related.append(["Prerequisite", prereq_name, prereq_desc])
                
                # Create the plot
                plt.figure(figsize=(14, 10))
                
                # Calculate node positions using spring layout
                pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
                
                # Define node colors and sizes based on type
                node_colors = []
                node_sizes = []
                for node, data in G.nodes(data=True):
                    if data.get('type') == 'main':
                        node_colors.append('#4e79a7')  # Blue for main concept
                        node_sizes.append(1500)
                    elif data.get('type') == 'prerequisite':
                        node_colors.append('#59a14f')  # Green for prerequisites
                        node_sizes.append(1000)
                    else:  # related
                        node_colors.append('#e15759')  # Red for related concepts
                        node_sizes.append(1000)
                
                # Draw nodes
                nx.draw_networkx_nodes(
                    G, pos,
                    node_color=node_colors,
                    node_size=node_sizes,
                    alpha=0.9,
                    edgecolors='white',
                    linewidths=2
                )
                
                # Draw edges with different styles for different relationships
                related_edges = [(u, v) for u, v, d in G.edges(data=True) 
                              if d.get('type') == 'related_to']
                prereq_edges = [(u, v) for u, v, d in G.edges(data=True) 
                             if d.get('type') == 'prerequisite_for']
                
                # Draw related edges
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=related_edges,
                    width=1.5,
                    alpha=0.7,
                    edge_color="#e15759",
                    style="solid",
                    arrowsize=15,
                    arrowstyle='-|>',
                    connectionstyle='arc3,rad=0.1'
                )
                
                # Draw prerequisite edges
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=prereq_edges,
                    width=1.5,
                    alpha=0.7,
                    edge_color="#59a14f",
                    style="dashed",
                    arrowsize=15,
                    arrowstyle='-|>',
                    connectionstyle='arc3,rad=0.1'
                )
                
                # Draw node labels with white background for better readability
                node_labels = {node: data["label"] 
                             for node, data in G.nodes(data=True) 
                             if "label" in data}
                
                nx.draw_networkx_labels(
                    G, pos,
                    labels=node_labels,
                    font_size=10,
                    font_weight="bold",
                    font_family="sans-serif",
                    bbox=dict(
                        facecolor="white",
                        edgecolor='none',
                        alpha=0.8,
                        boxstyle='round,pad=0.3',
                        linewidth=0
                    )
                )
                
                # Add a legend
                import matplotlib.patches as mpatches
                legend_elements = [
                    mpatches.Patch(facecolor='#4e79a7', label='Main Concept', alpha=0.9),
                    mpatches.Patch(facecolor='#e15759', label='Related Concept', alpha=0.9),
                    mpatches.Patch(facecolor='#59a14f', label='Prerequisite', alpha=0.9)
                ]
                
                plt.legend(
                    handles=legend_elements, 
                    loc='upper right',
                    bbox_to_anchor=(1.0, 1.0),
                    frameon=True,
                    framealpha=0.9
                )
                
                plt.axis('off')
                plt.tight_layout()
                
                # Create concept details dictionary
                concept_details = {
                    'name': concept['name'],
                    'id': concept['id'],
                    'description': concept['description']
                }
                
                # Return the figure, concept details, and related concepts
                return plt.gcf(), concept_details, all_related
                
    except Exception as e:
        return None, {"error": f"Failed to load concept graph: {str(e)}"}, []

def sync_load_concept_graph(concept_id):
    """Synchronous wrapper for async load_concept_graph, always returns 3 outputs."""
    try:
        result = asyncio.run(load_concept_graph(concept_id))
        if result and len(result) == 3:
            return result
        else:
            return None, {"error": "Unexpected result format"}, []
    except Exception as e:
        return None, {"error": str(e)}, []

# Synchronous wrapper functions for Gradio
def sync_check_plagiarism(submission, reference):
    """Synchronous wrapper for check_plagiarism_async"""
    try:
        return asyncio.run(check_plagiarism_async(submission, reference))
    except Exception as e:
        return {"error": str(e)}

# Interactive Quiz synchronous wrappers
def sync_start_interactive_quiz(quiz_data, student_id):
    """Synchronous wrapper for start_interactive_quiz_async"""
    try:
        return asyncio.run(start_interactive_quiz_async(quiz_data, student_id))
    except Exception as e:
        return {"error": str(e)}

def sync_submit_quiz_answer(session_id, question_id, selected_answer):
    """Synchronous wrapper for submit_quiz_answer_async"""
    try:
        return asyncio.run(submit_quiz_answer_async(session_id, question_id, selected_answer))
    except Exception as e:
        return {"error": str(e)}

def sync_get_quiz_hint(session_id, question_id):
    """Synchronous wrapper for get_quiz_hint_async"""
    try:
        return asyncio.run(get_quiz_hint_async(session_id, question_id))
    except Exception as e:
        return {"error": str(e)}

def sync_get_quiz_session_status(session_id):
    """Synchronous wrapper for get_quiz_session_status_async"""
    try:
        return asyncio.run(get_quiz_session_status_async(session_id))
    except Exception as e:
        return {"error": str(e)}

# Helper functions for interactive quiz interface
def format_question_display(quiz_session_data):
    """Format quiz session data for display"""
    if not quiz_session_data or "error" in quiz_session_data:
        return "❌ No active quiz session"

    question = quiz_session_data.get("question", {})
    if not question:
        return "✅ Quiz completed or no current question"

    question_text = question.get("question", "")
    options = question.get("options", [])
    question_num = quiz_session_data.get("current_question_number", 1)
    total = quiz_session_data.get("total_questions", 1)

    display_text = f"""
### Question {question_num} of {total}

**{question_text}**

**Options:**
"""
    for option in options:
        display_text += f"\n- {option}"

    return display_text

def update_answer_options(quiz_session_data):
    """Update answer options based on current question"""
    if not quiz_session_data or "error" in quiz_session_data:
        return gr.Radio(choices=["No options available"], value=None)

    question = quiz_session_data.get("question", {})
    options = question.get("options", ["A) Option A", "B) Option B", "C) Option C", "D) Option D"])

    return gr.Radio(choices=options, value=None, label="Select Your Answer")

def extract_question_id(quiz_session_data):
    """Extract question ID from quiz session data"""
    if not quiz_session_data or "error" in quiz_session_data:
        return ""

    question = quiz_session_data.get("question", {})
    return question.get("question_id", "")

def sync_generate_quiz(concept, difficulty):
    """Synchronous wrapper for on_generate_quiz"""
    try:
        return asyncio.run(on_generate_quiz(concept, difficulty))
    except Exception as e:
        return {"error": str(e)}

def sync_generate_lesson(topic, grade, duration):
    """Synchronous wrapper for generate_lesson_async"""
    try:
        return asyncio.run(generate_lesson_async(topic, grade, duration))
    except Exception as e:
        return {"error": str(e)}

def sync_generate_learning_path(student_id, concept_ids, student_level):
    """Synchronous wrapper for on_generate_learning_path"""
    try:
        return asyncio.run(on_generate_learning_path(student_id, concept_ids, student_level))
    except Exception as e:
        return {"error": str(e)}

def sync_text_interaction(text, student_id):
    """Synchronous wrapper for text_interaction_async"""
    try:
        return asyncio.run(text_interaction_async(text, student_id))
    except Exception as e:
        return {"error": str(e)}

def sync_document_ocr(file):
    """Synchronous wrapper for document_ocr_async"""
    try:
        return asyncio.run(document_ocr_async(file))
    except Exception as e:
        return {"error": str(e)}

# Adaptive learning synchronous wrappers
def sync_start_adaptive_session(student_id, concept_id, difficulty):
    """Synchronous wrapper for start_adaptive_session_async"""
    try:
        return asyncio.run(start_adaptive_session_async(student_id, concept_id, difficulty))
    except Exception as e:
        return {"error": str(e)}

def sync_record_learning_event(student_id, concept_id, event_type, session_id, correct, time_taken):
    """Synchronous wrapper for record_learning_event_async"""
    try:
        return asyncio.run(record_learning_event_async(student_id, concept_id, event_type, session_id, correct, time_taken))
    except Exception as e:
        return {"error": str(e)}

def sync_get_adaptive_recommendations(student_id, concept_id, session_id=None):
    """Synchronous wrapper for get_adaptive_recommendations_async"""
    try:
        return asyncio.run(get_adaptive_recommendations_async(student_id, concept_id, session_id))
    except Exception as e:
        return {"error": str(e)}

def sync_get_adaptive_learning_path(student_id, concept_ids, strategy, max_concepts):
    """Synchronous wrapper for get_adaptive_learning_path_async"""
    try:
        return asyncio.run(get_adaptive_learning_path_async(student_id, concept_ids, strategy, max_concepts))
    except Exception as e:
        return {"error": str(e)}

def sync_get_progress_summary(student_id, days=7):
    """Synchronous wrapper for get_progress_summary_async"""
    try:
        return asyncio.run(get_progress_summary_async(student_id, days))
    except Exception as e:
        return {"error": str(e)}

# AI Tutoring synchronous wrappers
def sync_start_tutoring_session(student_id, subject, learning_objectives):
    """Synchronous wrapper for start_tutoring_session_async"""
    try:
        return asyncio.run(start_tutoring_session_async(student_id, subject, learning_objectives))
    except Exception as e:
        return {"error": str(e)}

def sync_ai_tutor_chat(session_id, student_query, request_type):
    """Synchronous wrapper for ai_tutor_chat_async"""
    try:
        return asyncio.run(ai_tutor_chat_async(session_id, student_query, request_type))
    except Exception as e:
        return {"error": str(e)}

def sync_get_step_by_step_guidance(session_id, concept, current_step):
    """Synchronous wrapper for get_step_by_step_guidance_async"""
    try:
        return asyncio.run(get_step_by_step_guidance_async(session_id, concept, current_step))
    except Exception as e:
        return {"error": str(e)}

def sync_get_alternative_explanations(session_id, concept, explanation_types):
    """Synchronous wrapper for get_alternative_explanations_async"""
    try:
        return asyncio.run(get_alternative_explanations_async(session_id, concept, explanation_types))
    except Exception as e:
        return {"error": str(e)}

def sync_end_tutoring_session(session_id, session_summary):
    """Synchronous wrapper for end_tutoring_session_async"""
    try:
        return asyncio.run(end_tutoring_session_async(session_id, session_summary))
    except Exception as e:
        return {"error": str(e)}

# Content Generation synchronous wrappers
def sync_generate_interactive_exercise(concept, exercise_type, difficulty_level, student_level):
    """Synchronous wrapper for generate_interactive_exercise_async"""
    try:
        return asyncio.run(generate_interactive_exercise_async(concept, exercise_type, difficulty_level, student_level))
    except Exception as e:
        return {"error": str(e)}

def sync_generate_scenario_based_learning(concept, scenario_type, complexity_level):
    """Synchronous wrapper for generate_scenario_based_learning_async"""
    try:
        return asyncio.run(generate_scenario_based_learning_async(concept, scenario_type, complexity_level))
    except Exception as e:
        return {"error": str(e)}

def sync_generate_gamified_content(concept, game_type, target_age_group):
    """Synchronous wrapper for generate_gamified_content_async"""
    try:
        return asyncio.run(generate_gamified_content_async(concept, game_type, target_age_group))
    except Exception as e:
        return {"error": str(e)}

# Define async functions outside the interface
async def on_generate_quiz(concept, difficulty):
    try:
        if not concept or not str(concept).strip():
            return {"error": "Please enter a concept"}
        try:
            difficulty = int(float(difficulty))
            difficulty = max(1, min(5, difficulty))
        except (ValueError, TypeError):
            difficulty = 3
        if difficulty <= 2:
            difficulty_str = "easy"
        elif difficulty == 3:
            difficulty_str = "medium"
        else:
            difficulty_str = "hard"
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("generate_quiz_tool", {"concept": concept.strip(), "difficulty": difficulty_str})
                return await extract_response_content(response)
    except Exception as e:
        import traceback
        return {
            "error": f"Error generating quiz: {str(e)}\n\n{traceback.format_exc()}"
        }

async def generate_lesson_async(topic, grade, duration):
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool("generate_lesson_tool", {"topic": topic, "grade_level": grade, "duration_minutes": duration})
            return await extract_response_content(response)

async def on_generate_learning_path(student_id, concept_ids, student_level):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("get_learning_path", {
                    "student_id": student_id,
                    "concept_ids": [c.strip() for c in concept_ids.split(",") if c.strip()],
                    "student_level": student_level
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

# New adaptive learning functions
async def start_adaptive_session_async(student_id, concept_id, difficulty):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("start_adaptive_session", {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "initial_difficulty": float(difficulty)
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

async def record_learning_event_async(student_id, concept_id, event_type, session_id, correct, time_taken):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("record_learning_event", {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "event_type": event_type,
                    "session_id": session_id,
                    "event_data": {"correct": correct, "time_taken": time_taken}
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

async def get_adaptive_recommendations_async(student_id, concept_id, session_id=None):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                params = {
                    "student_id": student_id,
                    "concept_id": concept_id
                }
                if session_id:
                    params["session_id"] = session_id
                result = await session.call_tool("get_adaptive_recommendations", params)
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}


async def get_adaptive_learning_path_async(student_id, concept_ids, strategy, max_concepts):
    try:
        # Parse concept_ids if it's a string
        if isinstance(concept_ids, str):
            concept_ids = [c.strip() for c in concept_ids.split(',') if c.strip()]

        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("get_adaptive_learning_path", {
                    "student_id": student_id,
                    "target_concepts": concept_ids,
                    "strategy": strategy,
                    "max_concepts": int(max_concepts)
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

async def get_progress_summary_async(student_id, days=7):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("get_student_progress_summary", {
                    "student_id": student_id,
                    "days": int(days)
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

# Interactive Quiz async functions
async def start_interactive_quiz_async(quiz_data, student_id):
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool("start_interactive_quiz_tool", {"quiz_data": quiz_data, "student_id": student_id})
            return await extract_response_content(response)

async def submit_quiz_answer_async(session_id, question_id, selected_answer):
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool("submit_quiz_answer_tool", {"session_id": session_id, "question_id": question_id, "selected_answer": selected_answer})
            return await extract_response_content(response)

async def get_quiz_hint_async(session_id, question_id):
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool("get_quiz_hint_tool", {"session_id": session_id, "question_id": question_id})
            return await extract_response_content(response)

async def get_quiz_session_status_async(session_id):
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool("get_quiz_session_status_tool", {"session_id": session_id})
            return await extract_response_content(response)

async def extract_response_content(response):
    """Helper function to extract content from MCP response"""
    # Handle direct dictionary responses (new format)
    if isinstance(response, dict):
        return response

    # Handle MCP response with content structure (CallToolResult format)
    if hasattr(response, 'content') and isinstance(response.content, list):
        for item in response.content:
            # Handle TextContent objects
            if hasattr(item, 'text') and item.text:
                try:
                    return json.loads(item.text)
                except Exception as e:
                    return {"error": f"Failed to parse response: {str(e)}", "raw_text": item.text}
            # Handle other content types
            elif hasattr(item, 'type') and item.type == 'text':
                try:
                    return json.loads(str(item))
                except Exception:
                    return {"error": "Failed to parse text content", "raw_text": str(item)}

    # Handle string responses
    if isinstance(response, str):
        try:
            return json.loads(response)
        except Exception:
            return {"error": "Failed to parse string response", "raw_text": response}

    # Handle any other response type - try to extract useful information
    if hasattr(response, '__dict__'):
        return {"error": "Unexpected response format", "type": type(response).__name__, "raw_text": str(response)}

    return {"error": "Unknown response format", "type": type(response).__name__, "raw_text": str(response)}

async def text_interaction_async(text, student_id):
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            response = await session.call_tool("text_interaction", {"query": text, "student_id": student_id})
            return await extract_response_content(response)

async def upload_file_to_storage(file_path):
    """Helper function to upload file to storage API"""
    try:
        url = "https://storage-bucket-api.vercel.app/upload"
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(url, files=files)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": f"Error uploading file to storage: {str(e)}", "success": False}

async def document_ocr_async(file):
    if not file:
        return {"error": "No file provided", "success": False}
    try:
        if isinstance(file, dict):
            file_path = file.get("path", "")
        else:
            file_path = file
        if not file_path or not os.path.exists(file_path):
            return {"error": "File not found", "success": False}
        upload_result = await upload_file_to_storage(file_path)
        if not upload_result.get("success"):
            return upload_result
        storage_url = upload_result.get("storage_url")
        if not storage_url:
            return {"error": "No storage URL returned from upload", "success": False}
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("mistral_document_ocr", {"document_url": storage_url})
                return await extract_response_content(response)
    except Exception as e:
        return {"error": f"Error processing document: {str(e)}", "success": False}

# AI Tutoring async functions
async def start_tutoring_session_async(student_id, subject, learning_objectives):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("start_tutoring_session", {
                    "student_id": student_id,
                    "subject": subject,
                    "learning_objectives": learning_objectives
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

async def ai_tutor_chat_async(session_id, student_query, request_type):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("ai_tutor_chat", {
                    "session_id": session_id,
                    "student_query": student_query,
                    "request_type": request_type
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

async def get_step_by_step_guidance_async(session_id, concept, current_step):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("get_step_by_step_guidance", {
                    "session_id": session_id,
                    "concept": concept,
                    "current_step": current_step
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

async def get_alternative_explanations_async(session_id, concept, explanation_types):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("get_alternative_explanations", {
                    "session_id": session_id,
                    "concept": concept,
                    "explanation_types": explanation_types
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

async def end_tutoring_session_async(session_id, session_summary):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("end_tutoring_session", {
                    "session_id": session_id,
                    "session_summary": session_summary
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

# Content Generation async functions
async def generate_interactive_exercise_async(concept, exercise_type, difficulty_level, student_level):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("generate_interactive_exercise", {
                    "concept": concept,
                    "exercise_type": exercise_type,
                    "difficulty_level": difficulty_level,
                    "student_level": student_level
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

async def generate_scenario_based_learning_async(concept, scenario_type, complexity_level):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("generate_scenario_based_learning", {
                    "concept": concept,
                    "scenario_type": scenario_type,
                    "complexity_level": complexity_level
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

async def generate_gamified_content_async(concept, game_type, target_age_group):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                response = await session.call_tool("generate_gamified_content", {
                    "concept": concept,
                    "game_type": game_type,
                    "target_age_group": target_age_group
                })
                return await extract_response_content(response)
    except Exception as e:
        return {"error": str(e)}

# Enhanced UI/UX helper functions with Gradio Soft theme colors
def get_info_card_html(title, description, icon="ℹ️"):
    """Get HTML for a consistent info card component matching Gradio Soft theme"""
    return f"""
    <div style="background: var(--background-fill-secondary, #f7f7f7);
                border-left: 4px solid var(--color-accent, #ff6b6b);
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: var(--radius-lg, 8px);
                border: 1px solid var(--border-color-primary, #e5e5e5);">
        <h4 style="margin: 0 0 0.5rem 0; color: var(--body-text-color, #374151); font-weight: 600;">
            {icon} {title}
        </h4>
        <p style="margin: 0; color: var(--body-text-color-subdued, #6b7280); font-size: 0.9rem; line-height: 1.5;">
            {description}
        </p>
    </div>
    """

def get_status_display_html(message, status_type="info"):
    """Get HTML for a status display with Gradio Soft theme compatible styling"""
    # Using softer, more muted colors that match Gradio Soft theme
    colors = {
        "success": "var(--color-green-500, #10b981)",
        "error": "var(--color-red-500, #ef4444)",
        "warning": "var(--color-yellow-500, #f59e0b)",
        "info": "var(--color-blue-500, #3b82f6)"
    }
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }

    color = colors.get(status_type, colors["info"])
    icon = icons.get(status_type, icons["info"])

    return f"""
    <div style="background: var(--background-fill-secondary, #f7f7f7);
                border: 1px solid {color};
                color: var(--body-text-color, #374151);
                padding: 0.75rem;
                border-radius: var(--radius-md, 6px);
                margin: 0.5rem 0;
                border-left: 4px solid {color};">
        <span style="color: {color}; font-weight: 600;">{icon}</span> {message}
    </div>
    """

def create_feature_section(title, description, icon="🔧"):
    """Create a consistent feature section header matching Gradio Soft theme"""
    gr.Markdown(f"""
    <div style="background: var(--color-accent-soft, #ff6b6b20);
                border: 1px solid var(--color-accent, #ff6b6b);
                color: var(--body-text-color, #374151);
                padding: 1.5rem;
                margin: 1rem 0 0.5rem 0;
                border-radius: var(--radius-lg, 8px);
                box-shadow: var(--shadow-drop, 0 1px 3px rgba(0,0,0,0.1));">
        <h2 style="margin: 0; font-size: 1.5rem; color: var(--body-text-color, #374151); font-weight: 700;">
            {icon} {title}
        </h2>
        <p style="margin: 0.5rem 0 0 0; color: var(--body-text-color-subdued, #6b7280); font-size: 0.95rem; line-height: 1.5;">
            {description}
        </p>
    </div>
    """)

# Create Gradio interface with enhanced UI/UX
def create_gradio_interface():
    # Set a default student ID for the demo
    student_id = "student_12345"

    # Custom CSS for enhanced styling - Gradio Soft theme compatible
    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
    }

    /* Tab navigation with Gradio Soft theme colors */
    .tab-nav {
        background: var(--color-accent-soft, #ff6b6b20) !important;
        border: 1px solid var(--color-accent, #ff6b6b) !important;
        border-radius: var(--radius-lg, 8px) var(--radius-lg, 8px) 0 0 !important;
    }

    .tab-nav button {
        color: var(--body-text-color, #374151) !important;
        font-weight: 500 !important;
        padding: 12px 20px !important;
        margin: 0 2px !important;
        border-radius: var(--radius-md, 6px) var(--radius-md, 6px) 0 0 !important;
        transition: all 0.3s ease !important;
        background: transparent !important;
    }

    .tab-nav button:hover {
        background: var(--color-accent-soft, #ff6b6b20) !important;
        transform: translateY(-1px) !important;
    }

    .tab-nav button.selected {
        background: var(--background-fill-primary, #ffffff) !important;
        color: var(--body-text-color, #374151) !important;
        box-shadow: var(--shadow-drop, 0 1px 3px rgba(0,0,0,0.1)) !important;
        border-bottom: 2px solid var(--color-accent, #ff6b6b) !important;
    }

    /* Accordion styling */
    .accordion {
        border: 1px solid var(--border-color-primary, #e5e5e5) !important;
        border-radius: var(--radius-lg, 8px) !important;
        margin: 0.5rem 0 !important;
        overflow: hidden !important;
        background: var(--background-fill-primary, #ffffff) !important;
    }

    .accordion summary {
        background: var(--background-fill-secondary, #f7f7f7) !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        border-bottom: 1px solid var(--border-color-primary, #e5e5e5) !important;
        color: var(--body-text-color, #374151) !important;
    }

    .accordion[open] summary {
        border-bottom: 1px solid var(--border-color-primary, #e5e5e5) !important;
    }

    /* Button styling with Gradio theme */
    .button-primary {
        background: var(--color-accent, #ff6b6b) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-radius: var(--radius-md, 6px) !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-drop, 0 1px 3px rgba(0,0,0,0.1)) !important;
    }

    .button-primary:hover {
        background: var(--color-accent-hover, #ff5252) !important;
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-drop-lg, 0 4px 6px rgba(0,0,0,0.1)) !important;
    }

    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid var(--border-color-primary, #e5e5e5);
        border-top: 3px solid var(--color-accent, #ff6b6b);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Status cards */
    .status-card {
        background: var(--background-fill-primary, #ffffff);
        border: 1px solid var(--border-color-primary, #e5e5e5);
        border-radius: var(--radius-lg, 8px);
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-drop, 0 1px 3px rgba(0,0,0,0.1));
    }

    /* Feature highlights */
    .feature-highlight {
        background: var(--color-accent, #ff6b6b);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: var(--radius-full, 20px);
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.25rem;
        box-shadow: var(--shadow-drop, 0 1px 3px rgba(0,0,0,0.1));
    }

    /* Custom scrollbar for better theme integration */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--background-fill-secondary, #f7f7f7);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--color-accent-soft, #ff6b6b40);
        border-radius: var(--radius-md, 6px);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--color-accent, #ff6b6b);
    }
    """

    with gr.Blocks(
        title="TutorX Educational AI",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:
        # Start the ping task when the app loads
        demo.load(
            fn=start_ping_task,
            inputs=None,
            outputs=None,
            queue=False
        )

        # Enhanced Header Section with Welcome and Quick Start - Gradio Soft theme
        with gr.Row():
            with gr.Column():
                gr.Markdown("""
                <div style="background: var(--background-fill-primary, #ffffff);
                           border: 2px solid var(--color-accent, #ff6b6b);
                           color: var(--body-text-color, #374151);
                           padding: 2rem;
                           border-radius: var(--radius-xl, 12px);
                           text-align: center;
                           margin-bottom: 1rem;
                           box-shadow: var(--shadow-drop-lg, 0 4px 6px rgba(0,0,0,0.1));">
                    <h1 style="margin: 0 0 1rem 0; font-size: 2.5rem; font-weight: 700; color: var(--body-text-color, #374151);">
                        🧠 TutorX Educational AI Platform
                    </h1>
                    <p style="margin: 0 0 1rem 0; font-size: 1.2rem; color: var(--body-text-color-subdued, #6b7280); line-height: 1.5;">
                        An adaptive, multi-modal, and collaborative AI tutoring platform with real-time personalization
                    </p>
                    <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-top: 1.5rem;">
                        <span class="feature-highlight">🎯 Adaptive Learning</span>
                        <span class="feature-highlight">🤖 AI Tutoring</span>
                        <span class="feature-highlight">📊 Real-time Analytics</span>
                        <span class="feature-highlight">🎮 Interactive Content</span>
                    </div>
                </div>
                """)

        # Quick Start Guide - Gradio Soft theme compatible
        with gr.Accordion("🚀 Quick Start Guide - New Users Start Here!", open=True):
            gr.Markdown("""
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div style="background: var(--background-fill-secondary, #f7f7f7);
                           padding: 1.5rem;
                           border-radius: var(--radius-lg, 8px);
                           border-left: 4px solid var(--color-green-500, #10b981);
                           border: 1px solid var(--border-color-primary, #e5e5e5);">
                    <h4 style="color: var(--color-green-500, #10b981); margin: 0 0 0.5rem 0; font-weight: 600;">🎯 Step 1: Explore Concepts</h4>
                    <p style="margin: 0; color: var(--body-text-color-subdued, #6b7280); line-height: 1.5;">Start with the <strong>Core Features</strong> tab to visualize concept relationships and generate your first quiz.</p>
                </div>
                <div style="background: var(--background-fill-secondary, #f7f7f7);
                           padding: 1.5rem;
                           border-radius: var(--radius-lg, 8px);
                           border-left: 4px solid var(--color-blue-500, #3b82f6);
                           border: 1px solid var(--border-color-primary, #e5e5e5);">
                    <h4 style="color: var(--color-blue-500, #3b82f6); margin: 0 0 0.5rem 0; font-weight: 600;">🤖 Step 2: Try AI Tutoring</h4>
                    <p style="margin: 0; color: var(--body-text-color-subdued, #6b7280); line-height: 1.5;">Visit the <strong>AI Tutoring</strong> tab for personalized, step-by-step learning assistance.</p>
                </div>
                <div style="background: var(--background-fill-secondary, #f7f7f7);
                           padding: 1.5rem;
                           border-radius: var(--radius-lg, 8px);
                           border-left: 4px solid var(--color-purple-500, #8b5cf6);
                           border: 1px solid var(--border-color-primary, #e5e5e5);">
                    <h4 style="color: var(--color-purple-500, #8b5cf6); margin: 0 0 0.5rem 0; font-weight: 600;">🧠 Step 3: Adaptive Learning</h4>
                    <p style="margin: 0; color: var(--body-text-color-subdued, #6b7280); line-height: 1.5;">Experience the <strong>Adaptive Learning</strong> system that adjusts to your performance in real-time.</p>
                </div>
            </div>
            """)
# Main Tabs with enhanced navigation
        with gr.Tabs():
            # Tab 1: Core Features - Enhanced with better organization
            with gr.Tab("🎯 Core Features", elem_id="core_features_tab"):
                # Feature section header
                create_feature_section(
                    "Concept Graph Visualization",
                    "Explore relationships between educational concepts through interactive graph visualization",
                    "🔍"
                )

                # Enhanced concept graph interface with better UX
                with gr.Row():
                    # Left panel - Controls and Information
                    with gr.Column(scale=3):
                        # Input section with enhanced styling
                        with gr.Group():
                            gr.Markdown("### 🎯 Concept Explorer")
                            concept_input = gr.Textbox(
                                label="Enter Concept to Explore",
                                placeholder="e.g., machine_learning, calculus, quantum_physics",
                                value="machine_learning",
                                info="Enter any educational concept to visualize its relationships"
                            )
                            with gr.Row():
                                load_btn = gr.Button("🔍 Load Graph", variant="primary", scale=2)
                                clear_btn = gr.Button("🗑️ Clear", variant="secondary", scale=1)

                        # Quick examples for easy access
                        with gr.Group():
                            gr.Markdown("### 💡 Quick Examples")
                            with gr.Row():
                                example_btns = []
                                examples = ["machine_learning", "calculus", "quantum_physics", "biology"]
                                for example in examples:
                                    btn = gr.Button(example.replace("_", " ").title(), size="sm")
                                    example_btns.append(btn)

                        # Concept details with enhanced presentation
                        with gr.Accordion("📋 Concept Details", open=True):
                            concept_details = gr.JSON(
                                label=None,
                                show_label=False
                            )

                        # Related concepts with better formatting
                        with gr.Accordion("🔗 Related Concepts & Prerequisites", open=True):
                            related_concepts = gr.Dataframe(
                                headers=["Type", "Name", "Description"],
                                datatype=["str", "str", "str"],
                                interactive=False,
                                wrap=True
                                # height=200
                            )

                    # Right panel - Graph visualization
                    with gr.Column(scale=7):
                        with gr.Group():
                            gr.Markdown("### 🌐 Interactive Concept Graph")
                            graph_plot = gr.Plot(
                                label=None,
                                show_label=False,
                                container=True
                            )

                            # Graph legend and instructions
                            gr.Markdown("""
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 6px; margin-top: 0.5rem;">
                                <strong>📖 Graph Legend:</strong><br>
                                🔵 <span style="color: #4e79a7;">Main Concept</span> |
                                🔴 <span style="color: #e15759;">Related Concepts</span> |
                                🟢 <span style="color: #59a14f;">Prerequisites</span><br>
                                <em>Tip: The graph shows how concepts connect and build upon each other</em>
                            </div>
                            """)

                # Enhanced event handlers with better UX
                def clear_concept_input():
                    return "", None, {"message": "Enter a concept to explore"}, []

                def load_example_concept(example):
                    return example

                # Main load button
                load_btn.click(
                    fn=sync_load_concept_graph,
                    inputs=[concept_input],
                    outputs=[graph_plot, concept_details, related_concepts]
                )

                # Clear button
                clear_btn.click(
                    fn=clear_concept_input,
                    inputs=[],
                    outputs=[concept_input, graph_plot, concept_details, related_concepts]
                )

                # Example buttons
                for i, (btn, example) in enumerate(zip(example_btns, examples)):
                    btn.click(
                        fn=lambda ex=example: load_example_concept(ex),
                        inputs=[],
                        outputs=[concept_input]
                    ).then(
                        fn=sync_load_concept_graph,
                        inputs=[concept_input],
                        outputs=[graph_plot, concept_details, related_concepts]
                    )

                # Load initial graph on startup
                demo.load(
                    fn=lambda: sync_load_concept_graph("machine_learning"),
                    outputs=[graph_plot, concept_details, related_concepts]
                )

                # Enhanced Assessment Generation Section
                create_feature_section(
                    "Assessment Generation",
                    "Create customized quizzes and assessments with immediate feedback and detailed explanations",
                    "📝"
                )

                with gr.Row():
                    # Left panel - Quiz configuration
                    with gr.Column(scale=2):
                        with gr.Group():
                            gr.Markdown("### ⚙️ Quiz Configuration")
                            quiz_concept_input = gr.Textbox(
                                label="📚 Concept or Topic",
                                placeholder="e.g., Linear Equations, Photosynthesis, World War II",
                                lines=2,
                                info="Enter the subject matter for your quiz"
                            )

                            with gr.Row():
                                diff_input = gr.Slider(
                                    minimum=1,
                                    maximum=5,
                                    value=3,
                                    step=1,
                                    label="🎯 Difficulty Level",
                                    info="1=Very Easy, 3=Medium, 5=Very Hard"
                                )

                            with gr.Row():
                                gen_quiz_btn = gr.Button("🎲 Generate Quiz", variant="primary", scale=2)
                                preview_btn = gr.Button("👁️ Preview", variant="secondary", scale=1)

                    # Right panel - Generated quiz display
                    with gr.Column(scale=3):
                        with gr.Group():
                            gr.Markdown("### 📋 Generated Quiz")
                            quiz_output = gr.JSON(
                                label=None,
                                show_label=False,
                                container=True
                            )

                            # Quiz statistics - Gradio Soft theme compatible
                            quiz_stats = gr.Markdown("""
                            <div style="background: var(--background-fill-secondary, #f7f7f7);
                                       padding: 1rem;
                                       border-radius: var(--radius-md, 6px);
                                       margin-top: 0.5rem;
                                       border: 1px solid var(--border-color-primary, #e5e5e5);">
                                <strong style="color: var(--body-text-color, #374151);">📊 Quiz will appear here after generation</strong><br>
                                <em style="color: var(--body-text-color-subdued, #6b7280);">Click "Generate Quiz" to create your assessment</em>
                            </div>
                            """)

                # Enhanced quiz generation with better UX
                def generate_quiz_with_feedback(concept, difficulty):
                    """Generate quiz with user-friendly feedback"""
                    if not concept or not concept.strip():
                        return {
                            "error": "Please enter a concept or topic for the quiz",
                            "status": "error"
                        }

                    # Show loading state
                    result = sync_generate_quiz(concept, difficulty)

                    # Add user-friendly formatting
                    if isinstance(result, dict) and "error" not in result:
                        # Add metadata for better display
                        result["_ui_metadata"] = {
                            "concept": concept,
                            "difficulty": difficulty,
                            "generated_at": "Just now",
                            "status": "success"
                        }

                    return result

                # Connect enhanced quiz generation
                gen_quiz_btn.click(
                    fn=generate_quiz_with_feedback,
                    inputs=[quiz_concept_input, diff_input],
                    outputs=[quiz_output],
                    api_name="generate_quiz"
                )

                # Enhanced Interactive Quiz Section
                create_feature_section(
                    "Interactive Quiz Taking",
                    "Take quizzes with immediate feedback, hints, and detailed explanations for enhanced learning",
                    "🎮"
                )

                # Quiz workflow with step-by-step guidance
                with gr.Accordion("🚀 Step 1: Start Interactive Quiz Session", open=True):
                    with gr.Row():
                        with gr.Column(scale=2):
                            with gr.Group():
                                gr.Markdown("### 👤 Student Information")
                                quiz_student_id = gr.Textbox(
                                    label="Student ID",
                                    value=student_id,
                                    info="Your unique identifier for tracking progress"
                                )
                                start_quiz_btn = gr.Button("🎯 Start Interactive Quiz", variant="primary")

                                gr.Markdown(get_info_card_html(
                                    "📋 Prerequisites",
                                    "Make sure you have generated a quiz above before starting an interactive session"
                                ))

                        with gr.Column(scale=3):
                            with gr.Group():
                                gr.Markdown("### 📊 Session Status")
                                quiz_session_output = gr.JSON(
                                    label=None,
                                    show_label=False
                                )

                # Enhanced Quiz Taking Interface
                with gr.Accordion("📝 Step 2: Answer Questions", open=True):
                    with gr.Row():
                        # Left panel - Question and controls
                        with gr.Column(scale=2):
                            with gr.Group():
                                gr.Markdown("### 🎯 Current Question")
                                session_id_input = gr.Textbox(
                                    label="Session ID",
                                    placeholder="Enter session ID from above",
                                    info="Copy the session ID from the status above"
                                )
                                question_id_input = gr.Textbox(
                                    label="Question ID",
                                    placeholder="e.g., q1",
                                    info="Current question identifier"
                                )

                                # Enhanced answer options
                                answer_choice = gr.Radio(
                                    choices=["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
                                    label="📋 Select Your Answer",
                                    value=None,
                                    info="Choose the best answer from the options below"
                                )

                                # Action buttons with better organization
                                with gr.Row():
                                    submit_answer_btn = gr.Button("✅ Submit Answer", variant="primary", scale=2)
                                    get_hint_btn = gr.Button("💡 Get Hint", variant="secondary", scale=1)

                                with gr.Row():
                                    check_status_btn = gr.Button("📊 Check Progress", variant="secondary")

                        # Right panel - Feedback and results
                        with gr.Column(scale=3):
                            with gr.Group():
                                gr.Markdown("### 📋 Question & Feedback")
                                current_question_display = gr.Markdown("*Start a quiz session to see questions here*")

                            with gr.Accordion("💬 Answer Feedback", open=True):
                                answer_feedback = gr.JSON(
                                    label=None,
                                    show_label=False
                                )

                            with gr.Accordion("💡 Hints & Help", open=False):
                                hint_output = gr.JSON(
                                    label=None,
                                    show_label=False
                                )

                # Enhanced Quiz Progress and Results
                with gr.Accordion("📊 Step 3: Track Progress & Results", open=True):
                    with gr.Row():
                        with gr.Column():
                            with gr.Group():
                                gr.Markdown("### 📈 Progress Overview")
                                quiz_stats_display = gr.JSON(
                                    label=None,
                                    show_label=False
                                )

                        with gr.Column():
                            with gr.Group():
                                gr.Markdown("### 🏆 Performance Summary")
                                performance_summary = gr.Markdown("""
                                <div style="background: var(--background-fill-secondary, #f7f7f7);
                                           padding: 1rem;
                                           border-radius: var(--radius-md, 6px);
                                           text-align: center;
                                           border: 1px solid var(--border-color-primary, #e5e5e5);">
                                    <strong style="color: var(--body-text-color, #374151);">📊 Complete a quiz to see your performance metrics</strong><br>
                                    <em style="color: var(--body-text-color-subdued, #6b7280);">Accuracy • Speed • Learning Progress</em>
                                </div>
                                """)

                # Connect interactive quiz buttons with enhanced functionality
                def start_quiz_with_display(student_id, quiz_data):
                    """Start quiz and update displays"""
                    if not quiz_data or "error" in quiz_data:
                        return {"error": "Please generate a quiz first"}, "*Please generate a quiz first*", gr.Radio(choices=["No options available"], value=None), ""

                    session_result = sync_start_interactive_quiz(quiz_data, student_id)
                    question_display = format_question_display(session_result)
                    answer_options = update_answer_options(session_result)
                    question_id = extract_question_id(session_result)

                    return session_result, question_display, answer_options, question_id

                def submit_answer_with_feedback(session_id, question_id, selected_answer):
                    """Submit answer and update displays"""
                    feedback = sync_submit_quiz_answer(session_id, question_id, selected_answer)

                    # Update question display if there's a next question
                    if "next_question" in feedback:
                        next_q_data = {"question": feedback["next_question"]}
                        question_display = format_question_display(next_q_data)
                        answer_options = update_answer_options(next_q_data)
                        next_question_id = feedback["next_question"].get("question_id", "")
                    else:
                        question_display = "✅ Quiz completed! Check your final results below."
                        answer_options = gr.Radio(choices=["Quiz completed"], value=None)
                        next_question_id = ""

                    return feedback, question_display, answer_options, next_question_id

                start_quiz_btn.click(
                    fn=start_quiz_with_display,
                    inputs=[quiz_student_id, quiz_output],
                    outputs=[quiz_session_output, current_question_display, answer_choice, question_id_input]
                )

                submit_answer_btn.click(
                    fn=submit_answer_with_feedback,
                    inputs=[session_id_input, question_id_input, answer_choice],
                    outputs=[answer_feedback, current_question_display, answer_choice, question_id_input]
                )

                get_hint_btn.click(
                    fn=sync_get_quiz_hint,
                    inputs=[session_id_input, question_id_input],
                    outputs=[hint_output]
                )

                check_status_btn.click(
                    fn=sync_get_quiz_session_status,
                    inputs=[session_id_input],
                    outputs=[quiz_stats_display]
                )

                # Instructions and Examples
                with gr.Accordion("📖 How to Use Interactive Quizzes", open=False):
                    gr.Markdown("""
                    ### 🚀 Quick Start Guide

                    **Step 1: Generate a Quiz**
                    1. Enter a concept (e.g., "Linear Equations", "Photosynthesis")
                    2. Set difficulty level (1-5)
                    3. Click "Generate Quiz"

                    **Step 2: Start Interactive Session**
                    1. Enter your Student ID
                    2. Click "Start Interactive Quiz"
                    3. Copy the Session ID for tracking

                    **Step 3: Answer Questions**
                    1. Read the question displayed
                    2. Select your answer from the options
                    3. Click "Submit Answer" for immediate feedback
                    4. Use "Get Hint" if you need help

                    **Step 4: Track Progress**
                    - Use "Check Status" to see your overall progress
                    - View explanations for each answer
                    - See your final score when completed

                    ### 🎯 Features
                    - **Immediate Feedback**: Get instant results for each answer
                    - **Detailed Explanations**: Understand why answers are correct/incorrect
                    - **Helpful Hints**: Get guidance when you're stuck
                    - **Progress Tracking**: Monitor your performance throughout
                    - **Adaptive Content**: Questions tailored to your difficulty level

                    ### 💡 Tips
                    - Read questions carefully before selecting answers
                    - Use hints strategically to learn concepts
                    - Review explanations to reinforce learning
                    - Track your progress to identify improvement areas
                    """)

                gr.Markdown("---")
            
            # Tab 2: Advanced Features - Enhanced
            with gr.Tab("📚 Advanced Features", elem_id="advanced_features_tab"):
                create_feature_section(
                    "Lesson Generation",
                    "Create comprehensive lesson plans with structured content and learning objectives",
                    "📖"
                )

                with gr.Row():
                    with gr.Column():
                        topic_input = gr.Textbox(label="Lesson Topic", value="Solving Quadratic Equations")
                        grade_input = gr.Slider(minimum=1, maximum=12, value=9, step=1, label="Grade Level")
                        duration_input = gr.Slider(minimum=15, maximum=90, value=45, step=5, label="Duration (minutes)")
                        gen_lesson_btn = gr.Button("Generate Lesson Plan")

                    with gr.Column():
                        lesson_output = gr.JSON(label="Lesson Plan")

                # Connect lesson generation button
                gen_lesson_btn.click(
                    fn=sync_generate_lesson,
                    inputs=[topic_input, grade_input, duration_input],
                    outputs=[lesson_output]
                )

                create_feature_section(
                    "Learning Path Generation",
                    "Enhanced with adaptive learning capabilities for personalized educational journeys",
                    "🛤️"
                )

                with gr.Row():
                    with gr.Column():
                        lp_student_id = gr.Textbox(label="Student ID", value=student_id)
                        lp_concept_ids = gr.Textbox(label="Concept IDs (comma-separated)", placeholder="e.g., python,functions,oop")
                        lp_student_level = gr.Dropdown(choices=["beginner", "intermediate", "advanced"], value="beginner", label="Student Level")

                        with gr.Row():
                            lp_btn = gr.Button("Generate Basic Path")
                            adaptive_lp_btn = gr.Button("Generate Adaptive Path", variant="primary")

                    with gr.Column():
                        lp_output = gr.JSON(label="Learning Path")

                # Connect learning path generation buttons
                lp_btn.click(
                    fn=sync_generate_learning_path,
                    inputs=[lp_student_id, lp_concept_ids, lp_student_level],
                    outputs=[lp_output]
                )

                adaptive_lp_btn.click(
                    fn=lambda sid, cids, _: sync_get_adaptive_learning_path(sid, cids, "adaptive", 10),
                    inputs=[lp_student_id, lp_concept_ids, lp_student_level],
                    outputs=[lp_output]
                )
        
            # Tab 3: Interactive Tools - Enhanced
            with gr.Tab("🛠️ Interactive Tools", elem_id="interactive_tools_tab"):
                create_feature_section(
                    "Text Interaction & Document Processing",
                    "Ask questions, get explanations, and process documents with AI-powered analysis",
                    "💬"
                )

                with gr.Row():
                    with gr.Column():
                        text_input = gr.Textbox(label="Ask a Question", value="How do I solve a quadratic equation?")
                        text_btn = gr.Button("Submit")

                    with gr.Column():
                        text_output = gr.JSON(label="Response")

                # Connect text interaction button
                text_btn.click(
                    fn=lambda text: sync_text_interaction(text, student_id),
                    inputs=[text_input],
                    outputs=[text_output]
                )

                # Document OCR (PDF, images, etc.)
                create_feature_section(
                    "Document OCR & LLM Analysis",
                    "Upload and analyze documents with advanced OCR and AI-powered content extraction",
                    "📄"
                )
                with gr.Row():
                    with gr.Column():
                        doc_input = gr.File(label="Upload PDF or Document", file_types=[".pdf", ".jpg", ".jpeg", ".png"])
                        doc_ocr_btn = gr.Button("Extract Text & Analyze")
                    with gr.Column():
                        doc_output = gr.JSON(label="Document OCR & LLM Analysis")

                # Connect document OCR button
                doc_ocr_btn.click(
                    fn=sync_document_ocr,
                    inputs=[doc_input],
                    outputs=[doc_output]
                )

            # Tab 4: AI Tutoring - Enhanced
            with gr.Tab("🤖 AI Tutoring", elem_id="ai_tutoring_tab"):
                create_feature_section(
                    "Contextualized AI Tutoring",
                    "Experience personalized AI tutoring with step-by-step guidance and alternative explanations",
                    "🤖"
                )

                with gr.Accordion("ℹ️ How AI Tutoring Works", open=False):
                    gr.Markdown("""
                    ### 🎯 Contextualized Learning
                    - **Session Memory**: AI remembers your conversation and adapts responses
                    - **Step-by-Step Guidance**: Break down complex concepts into manageable steps
                    - **Alternative Explanations**: Multiple ways to understand the same concept
                    - **Personalized Feedback**: Responses tailored to your understanding level

                    ### 🚀 Getting Started
                    1. Start a tutoring session with your preferred subject
                    2. Ask questions or request explanations
                    3. Get step-by-step guidance for complex topics
                    4. Request alternative explanations if needed
                    5. End session to get a comprehensive summary
                    """)

                # Tutoring Session Management
                with gr.Accordion("📚 Start Tutoring Session", open=True):
                    with gr.Row():
                        with gr.Column():
                            tutor_student_id = gr.Textbox(label="Student ID", value=student_id)
                            tutor_subject = gr.Textbox(label="Subject", value="Mathematics", placeholder="e.g., Mathematics, Physics, Chemistry")
                            tutor_objectives = gr.Textbox(
                                label="Learning Objectives (optional)",
                                placeholder="e.g., Understand quadratic equations, Learn calculus basics",
                                lines=2
                            )
                            start_tutor_btn = gr.Button("Start Tutoring Session", variant="primary")

                        with gr.Column():
                            tutor_session_output = gr.JSON(label="Session Information")

                # AI Chat Interface
                with gr.Accordion("💬 Chat with AI Tutor", open=True):
                    with gr.Row():
                        with gr.Column():
                            chat_session_id = gr.Textbox(label="Session ID", placeholder="Enter session ID from above")
                            chat_query = gr.Textbox(
                                label="Ask Your Question",
                                placeholder="e.g., How do I solve quadratic equations?",
                                lines=3
                            )
                            chat_request_type = gr.Dropdown(
                                choices=["explanation", "step_by_step", "alternative", "practice", "clarification"],
                                value="explanation",
                                label="Request Type"
                            )
                            chat_btn = gr.Button("Ask AI Tutor", variant="primary")

                        with gr.Column():
                            chat_response = gr.JSON(label="AI Tutor Response")

                # Step-by-Step Guidance
                with gr.Accordion("📋 Step-by-Step Guidance", open=True):
                    with gr.Row():
                        with gr.Column():
                            step_session_id = gr.Textbox(label="Session ID")
                            step_concept = gr.Textbox(label="Concept", placeholder="e.g., Solving quadratic equations")
                            step_current = gr.Number(label="Current Step", value=1, minimum=1)
                            get_steps_btn = gr.Button("Get Step-by-Step Guidance")

                        with gr.Column():
                            steps_output = gr.JSON(label="Step-by-Step Guidance")

                # Alternative Explanations
                with gr.Accordion("🔄 Alternative Explanations", open=True):
                    with gr.Row():
                        with gr.Column():
                            alt_session_id = gr.Textbox(label="Session ID")
                            alt_concept = gr.Textbox(label="Concept", placeholder="e.g., Photosynthesis")
                            alt_types = gr.CheckboxGroup(
                                choices=["visual", "analogy", "real_world", "simplified", "technical"],
                                value=["visual", "analogy", "real_world"],
                                label="Explanation Types"
                            )
                            get_alt_btn = gr.Button("Get Alternative Explanations")

                        with gr.Column():
                            alt_output = gr.JSON(label="Alternative Explanations")

                # Session Management
                with gr.Accordion("🔚 End Session & Summary", open=True):
                    with gr.Row():
                        with gr.Column():
                            end_session_id = gr.Textbox(label="Session ID")
                            session_summary = gr.Textbox(
                                label="Session Summary (optional)",
                                placeholder="What did you learn? Any feedback?",
                                lines=3
                            )
                            end_session_btn = gr.Button("End Session & Get Summary", variant="secondary")

                        with gr.Column():
                            session_end_output = gr.JSON(label="Session Summary")

                # Connect all AI tutoring buttons
                start_tutor_btn.click(
                    fn=lambda sid, subj, obj: sync_start_tutoring_session(sid, subj, obj.split(',') if obj else []),
                    inputs=[tutor_student_id, tutor_subject, tutor_objectives],
                    outputs=[tutor_session_output]
                )

                chat_btn.click(
                    fn=sync_ai_tutor_chat,
                    inputs=[chat_session_id, chat_query, chat_request_type],
                    outputs=[chat_response]
                )

                get_steps_btn.click(
                    fn=sync_get_step_by_step_guidance,
                    inputs=[step_session_id, step_concept, step_current],
                    outputs=[steps_output]
                )

                get_alt_btn.click(
                    fn=sync_get_alternative_explanations,
                    inputs=[alt_session_id, alt_concept, alt_types],
                    outputs=[alt_output]
                )

                end_session_btn.click(
                    fn=sync_end_tutoring_session,
                    inputs=[end_session_id, session_summary],
                    outputs=[session_end_output]
                )

            # Tab 5: Content Generation - Enhanced
            with gr.Tab("🎨 Content Generation", elem_id="content_generation_tab"):
                create_feature_section(
                    "Advanced Content Generation",
                    "Generate interactive exercises, scenarios, and gamified content automatically with AI assistance",
                    "🎨"
                )

                # Interactive Exercise Generation
                with gr.Accordion("🎯 Interactive Exercise Generation", open=True):
                    with gr.Row():
                        with gr.Column():
                            ex_concept = gr.Textbox(label="Concept", placeholder="e.g., Photosynthesis, Linear Algebra")
                            ex_type = gr.Dropdown(
                                choices=["problem_solving", "simulation", "case_study", "lab", "project"],
                                value="problem_solving",
                                label="Exercise Type"
                            )
                            ex_difficulty = gr.Slider(minimum=0.1, maximum=1.0, value=0.5, step=0.1, label="Difficulty Level")
                            ex_level = gr.Dropdown(
                                choices=["beginner", "intermediate", "advanced"],
                                value="intermediate",
                                label="Student Level"
                            )
                            gen_exercise_btn = gr.Button("Generate Interactive Exercise", variant="primary")

                        with gr.Column():
                            exercise_output = gr.JSON(label="Generated Exercise")

                # Scenario-Based Learning
                with gr.Accordion("🎭 Scenario-Based Learning", open=True):
                    with gr.Row():
                        with gr.Column():
                            scenario_concept = gr.Textbox(label="Concept", placeholder="e.g., Climate Change, Economics")
                            scenario_type = gr.Dropdown(
                                choices=["real_world", "historical", "futuristic", "problem_solving"],
                                value="real_world",
                                label="Scenario Type"
                            )
                            scenario_complexity = gr.Dropdown(
                                choices=["simple", "moderate", "complex"],
                                value="moderate",
                                label="Complexity Level"
                            )
                            gen_scenario_btn = gr.Button("Generate Scenario", variant="primary")

                        with gr.Column():
                            scenario_output = gr.JSON(label="Generated Scenario")

                # Gamified Content
                with gr.Accordion("🎮 Gamified Content Generation", open=True):
                    with gr.Row():
                        with gr.Column():
                            game_concept = gr.Textbox(label="Concept", placeholder="e.g., Fractions, Chemical Reactions")
                            game_type = gr.Dropdown(
                                choices=["quest", "puzzle", "simulation", "competition", "story"],
                                value="quest",
                                label="Game Type"
                            )
                            game_age = gr.Dropdown(
                                choices=["child", "teen", "adult"],
                                value="teen",
                                label="Target Age Group"
                            )
                            gen_game_btn = gr.Button("Generate Gamified Content", variant="primary")

                        with gr.Column():
                            game_output = gr.JSON(label="Generated Game Content")

                # Connect content generation buttons
                gen_exercise_btn.click(
                    fn=sync_generate_interactive_exercise,
                    inputs=[ex_concept, ex_type, ex_difficulty, ex_level],
                    outputs=[exercise_output]
                )

                gen_scenario_btn.click(
                    fn=sync_generate_scenario_based_learning,
                    inputs=[scenario_concept, scenario_type, scenario_complexity],
                    outputs=[scenario_output]
                )

                gen_game_btn.click(
                    fn=sync_generate_gamified_content,
                    inputs=[game_concept, game_type, game_age],
                    outputs=[game_output]
                )

            # Tab 6: Adaptive Learning - Enhanced
            with gr.Tab("🧠 Adaptive Learning", elem_id="adaptive_learning_tab"):
                create_feature_section(
                    "Adaptive Learning System",
                    "Experience personalized learning with real-time adaptation based on your performance and learning patterns",
                    "🧠"
                )

                with gr.Accordion("ℹ️ How It Works", open=False):
                    gr.Markdown("""
                    ### 🎯 Real-Time Adaptation
                    - **Performance Tracking**: Monitor accuracy, time spent, and engagement
                    - **Difficulty Adjustment**: Automatically adjust content difficulty based on performance
                    - **Learning Path Optimization**: Personalize learning sequences based on your progress
                    - **Mastery Detection**: Multi-indicator assessment of concept understanding

                    ### 📊 Analytics & Insights
                    - **Learning Patterns**: Detect your learning style and preferences
                    - **Progress Monitoring**: Track milestones and achievements
                    - **Predictive Recommendations**: Suggest next best concepts to learn

                    ### 🚀 Getting Started
                    1. Start an adaptive session with a concept you want to learn
                    2. Record your learning events (answers, time taken, etc.)
                    3. Get real-time recommendations for difficulty adjustments
                    4. View your progress and mastery assessments
                    """)

                # Adaptive Learning Session Management
                with gr.Accordion("📚 Learning Session Management", open=True):
                    with gr.Row():
                        with gr.Column():
                            session_student_id = gr.Textbox(label="Student ID", value=student_id)
                            session_concept_id = gr.Textbox(label="Concept ID", value="algebra_linear_equations")
                            session_difficulty = gr.Slider(minimum=0.1, maximum=1.0, value=0.5, step=0.1, label="Initial Difficulty")
                            start_session_btn = gr.Button("Start Adaptive Session", variant="primary")

                        with gr.Column():
                            session_output = gr.JSON(label="Session Status")
                            
                # Learning Path Optimization
                with gr.Accordion("🛤️ Learning Path Optimization", open=True):
                    with gr.Row():
                        with gr.Column():
                            opt_student_id = gr.Textbox(label="Student ID", value=student_id)
                            opt_concepts = gr.Textbox(
                                label="Target Concepts (comma-separated)",
                                value="algebra_basics,linear_equations,quadratic_equations"
                            )
                            opt_strategy = gr.Dropdown(
                                choices=["mastery_focused", "breadth_first", "depth_first", "adaptive", "remediation"],
                                value="adaptive",
                                label="Optimization Strategy"
                            )
                            opt_max_concepts = gr.Slider(minimum=3, maximum=15, value=8, step=1, label="Max Concepts")
                            optimize_path_btn = gr.Button("Optimize Learning Path", variant="primary")

                        with gr.Column():
                            optimization_output = gr.JSON(label="Optimized Learning Path")

                # Mastery Assessment
                with gr.Accordion("🎓 Mastery Assessment", open=True):
                    with gr.Row():
                        with gr.Column():
                            mastery_student_id = gr.Textbox(label="Student ID", value=student_id)
                            mastery_concept_id = gr.Textbox(label="Concept ID", value="algebra_linear_equations")
                            assess_mastery_btn = gr.Button("Assess Mastery", variant="primary")

                        with gr.Column():
                            mastery_output = gr.JSON(label="Mastery Assessment")

                # Learning Analytics
                with gr.Accordion("📊 Learning Analytics & Progress", open=True):
                    with gr.Row():
                        with gr.Column():
                            analytics_student_id = gr.Textbox(label="Student ID", value=student_id)
                            analytics_days = gr.Slider(minimum=7, maximum=90, value=30, step=7, label="Analysis Period (days)")
                            get_analytics_btn = gr.Button("Get Learning Analytics")
                            get_progress_btn = gr.Button("Get Progress Summary")

                        with gr.Column():
                            analytics_output = gr.JSON(label="Learning Analytics")
                            progress_output = gr.JSON(label="Progress Summary")

                # Connect all the buttons
                start_session_btn.click(
                    fn=sync_start_adaptive_session,
                    inputs=[session_student_id, session_concept_id, session_difficulty],
                    outputs=[session_output]
                )

                record_event_btn.click(
                    fn=sync_record_learning_event,
                    inputs=[session_student_id, session_concept_id, event_type, event_session_id, event_correct, event_time],
                    outputs=[event_output]
                )

                optimize_path_btn.click(
                    fn=sync_get_adaptive_learning_path,
                    inputs=[opt_student_id, opt_concepts, opt_strategy, opt_max_concepts],
                    outputs=[optimization_output]
                )

                assess_mastery_btn.click(
                    fn=lambda sid, cid: sync_get_adaptive_recommendations(sid, cid),
                    inputs=[mastery_student_id, mastery_concept_id],
                    outputs=[mastery_output]
                )

                get_analytics_btn.click(
                    fn=lambda sid, days: sync_get_progress_summary(sid, days),
                    inputs=[analytics_student_id, analytics_days],
                    outputs=[analytics_output]
                )

                get_progress_btn.click(
                    fn=lambda sid: sync_get_progress_summary(sid, 7),
                    inputs=[analytics_student_id],
                    outputs=[progress_output]
                )

                # Examples and Tips
                with gr.Accordion("💡 Examples & Tips", open=False):
                    gr.Markdown("""
                    ### 📝 Example Workflow

                    **1. Start a Session:**
                    - Student ID: `student_001`
                    - Concept: `algebra_linear_equations`
                    - Difficulty: `0.5` (medium)

                    **2. Record Events:**
                    - Answer submitted: correct=True, time=30s
                    - Hint used: correct=False, time=45s

                    **3. Get Recommendations:**
                    - System suggests difficulty adjustments
                    - Provides next concept suggestions

                    **4. Optimize Learning Path:**
                    - Target concepts: `algebra_basics,linear_equations,quadratic_equations`
                    - Strategy: `adaptive` (recommended)

                    ### 🎯 Optimization Strategies
                    - **Mastery Focused**: Deep understanding before moving on
                    - **Breadth First**: Cover many concepts quickly
                    - **Depth First**: Thorough exploration of fewer concepts
                    - **Adaptive**: System chooses best strategy for you
                    - **Remediation**: Focus on filling knowledge gaps

                    ### 📊 Understanding Analytics
                    - **Learning Patterns**: Identifies your learning style
                    - **Performance Trends**: Shows improvement over time
                    - **Mastery Levels**: Tracks concept understanding
                    - **Engagement Metrics**: Measures learning engagement
                    """)

            # Tab 7: Data Analytics - Enhanced
            with gr.Tab("📊 Analytics", elem_id="data_analytics_tab"):
                create_feature_section(
                    "Plagiarism Detection & Analytics",
                    "Advanced plagiarism detection with detailed similarity analysis and originality reporting",
                    "📊"
                )

                with gr.Row():
                    with gr.Column():
                        submission_input = gr.Textbox(
                            label="Student Submission",
                            lines=5,
                            value="The quadratic formula states that if ax² + bx + c = 0, then x = (-b ± √(b² - 4ac)) / 2a."
                        )
                        reference_input = gr.Textbox(
                            label="Reference Source",
                            lines=5,
                            value="According to the quadratic formula, for any equation in the form ax² + bx + c = 0, the solutions are x = (-b ± √(b² - 4ac)) / 2a."
                        )
                        plagiarism_btn = gr.Button("Check Originality")

                    with gr.Column():
                        with gr.Group():
                            gr.Markdown("### 🔍 Originality Report")
                            plagiarism_output = gr.JSON(label="", show_label=False, container=False)

                # Connect the button to the plagiarism check function
                plagiarism_btn.click(
                    fn=sync_check_plagiarism,
                    inputs=[submission_input, reference_input],
                    outputs=[plagiarism_output]
                )
            
            # Enhanced Footer Section - Gradio Soft theme compatible
            gr.Markdown("""
            <div style="background: var(--background-fill-secondary, #f7f7f7);
                       padding: 2rem;
                       margin-top: 2rem;
                       border-radius: var(--radius-xl, 12px);
                       border-top: 3px solid var(--color-accent, #ff6b6b);
                       border: 1px solid var(--border-color-primary, #e5e5e5);">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;">
                    <div>
                        <h3 style="color: var(--body-text-color, #374151); margin: 0 0 1rem 0; font-weight: 600;">🧠 About TutorX</h3>
                        <p style="color: var(--body-text-color-subdued, #6b7280); margin: 0; line-height: 1.6;">
                            TutorX is an AI-powered educational platform that provides adaptive learning,
                            interactive assessments, and personalized tutoring to enhance the learning experience.
                        </p>
                    </div>
                    <div>
                        <h3 style="color: var(--body-text-color, #374151); margin: 0 0 1rem 0; font-weight: 600;">🔗 Quick Links</h3>
                        <div style="color: var(--body-text-color-subdued, #6b7280);">
                            <p style="margin: 0.5rem 0;">📖 <a href="https://github.com/Meetpatel006/TutorX/blob/main/README.md" target="_blank" style="color: var(--color-accent, #ff6b6b); text-decoration: none;">Documentation</a></p>
                            <p style="margin: 0.5rem 0;">💻 <a href="https://github.com/Meetpatel006/TutorX" target="_blank" style="color: var(--color-accent, #ff6b6b); text-decoration: none;">GitHub Repository</a></p>
                            <p style="margin: 0.5rem 0;">🐛 <a href="https://github.com/Meetpatel006/TutorX/issues" target="_blank" style="color: var(--color-accent, #ff6b6b); text-decoration: none;">Report an Issue</a></p>
                        </div>
                    </div>
                    <div>
                        <h3 style="color: var(--body-text-color, #374151); margin: 0 0 1rem 0; font-weight: 600;">✨ Key Features</h3>
                        <div style="color: var(--body-text-color-subdued, #6b7280); font-size: 0.9rem;">
                            <p style="margin: 0.25rem 0;">🎯 Adaptive Learning Paths</p>
                            <p style="margin: 0.25rem 0;">🤖 AI-Powered Tutoring</p>
                            <p style="margin: 0.25rem 0;">📊 Real-time Analytics</p>
                            <p style="margin: 0.25rem 0;">🎮 Interactive Assessments</p>
                        </div>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color-primary, #e5e5e5);">
                    <p style="color: var(--body-text-color-subdued, #6b7280); margin: 0; font-size: 0.9rem;">
                        © 2025 TutorX Educational AI Platform - Empowering Learning Through Technology
                    </p>
                </div>
            </div>
            """)
        
        return demo

# Launch the interface
if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
