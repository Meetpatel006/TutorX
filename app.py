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

# Import MCP client to communicate with the MCP server
from client import client

# Server configuration
SERVER_URL = "http://localhost:8001"  # Default port is now 8001 to match main.py

# Utility functions


async def load_concept_graph(concept_id: str = None):
    """
    Load and visualize the concept graph for a given concept ID.
    If no concept_id is provided, returns the first available concept.
    
    Returns:
        tuple: (figure, concept_details, related_concepts) or (None, error_dict, [])
    """
    try:
        print(f"[DEBUG] Loading concept graph for concept_id: {concept_id}")
        
        # Get concept graph data from the server
        # First try direct API call, fall back to MCP tool if needed
        result = await client.get_concept_graph(concept_id, use_mcp=False)
        
        # If direct API call fails, try MCP tool
        if "error" in result:
            print(f"[DEBUG] Direct API call failed, trying MCP tool: {result}")
            result = await client.get_concept_graph(concept_id, use_mcp=True)
        print(f"[DEBUG] Server response: {result}")
        
        if not result or not isinstance(result, dict):
            error_msg = "Invalid server response"
            print(f"[ERROR] {error_msg}")
            return None, {"error": error_msg}, []
        
        if "error" in result:
            print(f"[ERROR] Server returned error: {result['error']}")
            return None, {"error": result["error"]}, []
        
        # Handle response when no specific concept_id was requested
        if "concepts" in result and not concept_id:
            if not result["concepts"]:
                error_msg = "No concepts available"
                print(f"[ERROR] {error_msg}")
                return None, {"error": error_msg}, []
            concept = result["concepts"][0]
            print(f"[DEBUG] Using first concept from list: {concept.get('id')}")
        else:
            concept = result
            print(f"[DEBUG] Using direct concept: {concept.get('id')}")
        
        # Validate the concept structure
        if not isinstance(concept, dict) or not concept.get('id'):
            error_msg = "Invalid concept data structure"
            print(f"[ERROR] {error_msg}: {concept}")
            return None, {"error": error_msg}, []
        
        # Create a simple visualization using matplotlib
        import matplotlib.pyplot as plt
        import networkx as nx
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add the main concept node
        G.add_node(concept["id"], label=concept["name"], type="concept")
        
        # Add related concepts
        related_concepts = []
        if "related" in concept:
            for rel_id in concept["related"]:
                rel_result = await client.get_concept_graph(rel_id)
                if "error" not in rel_result:
                    G.add_node(rel_id, label=rel_result["name"], type="related")
                    G.add_edge(concept["id"], rel_id, relationship="related_to")
                    related_concepts.append([rel_id, rel_result.get("name", ""), rel_result.get("description", "")])
        
        # Add prerequisites if any
        if "prerequisites" in concept:
            for prereq_id in concept["prerequisites"]:
                prereq_result = await client.get_concept_graph(prereq_id)
                if "error" not in prereq_result:
                    G.add_node(prereq_id, label=prereq_result["name"], type="prerequisite")
                    G.add_edge(prereq_id, concept["id"], relationship="prerequisite_for")
        
        # Draw the graph
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)
        
        # Draw nodes with different colors based on type
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
        
        # Add labels
        labels = {node: G.nodes[node].get("label", node) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold")
        
        # Add edge labels
        edge_labels = {(u, v): d["relationship"] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        
        plt.title(f"Concept Graph: {concept.get('name', concept_id)}")
        plt.axis("off")
        
        # Return the figure and concept details
        concept_details = {
            "id": concept.get("id", ""),
            "name": concept.get("name", ""),
            "description": concept.get("description", ""),
            "related_concepts_count": len(concept.get("related", [])),
            "prerequisites_count": len(concept.get("prerequisites", []))
        }
        
        return plt.gcf(), concept_details, related_concepts
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, {"error": f"Failed to load concept graph: {str(e)}"}, []

async def api_request(endpoint, method="GET", params=None, json_data=None):
    """Make an API request to the server"""
    url = f"{SERVER_URL}/api/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error = await response.text()
                        return {"error": f"API error: {response.status} - {error}"}
            elif method.upper() == "POST":
                async with session.post(url, json=json_data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error = await response.text()
                        return {"error": f"API error: {response.status} - {error}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

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
                        concept_id = gr.Dropdown(
                            label="Select a Concept",
                            choices=["python", "functions", "oop", "data_structures"],
                            value="python",
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
                    inputs=[concept_id],
                    outputs=[graph_output, concept_details, related_concepts]
                )
                
                # Load default concept on tab click
                concept_graph_tab.load(
                    fn=load_concept_graph,
                    inputs=[concept_id],
                    outputs=[graph_output, concept_details, related_concepts]
                )
            
            gr.Markdown("## Assessment Generation")
            with gr.Row():
                with gr.Column():
                    concepts_input = gr.CheckboxGroup(
                        choices=["math_algebra_basics", "math_algebra_linear_equations", "math_algebra_quadratic_equations"],
                        label="Select Concepts",
                        value=["math_algebra_linear_equations"]
                    )
                    diff_input = gr.Slider(minimum=1, maximum=5, value=2, step=1, label="Difficulty")
                    gen_quiz_btn = gr.Button("Generate Quiz")
                
                with gr.Column():
                    quiz_output = gr.JSON(label="Generated Quiz")
            
            async def on_generate_quiz(concepts, difficulty):
                # Convert the request to match the expected format
                request_data = {
                    "concept_ids": concepts if isinstance(concepts, list) else [concepts],
                    "difficulty": int(difficulty)
                }
                result = await api_request(
                    "generate_quiz", 
                    "POST", 
                    json_data=request_data
                )
                return result
                
            gen_quiz_btn.click(
                fn=on_generate_quiz,
                inputs=[concepts_input, diff_input],
                outputs=[quiz_output]
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
                return await client.generate_lesson(topic, grade, duration)
                
            gen_lesson_btn.click(
                fn=generate_lesson_async,
                inputs=[topic_input, grade_input, duration_input],
                outputs=[lesson_output]
            )
            
            gr.Markdown("## Curriculum Standards")
            
            with gr.Row():
                with gr.Column():
                    country_input = gr.Dropdown(
                        choices=["US", "UK"],
                        label="Country",
                        value="US"
                    )
                    standards_btn = gr.Button("Get Standards")
                
                with gr.Column():
                    standards_output = gr.JSON(label="Curriculum Standards")
            
            async def get_standards_async(country):
                try:
                    # Convert display text to lowercase for the API
                    country_code = country.lower()
                    response = await client.get_curriculum_standards(country_code)
                    
                    # Format the response for better display
                    if "standards" in response:
                        formatted = {
                            "country": response["standards"]["name"],
                            "subjects": {},
                            "website": response["standards"].get("website", "")
                        }
                        
                        # Format subjects and domains
                        for subj_key, subj_info in response["standards"]["subjects"].items():
                            formatted["subjects"][subj_key] = {
                                "description": subj_info["description"],
                                "domains": subj_info["domains"]
                            }
                        
                        # Add grade levels or key stages if available
                        if "grade_levels" in response["standards"]:
                            formatted["grade_levels"] = response["standards"]["grade_levels"]
                        elif "key_stages" in response["standards"]:
                            formatted["key_stages"] = response["standards"]["key_stages"]
                            
                        return formatted
                    return response
                except Exception as e:
                    return {"error": f"Failed to fetch standards: {str(e)}"}
                
            standards_btn.click(
                fn=get_standards_async,
                inputs=[country_input],
                outputs=[standards_output]
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
                return await client.text_interaction(text, "student_12345")
                
            text_btn.click(
                fn=text_interaction_async,
                inputs=[text_input],
                outputs=[text_output]
            )
            
            gr.Markdown("## PDF OCR and Summarization (Coming Soon)")
            with gr.Row():
                with gr.Column():
                    pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
                    ocr_btn = gr.Button("Extract Text")
                
                with gr.Column():
                    summary_output = gr.JSON(label="Summary")
            
            async def pdf_ocr_async(pdf_file):
                if not pdf_file:
                    return {"error": "No PDF file provided", "success": False}
                try:
                    # Get the file path from the Gradio file object
                    if isinstance(pdf_file, dict):
                        file_path = pdf_file.get("path", "")
                    else:
                        file_path = pdf_file
                    
                    if not file_path or not os.path.exists(file_path):
                        return {"error": "File not found", "success": False}
                        
                    return await client.pdf_ocr(file_path)
                except Exception as e:
                    return {"error": f"Error processing PDF: {str(e)}", "success": False}
                
            ocr_btn.click(
                fn=pdf_ocr_async,
                inputs=[pdf_input],
                outputs=[summary_output]
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
                return await client.check_submission_originality(submission, [reference])
                
            plagiarism_btn.click(
                fn=check_plagiarism_async,
                inputs=[submission_input, reference_input],
                outputs=[plagiarism_output]
            )

# Launch the interface
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
