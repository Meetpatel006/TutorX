"""
Text interaction and submission checking tools for TutorX.
"""
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional
from mcp_server.mcp_instance import mcp

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate the similarity ratio between two texts."""
    return SequenceMatcher(None, text1, text2).ratio()

@mcp.tool()
async def text_interaction(query: str, student_id: str) -> Dict[str, Any]:
    """
    Process a text query from a student and provide an educational response.
    
    Args:
        query: The student's question or input text
        student_id: Unique identifier for the student
        
    Returns:
        Dictionary containing the response and metadata
    """
    # Simple response generation based on keywords
    query_lower = query.lower()
    
    # Check for greetings
    if any(word in query_lower for word in ["hello", "hi", "hey"]):
        return {
            "response": f"Hello! I'm your TutorX assistant. How can I help you today, Student {student_id}?",
            "suggested_actions": [
                "Ask a question about programming",
                "Request a lesson on a topic",
                "Take a quiz"
            ]
        }
    
    # Check for help request
    if "help" in query_lower or "confused" in query_lower:
        return {
            "response": "I'm here to help! Could you please tell me what specific topic or concept you're struggling with?",
            "suggested_actions": [
                "Explain functions in Python",
                "What is object-oriented programming?",
                "Help me debug my code"
            ]
        }
    
    # Default response for other queries
    return {
        "response": f"I understand you're asking about: {query}. Here's what I can tell you...",
        "metadata": {
            "student_id": student_id,
            "query_type": "general_inquiry"
        },
        "suggested_resources": [
            {"title": "Related Documentation", "url": "https://docs.python.org/3/"},
            {"title": "Tutorial Video", "url": "https://www.youtube.com/"},
            {"title": "Practice Exercises", "url": "https://www.hackerrank.com/"}
        ]
    }

@mcp.tool()
async def check_submission_originality(submission: str, reference_sources: List[str]) -> Dict[str, Any]:
    """
    Check a student's submission for potential plagiarism against reference sources.
    
    Args:
        submission: The student's submission text
        reference_sources: List of reference texts to check against
        
    Returns:
        Dictionary with originality analysis results
    """
    if not submission or not reference_sources:
        return {"error": "Both submission and reference_sources are required"}
    
    # Simple plagiarism check using string similarity
    results = []
    for i, source in enumerate(reference_sources, 1):
        if not source:
            continue
            
        similarity = calculate_similarity(submission, source)
        results.append({
            "source_index": i,
            "similarity_score": round(similarity, 4),
            "is_original": similarity < 0.7,  # Threshold for originality
            "suspicious_sections": []
        })
    
    # Check for exact matches
    exact_matches = []
    submission_words = submission.split()
    for i in range(len(submission_words) - 4):  # Check 5-word sequences
        seq = ' '.join(submission_words[i:i+5])
        for j, source in enumerate(reference_sources):
            if seq in source:
                exact_matches.append({
                    "source_index": j + 1,
                    "matched_text": seq,
                    "position": i
                })
    
    # Calculate overall originality score (weighted average)
    if results:
        avg_similarity = sum(r["similarity_score"] for r in results) / len(results)
        originality_score = max(0, 1 - avg_similarity)
    else:
        originality_score = 1.0
    
    return {
        "originality_score": round(originality_score, 2),
        "is_original": all(r["is_original"] for r in results) if results else True,
        "sources_checked": len(reference_sources),
        "source_comparisons": results,
        "exact_matches": exact_matches,
        "recommendations": [
            "Paraphrase any sections with high similarity scores",
            "Add proper citations for referenced material",
            "Use your own words to explain concepts"
        ] if any(not r["is_original"] for r in results) else [
            "Good job! Your work appears to be original.",
            "Remember to always cite your sources properly."
        ]
    }
