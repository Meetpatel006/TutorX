# TutorX MCP API Documentation

## Overview

The TutorX MCP API provides a comprehensive set of endpoints for educational tools and resources. The API follows RESTful principles and uses JSON for request/response bodies.

## Base URL

```
http://127.0.0.1:8000
```

## Authentication

Currently, the API does not require authentication. This will be implemented in future versions.

## Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the server.

**Response**
```json
{
    "status": "healthy",
    "timestamp": "2024-03-14T12:00:00.000Z",
    "server": "TutorX MCP",
    "version": "1.0.0"
}
```

### Core Features

#### Assess Skill

```http
POST /mcp/tools/assess_skill
```

Assesses a student's skill level on a specific concept.

**Request Body**
```json
{
    "student_id": "string",
    "concept_id": "string"
}
```

**Response**
```json
{
    "student_id": "string",
    "concept_id": "string",
    "skill_level": 0.75,
    "confidence": 0.85,
    "recommendations": [
        "Practice more complex problems",
        "Review related concept: algebra_linear_equations"
    ],
    "timestamp": "2024-03-14T12:00:00.000Z"
}
```

#### Get Concept Graph

```http
GET /mcp/resources/concept-graph://
```

Returns the full knowledge concept graph.

**Response**
```json
{
    "nodes": [
        {
            "id": "math_algebra_basics",
            "name": "Algebra Basics",
            "difficulty": 1
        }
    ],
    "edges": [
        {
            "from": "math_algebra_basics",
            "to": "math_algebra_linear_equations",
            "weight": 1.0
        }
    ]
}
```

#### Get Learning Path

```http
GET /mcp/resources/learning-path://{student_id}
```

Returns a personalized learning path for a student.

**Response**
```json
{
    "student_id": "string",
    "current_concepts": ["math_algebra_linear_equations"],
    "recommended_next": ["math_algebra_quadratic_equations"],
    "mastered": ["math_algebra_basics"],
    "estimated_completion_time": "2 weeks"
}
```

#### Generate Quiz

```http
POST /mcp/tools/generate_quiz
```

Generates a quiz based on specified concepts and difficulty.

**Request Body**
```json
{
    "concept_ids": ["string"],
    "difficulty": 2
}
```

**Response**
```json
{
    "quiz_id": "string",
    "concept_ids": ["string"],
    "difficulty": 2,
    "questions": [
        {
            "id": "string",
            "text": "string",
            "type": "string",
            "answer": "string",
            "solution_steps": ["string"]
        }
    ]
}
```

## Error Responses

The API uses standard HTTP status codes and returns error details in the response body:

```json
{
    "error": "Error message",
    "timestamp": "2024-03-14T12:00:00.000Z"
}
```

Common status codes:
- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

## Rate Limiting

Currently, there are no rate limits implemented. This will be added in future versions.

## Versioning

The API version is included in the response headers and health check endpoint. Future versions will support versioning through the URL path.

## Support

For support or to report issues, please contact the development team or create an issue in the project repository. 