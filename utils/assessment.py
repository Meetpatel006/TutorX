"""
Assessment and analytics utilities for the TutorX MCP server.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import json

def generate_question(concept_id: str, difficulty: int) -> Dict[str, Any]:
    """
    Generate a question for a specific concept at the given difficulty level
    
    Args:
        concept_id: The concept identifier
        difficulty: Difficulty level from 1-5
        
    Returns:
        Question object
    """
    # In a real implementation, this would use templates and context to generate appropriate questions
    # Here we'll simulate with some hardcoded examples
    
    question_templates = {
        "math_algebra_basics": [
            {
                "text": "Simplify: {a}x + {b}x",
                "variables": {"a": (1, 10), "b": (1, 10)},
                "solution_template": "{a}x + {b}x = {sum}x",
                "answer_template": "{sum}x"
            },
            {
                "text": "Solve: x + {a} = {b}",
                "variables": {"a": (1, 20), "b": (5, 30)},
                "solution_template": "x + {a} = {b}\nx = {b} - {a}\nx = {answer}",
                "answer_template": "x = {answer}"
            }
        ],
        "math_algebra_linear_equations": [
            {
                "text": "Solve for x: {a}x + {b} = {c}",
                "variables": {"a": (2, 5), "b": (1, 10), "c": (10, 30)},
                "solution_template": "{a}x + {b} = {c}\n{a}x = {c} - {b}\n{a}x = {c_minus_b}\nx = {c_minus_b} / {a}\nx = {answer}",
                "answer_template": "x = {answer}"
            }
        ],
        "math_algebra_quadratic_equations": [
            {
                "text": "Solve: x² + {b}x + {c} = 0",
                "variables": {"b": (-10, 10), "c": (-20, 20)},
                "solution_template": "Using the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a\nWith a=1, b={b}, c={c}:\nx = (-({b}) ± √(({b})² - 4(1)({c}))) / 2(1)\nx = (-{b} ± √({b_squared} - {four_c})) / 2\nx = (-{b} ± √{discriminant}) / 2\nx = (-{b} ± {sqrt_discriminant}) / 2\nx = ({neg_b_plus_sqrt} / 2) or x = ({neg_b_minus_sqrt} / 2)\nx = {answer1} or x = {answer2}",
                "answer_template": "x = {answer1} or x = {answer2}"
            }
        ]
    }
    
    # Select a template based on concept_id or return a default
    templates = question_templates.get(concept_id, [
        {
            "text": "Define the term: {concept}",
            "variables": {"concept": concept_id.replace("_", " ")},
            "solution_template": "Definition of {concept}",
            "answer_template": "Definition varies"
        }
    ])
    
    # Select a template based on difficulty
    template_index = min(int(difficulty / 2), len(templates) - 1)
    template = templates[template_index]
    
    # Fill in template variables
    variables = {}
    for var_name, var_range in template.get("variables", {}).items():
        if isinstance(var_range, tuple) and len(var_range) == 2:
            # For numeric ranges
            variables[var_name] = random.randint(var_range[0], var_range[1])
        else:
            # For non-numeric values
            variables[var_name] = var_range
    
    # Process the variables further for the solution
    solution_vars = dict(variables)
    
    # For algebra basics
    if concept_id == "math_algebra_basics" and "a" in variables and "b" in variables:
        solution_vars["sum"] = variables["a"] + variables["b"]
        solution_vars["answer"] = variables["b"] - variables["a"]
    
    # For linear equations
    if concept_id == "math_algebra_linear_equations" and all(k in variables for k in ["a", "b", "c"]):
        solution_vars["c_minus_b"] = variables["c"] - variables["b"]
        solution_vars["answer"] = (variables["c"] - variables["b"]) / variables["a"]
    
    # For quadratic equations
    if concept_id == "math_algebra_quadratic_equations" and all(k in variables for k in ["b", "c"]):
        a = 1  # Assuming a=1 for simplicity
        b = variables["b"]
        c = variables["c"]
        solution_vars["b_squared"] = b**2
        solution_vars["four_c"] = 4 * c
        solution_vars["discriminant"] = b**2 - 4*a*c
        
        if solution_vars["discriminant"] >= 0:
            solution_vars["sqrt_discriminant"] = round(solution_vars["discriminant"] ** 0.5, 3)
            solution_vars["neg_b_plus_sqrt"] = -b + solution_vars["sqrt_discriminant"]
            solution_vars["neg_b_minus_sqrt"] = -b - solution_vars["sqrt_discriminant"]
            solution_vars["answer1"] = round((-b + solution_vars["sqrt_discriminant"]) / (2*a), 3)
            solution_vars["answer2"] = round((-b - solution_vars["sqrt_discriminant"]) / (2*a), 3)
        else:
            # Complex roots
            solution_vars["sqrt_discriminant"] = f"{round((-solution_vars['discriminant']) ** 0.5, 3)}i"
            solution_vars["answer1"] = f"{round(-b/(2*a), 3)} + {round(((-solution_vars['discriminant']) ** 0.5)/(2*a), 3)}i"
            solution_vars["answer2"] = f"{round(-b/(2*a), 3)} - {round(((-solution_vars['discriminant']) ** 0.5)/(2*a), 3)}i"
    
    # Format text and solution
    text = template["text"].format(**variables)
    solution = template["solution_template"].format(**solution_vars) if "solution_template" in template else ""
    answer = template["answer_template"].format(**solution_vars) if "answer_template" in template else ""
    
    return {
        "id": f"q_{concept_id}_{random.randint(1000, 9999)}",
        "concept_id": concept_id,
        "difficulty": difficulty,
        "text": text,
        "solution": solution,
        "answer": answer,
        "variables": variables
    }


def evaluate_student_answer(question: Dict[str, Any], student_answer: str) -> Dict[str, Any]:
    """
    Evaluate a student's answer to a question
    
    Args:
        question: The question object
        student_answer: The student's answer as a string
        
    Returns:
        Evaluation results
    """
    # In a real implementation, this would use NLP and math parsing to evaluate the answer
    # Here we'll do a simple string comparison with some basic normalization
    
    def normalize_answer(answer):
        """Normalize an answer string for comparison"""
        return (answer.lower()
                .replace(" ", "")
                .replace("x=", "")
                .replace("y=", ""))
    
    correct_answer = normalize_answer(question["answer"])
    student_answer_norm = normalize_answer(student_answer)
    
    # Simple exact match for now
    is_correct = student_answer_norm == correct_answer
    
    # In a real implementation, we would have partial matching and error analysis
    error_type = None
    if not is_correct:
        # Try to guess error type - very simplified example
        if question["concept_id"] == "math_algebra_linear_equations":
            # Check for sign error
            if "-" in correct_answer and "+" in student_answer_norm:
                error_type = "sign_error"
            # Check for arithmetic error (within 20% of correct value)
            elif student_answer_norm.replace("-", "").isdigit() and correct_answer.replace("-", "").isdigit():
                try:
                    student_val = float(student_answer_norm)
                    correct_val = float(correct_answer)
                    if abs((student_val - correct_val) / correct_val) < 0.2:
                        error_type = "arithmetic_error"
                except (ValueError, ZeroDivisionError):
                    pass
    
    return {
        "question_id": question["id"],
        "is_correct": is_correct,
        "error_type": error_type,
        "correct_answer": question["answer"],
        "student_answer": student_answer,
        "timestamp": datetime.now().isoformat()
    }


def generate_performance_analytics(student_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
    """
    Generate performance analytics for a student
    
    Args:
        student_id: The student's unique identifier
        timeframe_days: Number of days to include in the analysis
        
    Returns:
        Performance analytics
    """
    # In a real implementation, this would query a database
    # Here we'll generate sample data
    
    # Generate some sample data points over the timeframe
    start_date = datetime.now() - timedelta(days=timeframe_days)
    data_points = []
    
    # Simulate an improving learning curve
    accuracy_base = 0.65
    speed_base = 120  # seconds
    
    for day in range(timeframe_days):
        current_date = start_date + timedelta(days=day)
        
        # Simulate improvement over time with some random variation
        improvement_factor = min(day / timeframe_days * 0.3, 0.3)  # Max 30% improvement
        random_variation = random.uniform(-0.05, 0.05)
        
        accuracy = min(accuracy_base + improvement_factor + random_variation, 0.98)
        speed = max(speed_base * (1 - improvement_factor) + random.uniform(-10, 10), 30)
        
        # Generate 1-3 data points per day
        daily_points = random.randint(1, 3)
        for _ in range(daily_points):
            hour = random.randint(9, 20)  # Between 9 AM and 8 PM
            timestamp = current_date.replace(hour=hour, minute=random.randint(0, 59))
            
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "accuracy": round(accuracy, 2),
                "speed_seconds": round(speed),
                "difficulty": random.randint(1, 5),
                "concepts": [f"concept_{random.randint(1, 10)}" for _ in range(random.randint(1, 3))]
            })
    
    # Calculate aggregate metrics
    if data_points:
        avg_accuracy = sum(point["accuracy"] for point in data_points) / len(data_points)
        avg_speed = sum(point["speed_seconds"] for point in data_points) / len(data_points)
        
        # Calculate improvement
        first_week = [p for p in data_points if datetime.fromisoformat(p["timestamp"]) < start_date + timedelta(days=7)]
        last_week = [p for p in data_points if datetime.fromisoformat(p["timestamp"]) > datetime.now() - timedelta(days=7)]
        
        accuracy_improvement = 0
        speed_improvement = 0
        
        if first_week and last_week:
            first_week_acc = sum(p["accuracy"] for p in first_week) / len(first_week)
            last_week_acc = sum(p["accuracy"] for p in last_week) / len(last_week)
            accuracy_improvement = round((last_week_acc - first_week_acc) * 100, 1)
            
            first_week_speed = sum(p["speed_seconds"] for p in first_week) / len(first_week)
            last_week_speed = sum(p["speed_seconds"] for p in last_week) / len(last_week)
            speed_improvement = round((first_week_speed - last_week_speed) / first_week_speed * 100, 1)
    else:
        avg_accuracy = 0
        avg_speed = 0
        accuracy_improvement = 0
        speed_improvement = 0
    
    # Compile strengths and weaknesses
    concept_performance = {}
    for point in data_points:
        for concept in point["concepts"]:
            if concept not in concept_performance:
                concept_performance[concept] = {"total": 0, "correct": 0}
            concept_performance[concept]["total"] += 1
            concept_performance[concept]["correct"] += point["accuracy"]
    
    strengths = []
    weaknesses = []
    
    for concept, perf in concept_performance.items():
        avg = perf["correct"] / perf["total"] if perf["total"] > 0 else 0
        if avg > 0.85 and perf["total"] >= 3:
            strengths.append(concept)
        elif avg < 0.7 and perf["total"] >= 3:
            weaknesses.append(concept)
    
    return {
        "student_id": student_id,
        "timeframe_days": timeframe_days,
        "metrics": {
            "avg_accuracy": round(avg_accuracy * 100, 1),
            "avg_speed_seconds": round(avg_speed, 1),
            "accuracy_improvement": accuracy_improvement,  # percentage points
            "speed_improvement": speed_improvement,  # percentage
            "total_questions_attempted": len(data_points),
            "study_sessions": len(set(p["timestamp"].split("T")[0] for p in data_points))
        },
        "strengths": strengths[:3],  # Top 3 strengths
        "weaknesses": weaknesses[:3],  # Top 3 weaknesses
        "learning_style": "visual" if random.random() > 0.5 else "interactive",
        "recommendations": [
            "Focus on quadratic equations",
            "Try more word problems",
            "Schedule a tutoring session for challenging topics"
        ],
        "generated_at": datetime.now().isoformat()
    }


def detect_plagiarism(submission: str, reference_sources: List[str]) -> Dict[str, Any]:
    """
    Check for potential plagiarism in a student's submission
    
    Args:
        submission: The student's submission
        reference_sources: List of reference sources to check against
        
    Returns:
        Plagiarism analysis
    """
    # In a real implementation, this would use sophisticated text comparison
    # Here we'll do a simple similarity check
    
    def normalize_text(text):
        return text.lower().replace(" ", "")
    
    norm_submission = normalize_text(submission)
    matches = []
    
    for i, source in enumerate(reference_sources):
        norm_source = normalize_text(source)
        
        # Check for exact substring matches of significant length
        min_match_length = 30  # Characters
        
        for start in range(len(norm_submission) - min_match_length + 1):
            chunk = norm_submission[start:start + min_match_length]
            if chunk in norm_source:
                source_start = norm_source.find(chunk)
                
                # Try to extend the match
                match_length = min_match_length
                while (start + match_length < len(norm_submission) and 
                       source_start + match_length < len(norm_source) and
                       norm_submission[start + match_length] == norm_source[source_start + match_length]):
                    match_length += 1
                
                matches.append({
                    "source_index": i,
                    "source_start": source_start,
                    "submission_start": start,
                    "length": match_length,
                    "match_text": submission[start:start + match_length]
                })
    
    # Calculate overall similarity
    total_matched_chars = sum(match["length"] for match in matches)
    similarity_score = min(total_matched_chars / len(submission) if submission else 0, 1.0)
    
    return {
        "similarity_score": round(similarity_score, 2),
        "plagiarism_detected": similarity_score > 0.2,
        "suspicious_threshold": 0.2,
        "matches": matches,
        "recommendation": "Review academic integrity guidelines" if similarity_score > 0.2 else "No issues detected",
        "timestamp": datetime.now().isoformat()
    }
