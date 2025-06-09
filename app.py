"""
Gradio web interface for the TutorX MCP Server with SSE support
"""

import os
import json
import asyncio
import gradio as gr
from typing import Optional, Dict, Any, List, Union, Tuple, Callable
import requests
import tempfile
import base64
import re
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Set matplotlib to use 'Agg' backend to avoid GUI issues in Gradio
matplotlib.use('Agg')

# Import MCP client components
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.types import TextContent, CallToolResult

# Server configuration
SERVER_URL = "https://tutorx-mcp.onrender.com/sse"  # Ensure this is the SSE endpoint

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

def start_ping_task():
    """Start the ping task when the Gradio app launches"""
    global ping_task
    try:
        if ping_task is None:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                ping_task = loop.create_task(start_periodic_ping())
                print("Started periodic ping task")
            else:
                print("Event loop is not running, will start ping task later")
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
    print(f"[DEBUG] Loading concept graph for concept_id: {concept_id}")
    
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                
                # Call the concept graph tool
                result = await session.call_tool(
                    "get_concept_graph_tool", 
                    {"concept_id": concept_id} if concept_id else {}
                )
                print(f"[DEBUG] Raw tool response type: {type(result)}")
                
                # Extract content if it's a TextContent object
                if hasattr(result, 'content') and isinstance(result.content, list):
                    for item in result.content:
                        if hasattr(item, 'text') and item.text:
                            try:
                                result = json.loads(item.text)
                                print("[DEBUG] Successfully parsed JSON from TextContent")
                                break
                            except json.JSONDecodeError as e:
                                print(f"[ERROR] Failed to parse JSON from TextContent: {e}")
                
                # If result is a string, try to parse it as JSON
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Failed to parse result as JSON: {e}")
                        return None, {"error": f"Failed to parse concept graph data: {str(e)}"}, []
                
                # Debug print for the raw backend response
                print(f"[DEBUG] Raw backend response: {result}")
                
                # Handle backend error response
                if isinstance(result, dict) and "error" in result:
                    error_msg = f"Backend error: {result['error']}"
                    print(f"[ERROR] {error_msg}")
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
                                    print(f"[ERROR] {error_msg}")
                                    return None, {"error": error_msg}, []
                        else:
                            error_msg = "No concepts found in the concept graph"
                            print(f"[ERROR] {error_msg}")
                            return None, {"error": error_msg}, []
                
                # If we still don't have a valid concept
                if not concept or not isinstance(concept, dict):
                    error_msg = "Could not extract valid concept data from response"
                    print(f"[ERROR] {error_msg}")
                    return None, {"error": error_msg}, []
                
                # Ensure required fields exist with defaults
                concept.setdefault('related_concepts', [])
                concept.setdefault('prerequisites', [])
                
                print(f"[DEBUG] Final concept data: {concept}")
                
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
        import traceback
        error_msg = f"Error in load_concept_graph: {str(e)}\n\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
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

# Create Gradio interface
def create_gradio_interface():
    # Set a default student ID for the demo
    student_id = "student_12345"
    
    with gr.Blocks(title="TutorX Educational AI", theme=gr.themes.Soft()) as demo:
        # Start the ping task when the app loads
        demo.load(
            fn=start_ping_task,
            inputs=None,
            outputs=None,
            queue=False
        )
        
        # Interface content
        gr.Markdown("# 📚 TutorX Educational AI Platform")
        gr.Markdown("""
        An adaptive, multi-modal, and collaborative AI tutoring platform built with MCP.
        """)
        
        with gr.Tabs() as tabs:
            # Tab 1: Core Features
            with gr.Tab("Core Features"):
                with gr.Blocks() as concept_graph_tab:
                    gr.Markdown("## Concept Graph Visualization")
                    gr.Markdown("Explore relationships between educational concepts through an interactive graph visualization.")
                    
                    with gr.Row():
                        # Left panel for controls and details
                        with gr.Column(scale=3):
                            with gr.Row():
                                concept_input = gr.Textbox(
                                    label="Enter Concept",
                                    placeholder="e.g., machine_learning, calculus, quantum_physics",
                                    value="machine_learning",
                                    scale=4
                                )
                            load_btn = gr.Button("Load Graph", variant="primary", scale=1)
                        
                        # Concept details
                        with gr.Accordion("Concept Details", open=True):
                            concept_details = gr.JSON(
                                label=None,
                                show_label=False
                            )
                        
                        # Related concepts and prerequisites
                        with gr.Accordion("Related Concepts & Prerequisites", open=True):
                            related_concepts = gr.Dataframe(
                                headers=["Type", "Name", "Description"],
                                datatype=["str", "str", "str"],
                                interactive=False,
                                wrap=True,
                                # max_height=300,  # Fixed height with scroll in Gradio 5.x
                                # overflow_row_behaviour="paginate"
                            )
                    
                    # Graph visualization
                    with gr.Column(scale=7):
                        graph_plot = gr.Plot(
                            label="Concept Graph",
                            show_label=True,
                            container=True
                        )
                
                # Event handlers
                load_btn.click(
                    fn=sync_load_concept_graph,
                    inputs=[concept_input],
                    outputs=[graph_plot, concept_details, related_concepts]
                )
                
                # Load initial graph
                demo.load(
                    fn=lambda: sync_load_concept_graph("machine_learning"),
                    outputs=[graph_plot, concept_details, related_concepts]
                )
                # Help text and examples
                with gr.Row():
                    gr.Markdown("""
                    **Examples to try:**
                    - `machine_learning`
                    - `neural_networks`
                    - `calculus`
                    - `quantum_physics`
                    """)
                
                # Error display (leave in UI, but not wired up)
                error_output = gr.Textbox(
                    label="Error Messages",
                    visible=False,
                    interactive=False
                )
            
            gr.Markdown("## Assessment Generation")
            with gr.Row():
                with gr.Column():
                    concept_input = gr.Textbox(
                        label="Enter Concept",
                        placeholder="e.g., Linear Equations, Photosynthesis, World War II",
                        lines=2
                    )
                    with gr.Row():
                        diff_input = gr.Slider(
                            minimum=1, 
                            maximum=5, 
                            value=2, 
                            step=1, 
                            label="Difficulty Level",
                            interactive=True
                        )
                        gen_quiz_btn = gr.Button("Generate Quiz", variant="primary")
                
                with gr.Column():
                    quiz_output = gr.JSON(label="Generated Quiz")
            
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
                            if hasattr(response, 'content') and isinstance(response.content, list):
                                for item in response.content:
                                    if hasattr(item, 'text') and item.text:
                                        try:
                                            quiz_data = json.loads(item.text)
                                            return quiz_data
                                        except Exception:
                                            return {"raw_pretty": json.dumps(item.text, indent=2)}
                            if isinstance(response, dict):
                                return response
                            if isinstance(response, str):
                                try:
                                    return json.loads(response)
                                except Exception:
                                    return {"raw_pretty": json.dumps(response, indent=2)}
                            return {"raw_pretty": json.dumps(str(response), indent=2)}
                except Exception as e:
                    import traceback
                    return {
                        "error": f"Error generating quiz: {str(e)}\n\n{traceback.format_exc()}"
                    }
                
            gen_quiz_btn.click(
                fn=on_generate_quiz,
                inputs=[concept_input, diff_input],
                outputs=[quiz_output],
                api_name="generate_quiz"
            )
        
        # Tab 2: Advanced Features
        with gr.Tab("Advanced Features"):
            gr.Markdown("## Lesson Generation")
            
            with gr.Row():
                with gr.Column():
                    topic_input = gr.Textbox(label="Lesson Topic", value="Solving Quadratic Equations")
                    grade_input = gr.Slider(minimum=1, maximum=12, value=9, step=1, label="Grade Level")
                    duration_input = gr.Slider(minimum=15, maximum=90, value=45, step=5, label="Duration (minutes)")
                    gen_lesson_btn = gr.Button("Generate Lesson Plan")
                
                with gr.Column():
                    lesson_output = gr.JSON(label="Lesson Plan")
            async def generate_lesson_async(topic, grade, duration):
                async with sse_client(SERVER_URL) as (sse, write):
                    async with ClientSession(sse, write) as session:
                        await session.initialize()
                        response = await session.call_tool("generate_lesson_tool", {"topic": topic, "grade_level": grade, "duration_minutes": duration})
                        if hasattr(response, 'content') and isinstance(response.content, list):
                            for item in response.content:
                                if hasattr(item, 'text') and item.text:
                                    try:
                                        lesson_data = json.loads(item.text)
                                        return lesson_data
                                    except Exception:
                                        return {"raw_pretty": json.dumps(item.text, indent=2)}
                        if isinstance(response, dict):
                            return response
                        if isinstance(response, str):
                            try:
                                return json.loads(response)
                            except Exception:
                                return {"raw_pretty": json.dumps(response, indent=2)}
                        return {"raw_pretty": json.dumps(str(response), indent=2)}
                
            gen_lesson_btn.click(
                fn=generate_lesson_async,
                inputs=[topic_input, grade_input, duration_input],
                outputs=[lesson_output]
            )
            
            gr.Markdown("## Learning Path Generation")
            with gr.Row():
                with gr.Column():
                    lp_student_id = gr.Textbox(label="Student ID", value=student_id)
                    lp_concept_ids = gr.Textbox(label="Concept IDs (comma-separated)", placeholder="e.g., python,functions,oop")
                    lp_student_level = gr.Dropdown(choices=["beginner", "intermediate", "advanced"], value="beginner", label="Student Level")
                    lp_btn = gr.Button("Generate Learning Path")
                with gr.Column():
                    lp_output = gr.JSON(label="Learning Path")
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
                            if hasattr(result, 'content') and isinstance(result.content, list):
                                for item in result.content:
                                    if hasattr(item, 'text') and item.text:
                                        try:
                                            lp_data = json.loads(item.text)
                                            return lp_data
                                        except Exception:
                                            return {"raw_pretty": json.dumps(item.text, indent=2)}
                            if isinstance(result, dict):
                                return result
                            if isinstance(result, str):
                                try:
                                    return json.loads(result)
                                except Exception:
                                    return {"raw_pretty": json.dumps(result, indent=2)}
                            return {"raw_pretty": json.dumps(str(result), indent=2)}
                except Exception as e:
                    return {"error": str(e)}
            lp_btn.click(
                fn=on_generate_learning_path,
                inputs=[lp_student_id, lp_concept_ids, lp_student_level],
                outputs=[lp_output]
            )
        
        # Tab 3: Multi-Modal Interaction
        with gr.Tab("Multi-Modal Interaction"):
            gr.Markdown("## Text Interaction")
            
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(label="Ask a Question", value="How do I solve a quadratic equation?")
                    text_btn = gr.Button("Submit")
                
                with gr.Column():
                    text_output = gr.JSON(label="Response")
            async def text_interaction_async(text):
                async with sse_client(SERVER_URL) as (sse, write):
                    async with ClientSession(sse, write) as session:
                        await session.initialize()
                        response = await session.call_tool("text_interaction", {"query": text, "student_id": student_id})
                        if hasattr(response, 'content') and isinstance(response.content, list):
                            for item in response.content:
                                if hasattr(item, 'text') and item.text:
                                    try:
                                        data = json.loads(item.text)
                                        return data
                                    except Exception:
                                        return {"raw_pretty": json.dumps(item.text, indent=2)}
                        if isinstance(response, dict):
                            return response
                        if isinstance(response, str):
                            try:
                                return json.loads(response)
                            except Exception:
                                return {"raw_pretty": json.dumps(response, indent=2)}
                        return {"raw_pretty": json.dumps(str(response), indent=2)}
                
            text_btn.click(
                fn=text_interaction_async,
                inputs=[text_input],
                outputs=[text_output]
            )
            
            # Document OCR (PDF, images, etc.)
            gr.Markdown("## Document OCR & LLM Analysis")
            with gr.Row():
                with gr.Column():
                    doc_input = gr.File(label="Upload PDF or Document", file_types=[".pdf", ".jpg", ".jpeg", ".png"])
                    doc_ocr_btn = gr.Button("Extract Text & Analyze")
                with gr.Column():
                    doc_output = gr.JSON(label="Document OCR & LLM Analysis")
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
                            if hasattr(response, 'content') and isinstance(response.content, list):
                                for item in response.content:
                                    if hasattr(item, 'text') and item.text:
                                        try:
                                            data = json.loads(item.text)
                                            return data
                                        except Exception:
                                            return {"raw_pretty": json.dumps(item.text, indent=2)}
                            if isinstance(response, dict):
                                return response
                            if isinstance(response, str):
                                try:
                                    return json.loads(response)
                                except Exception:
                                    return {"raw_pretty": json.dumps(response, indent=2)}
                            return {"raw_pretty": json.dumps(str(response), indent=2)}
                except Exception as e:
                    return {"error": f"Error processing document: {str(e)}", "success": False}
            doc_ocr_btn.click(
                fn=document_ocr_async,
                inputs=[doc_input],
                outputs=[doc_output]
            )
        
        # Tab 4: Analytics
        with gr.Tab("Analytics"):
            gr.Markdown("## Plagiarism Detection")
            
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
                    plagiarism_output = gr.JSON(label="Originality Report")
            
            async def check_plagiarism_async(submission, reference):
                async with sse_client(SERVER_URL) as (sse, write):
                    async with ClientSession(sse, write) as session:
                        await session.initialize()
                        response = await session.call_tool("check_submission_originality", {"submission": submission, "reference_sources": [reference] if isinstance(reference, str) else reference})
                        if hasattr(response, 'content') and isinstance(response.content, list):
                            for item in response.content:
                                if hasattr(item, 'text') and item.text:
                                    try:
                                        data = json.loads(item.text)
                                        return data
                                    except Exception:
                                        return {"raw_pretty": json.dumps(item.text, indent=2)}
                        if isinstance(response, dict):
                            return response
                        if isinstance(response, str):
                            try:
                                return json.loads(response)
                            except Exception:
                                return {"raw_pretty": json.dumps(response, indent=2)}
                        return {"raw_pretty": json.dumps(str(response), indent=2)}
                
            plagiarism_btn.click(
                fn=check_plagiarism_async,
                inputs=[submission_input, reference_input],
                outputs=[plagiarism_output]
            )
        
        return demo

# Launch the interface
if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
