"""
Gradio web interface for the TutorX MCP Server with SSE support
"""

import os
import gradio as gr
import numpy as np
import json

from datetime import datetime
import asyncio
import aiohttp
import sseclient
import requests

# Import MCP SSE client context managers
from mcp import ClientSession
from mcp.client.sse import sse_client

# Server configuration
SERVER_URL = "http://localhost:8000/sse"  # Ensure this is the SSE endpoint

# Utility functions


async def load_concept_graph(concept_id: str = None):
    """
    Load and visualize the concept graph for a given concept ID.
    If no concept_id is provided, returns the first available concept.
    Uses call_resource for concept graph retrieval (not a tool).
    
    Returns:
        tuple: (figure, concept_details, related_concepts) or (None, error_dict, [])
    """
    try:
        print(f"[DEBUG] Loading concept graph for concept_id: {concept_id}")
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("get_concept_graph_tool", {"concept_id": concept_id} if concept_id else {})
                print(f"[DEBUG] Server response: {result}")
                if not result or not isinstance(result, dict):
                    error_msg = "Invalid server response"
                    print(f"[ERROR] {error_msg}")
                    return None, {"error": error_msg}, []
                if "error" in result:
                    print(f"[ERROR] Server returned error: {result['error']}")
                    return None, {"error": result["error"]}, []
                if "concepts" in result and not concept_id:
                    if not result["concepts"]:
                        error_msg = "No concepts available"
                        print(f"[ERROR] {error_msg}")
                        return None, {"error": error_msg}, []
                    concept = result["concepts"][0]
                    print(f"[DEBUG] Using first concept from list: {concept.get('id')}")
                else:
                    concept = result.get("concept", result)
                    print(f"[DEBUG] Using direct concept: {concept.get('id')}")
                if not isinstance(concept, dict) or not concept.get('id'):
                    error_msg = "Invalid concept data structure"
                    print(f"[ERROR] {error_msg}: {concept}")
                    return None, {"error": error_msg}, []
                import matplotlib.pyplot as plt
                import networkx as nx
                G = nx.DiGraph()
                G.add_node(concept["id"], label=concept["name"], type="concept")
                related_concepts = []
                if "related" in concept:
                    for rel_id in concept["related"]:
                        rel_result = await session.call_tool("get_concept_graph_tool", {"concept_id": rel_id})
                        if "error" not in rel_result:
                            rel_concept = rel_result.get("concept", {})
                            G.add_node(rel_id, label=rel_concept.get("name", rel_id), type="related")
                            G.add_edge(concept["id"], rel_id, relationship="related_to")
                            related_concepts.append([rel_id, rel_concept.get("name", ""), rel_concept.get("description", "")])
                if "prerequisites" in concept:
                    for prereq_id in concept["prerequisites"]:
                        prereq_result = await session.call_tool("get_concept_graph_tool", {"concept_id": prereq_id})
                        if "error" not in prereq_result:
                            prereq_concept = prereq_result.get("concept", {})
                            G.add_node(prereq_id, label=prereq_concept.get("name", prereq_id), type="prerequisite")
                            G.add_edge(prereq_id, concept["id"], relationship="prerequisite_for")
                plt.figure(figsize=(10, 8))
                pos = nx.spring_layout(G)
                node_colors = []
                for node in G.nodes():
                    if G.nodes[node].get("type") == "concept":
                        node_colors.append("lightblue")
                    elif G.nodes[node].get("type") == "prerequisite":
                        node_colors.append("lightcoral")
                    else:
                        node_colors.append("lightgreen")
                nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=node_colors, alpha=0.8)
                nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
                labels = {node: G.nodes[node].get("label", node) for node in G.nodes()}
                nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold")
                edge_labels = {(u, v): d["relationship"] for u, v, d in G.edges(data=True)}
                nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
                plt.title(f"Concept Graph: {concept.get('name', concept_id)}")
                plt.axis("off")
                concept_details = concept
                return plt.gcf(), concept_details, related_concepts
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, {"error": f"Failed to load concept graph: {str(e)}"}, []
        
# Create Gradio interface
with gr.Blocks(title="TutorX Educational AI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📚 TutorX Educational AI Platform")
    gr.Markdown("""
    An adaptive, multi-modal, and collaborative AI tutoring platform built with MCP.
    
    This interface demonstrates the functionality of the TutorX MCP server using SSE connections.
    """)
    
    # Set a default student ID for the demo
    student_id = "student_12345"
    
    with gr.Tabs() as tabs:
        # Tab 1: Core Features
        with gr.Tab("Core Features"):
            with gr.Blocks() as concept_graph_tab:
                gr.Markdown("## Concept Graph Visualization")
                with gr.Row():
                    with gr.Column(scale=3):
                        # Change from dropdown to textbox for concept input
                        concept_input_box = gr.Textbox(
                            label="Enter Concept Name",
                            placeholder="e.g., python, functions, oop, data_structures",
                            lines=1,
                            interactive=True
                        )
                        load_concept_btn = gr.Button("Load Concept Graph", variant="primary")
                        
                        # Concept details
                        concept_details = gr.JSON(label="Concept Details")
                        
                        # Related concepts
                        related_concepts = gr.Dataframe(
                            headers=["ID", "Name", "Description"],
                            datatype=["str", "str", "str"],
                            label="Related Concepts"
                        )
                    
                    # Graph visualization
                    with gr.Column(scale=7):
                        graph_output = gr.Plot(label="Concept Graph")
                
                # Button click handler
                load_concept_btn.click(
                    fn=load_concept_graph,
                    inputs=[concept_input_box],
                    outputs=[graph_output, concept_details, related_concepts]
                )
                
                # Load default concept on tab click
                concept_graph_tab.load(
                    fn=load_concept_graph,
                    inputs=[concept_input_box],
                    outputs=[graph_output, concept_details, related_concepts]
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
                            return response
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
                        return response
                
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
                            return result
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
                        return response
                
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
                    
                    # Upload file to storage API
                    upload_result = await upload_file_to_storage(file_path)
                    if not upload_result.get("success"):
                        return upload_result
                    
                    # Get the storage URL from the upload response
                    storage_url = upload_result.get("storage_url")
                    if not storage_url:
                        return {"error": "No storage URL returned from upload", "success": False}
                    
                    # Use the storage URL for OCR processing
                    async with sse_client(SERVER_URL) as (sse, write):
                        async with ClientSession(sse, write) as session:
                            await session.initialize()
                            response = await session.call_tool("mistral_document_ocr", {"document_url": storage_url})
                            return response
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
                        return response
                
            plagiarism_btn.click(
                fn=check_plagiarism_async,
                inputs=[submission_input, reference_input],
                outputs=[plagiarism_output]
            )

# Launch the interface
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
