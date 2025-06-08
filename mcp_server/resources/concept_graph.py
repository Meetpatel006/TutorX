"""
Concept graph data structure for TutorX knowledge base.
"""
from typing import Dict, Any

# Store the concept graph data in memory
CONCEPT_GRAPH = {
    "python": {
        "id": "python",
        "name": "Python Programming",
        "description": "Fundamentals of Python programming language",
        "prerequisites": [],
        "related": ["functions", "oop", "data_structures"]
    },
    "functions": {
        "id": "functions",
        "name": "Python Functions",
        "description": "Creating and using functions in Python",
        "prerequisites": ["python"],
        "related": ["decorators", "lambdas"]
    },
    "oop": {
        "id": "oop",
        "name": "Object-Oriented Programming",
        "description": "Classes and objects in Python",
        "prerequisites": ["python"],
        "related": ["inheritance", "polymorphism"]
    },
    "data_structures": {
        "id": "data_structures",
        "name": "Data Structures",
        "description": "Built-in data structures in Python",
        "prerequisites": ["python"],
        "related": ["algorithms"]
    },
    "decorators": {
        "id": "decorators",
        "name": "Python Decorators",
        "description": "Function decorators in Python",
        "prerequisites": ["functions"],
        "related": ["python", "functions"]
    },
    "lambdas": {
        "id": "lambdas",
        "name": "Lambda Functions",
        "description": "Anonymous functions in Python",
        "prerequisites": ["functions"],
        "related": ["python", "functions"]
    },
    "inheritance": {
        "id": "inheritance",
        "name": "Inheritance in OOP",
        "description": "Creating class hierarchies in Python",
        "prerequisites": ["oop"],
        "related": ["python", "oop"]
    },
    "polymorphism": {
        "id": "polymorphism",
        "name": "Polymorphism in OOP",
        "description": "Multiple forms of methods in Python",
        "prerequisites": ["oop"],
        "related": ["python", "oop"]
    },
    "algorithms": {
        "id": "algorithms",
        "name": "Basic Algorithms",
        "description": "Common algorithms in Python",
        "prerequisites": ["data_structures"],
        "related": ["python", "data_structures"]
    }
}

def get_concept(concept_id: str) -> Dict[str, Any]:
    """Get a specific concept by ID or return None if not found."""
    return CONCEPT_GRAPH.get(concept_id)

def get_all_concepts() -> Dict[str, Any]:
    """Get all concepts in the graph."""
    return {"concepts": list(CONCEPT_GRAPH.values())}

def get_concept_graph() -> Dict[str, Any]:
    """Get the complete concept graph."""
    return CONCEPT_GRAPH
