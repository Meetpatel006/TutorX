"""
Gradio web interface for the TutorX MCP Server with SSE support
"""

import gradio as gr
import numpy as np
import json
import base64
from io import BytesIO
from PIL import Image
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
def image_to_base64(img):
    """Convert a PIL image or numpy array to base64 string"""
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

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
            gr.Markdown("## Adaptive Learning Engine")
            
            with gr.Row():
                with gr.Column():
                    concept_id_input = gr.Dropdown(
                        choices=["math_algebra_basics", "math_algebra_linear_equations", "math_algebra_quadratic_equations"],
                        label="Select Concept",
                        value="math_algebra_linear_equations"
                    )
                    assess_btn = gr.Button("Assess Skill")
                
                with gr.Column():
                    assessment_output = gr.JSON(label="Skill Assessment")
            async def on_assess_click(concept_id):
                result = await api_request("assess_skill", "GET", {"student_id": "student_12345", "concept_id": concept_id})
                return result
                
            assess_btn.click(
                fn=on_assess_click,
                inputs=[concept_id_input],
                outputs=[assessment_output]
            )
            
            gr.Markdown("## Concept Graph")
            concept_graph_btn = gr.Button("Show Concept Graph")
            concept_graph_output = gr.JSON(label="Concept Graph")
            
            async def on_concept_graph_click():
                result = await api_request("concept_graph")
                return result
                
            concept_graph_btn.click(
                fn=on_concept_graph_click,
                inputs=[],
                outputs=[concept_graph_output]
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
                result = await api_request(
                    "generate_quiz", 
                    "POST", 
                    json_data={"concept_ids": concepts, "difficulty": difficulty}
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
            gen_lesson_btn.click(
                fn=lambda x, y, z: asyncio.run(client.generate_lesson(x, y, z)),
                inputs=[topic_input, grade_input, duration_input],
                outputs=[lesson_output]
            )
            
            gr.Markdown("## Curriculum Standards")
            
            with gr.Row():
                with gr.Column():
                    country_input = gr.Dropdown(
                        choices=["us", "uk"],
                        label="Country",
                        value="us"
                    )
                    standards_btn = gr.Button("Get Standards")
                
                with gr.Column():
                    standards_output = gr.JSON(label="Curriculum Standards")
            
            standards_btn.click(
                fn=lambda x: asyncio.run(client.get_curriculum_standards(x)),
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
            text_btn.click(
                fn=lambda x: asyncio.run(client.text_interaction(x, "student_12345")),
                inputs=[text_input],
                outputs=[text_output]
            )
            
            gr.Markdown("## Handwriting Recognition")
            
            with gr.Row():
                with gr.Column():
                    drawing_input = gr.Sketchpad(label="Draw an Equation")
                    drawing_btn = gr.Button("Recognize")
                
                with gr.Column():
                    drawing_output = gr.JSON(label="Recognition Results")
            
            drawing_btn.click(
                fn=lambda x: asyncio.run(client.handwriting_recognition(image_to_base64(x), "student_12345")),
                inputs=[drawing_input],
                outputs=[drawing_output]
            )
        
        # Tab 4: Analytics
        with gr.Tab("Analytics"):
            gr.Markdown("## Student Performance")
            analytics_btn = gr.Button("Generate Analytics Report")
            timeframe = gr.Slider(minimum=7, maximum=90, value=30, step=1, label="Timeframe (days)")
            analytics_output = gr.JSON(label="Performance Analytics")
            analytics_btn.click(
                fn=lambda x: asyncio.run(client.get_student_analytics("student_12345", x)),
                inputs=[timeframe],
                outputs=[analytics_output]
            )
            
            gr.Markdown("## Error Pattern Analysis")
            
            error_concept = gr.Dropdown(
                choices=["math_algebra_basics", "math_algebra_linear_equations", "math_algebra_quadratic_equations"],
                label="Select Concept for Error Analysis",
                value="math_algebra_linear_equations"
            )
            error_btn = gr.Button("Analyze Errors")
            error_output = gr.JSON(label="Error Pattern Analysis")
            
            error_btn.click(
                fn=lambda x: asyncio.run(client.analyze_error_patterns("student_12345", x)),
                inputs=[error_concept],
                outputs=[error_output]
            )
            
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
            
            plagiarism_btn.click(
                fn=lambda x, y: asyncio.run(client.check_submission_originality(x, [y])),
                inputs=[submission_input, reference_input],
                outputs=[plagiarism_output]
            )

# Launch the interface
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
