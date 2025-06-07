"""
Gradio web interface for the TutorX MCP Server
"""

import gradio as gr
import numpy as np
import json
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime

# Import MCP client to communicate with the MCP server
from client import client

# Utility functions
def image_to_base64(img):
    """Convert a PIL image or numpy array to base64 string"""
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def format_json(data):
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

# Create Gradio interface
with gr.Blocks(title="TutorX Educational AI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📚 TutorX Educational AI Platform")
    gr.Markdown("""
    An adaptive, multi-modal, and collaborative AI tutoring platform built with MCP.
    
    This interface demonstrates the functionality of the TutorX MCP server.
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
              assess_btn.click(
                fn=lambda concept: client.assess_skill(student_id, concept),
                inputs=[concept_id_input],
                outputs=[assessment_output]
            )
            
            gr.Markdown("## Concept Graph")
            concept_graph_btn = gr.Button("Show Concept Graph")
            concept_graph_output = gr.JSON(label="Concept Graph")
            
            concept_graph_btn.click(
                fn=lambda: client.get_concept_graph(),
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
            
            gen_quiz_btn.click(
                fn=lambda concepts, diff: client.generate_quiz(concepts, diff),
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
                fn=lambda topic, grade, duration: client.generate_lesson(topic, grade, duration),
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
                fn=lambda country: client.get_curriculum_standards(country),
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
                fn=lambda query: client.text_interaction(query, student_id),
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
            
            # Convert drawing to base64 then process
            drawing_btn.click(
                fn=lambda img: client.handwriting_recognition(image_to_base64(img), student_id),
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
                fn=lambda days: client.get_student_analytics(student_id, days),
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
                fn=lambda concept: client.analyze_error_patterns(student_id, concept),
                inputs=[error_concept],
                outputs=[error_output]
            )
        
        # Tab 5: Assessment Tools
        with gr.Tab("Assessment Tools"):
            gr.Markdown("## Create Assessment")
            
            with gr.Row():
                with gr.Column():
                    assess_concepts = gr.CheckboxGroup(
                        choices=["math_algebra_basics", "math_algebra_linear_equations", "math_algebra_quadratic_equations"],
                        label="Select Concepts",
                        value=["math_algebra_linear_equations"]
                    )
                    assess_questions = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="Number of Questions")
                    assess_diff = gr.Slider(minimum=1, maximum=5, value=3, step=1, label="Difficulty")
                    create_assess_btn = gr.Button("Create Assessment")
                
                with gr.Column():
                    assessment_output = gr.JSON(label="Generated Assessment")
              create_assess_btn.click(
                fn=lambda concepts, num, diff: client.create_assessment(concepts, num, diff),
                inputs=[assess_concepts, assess_questions, assess_diff],
                outputs=[assessment_output]
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
                fn=lambda sub, ref: client.check_submission_originality(sub, [ref]),
                inputs=[submission_input, reference_input],
                outputs=[plagiarism_output]
            )

# Launch the app
if __name__ == "__main__":
    demo.launch()
