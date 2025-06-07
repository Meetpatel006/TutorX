# TutorX-MCP API Documentation

This document provides comprehensive documentation for the TutorX-MCP API for developers who want to integrate with the system.

## API Overview

The TutorX-MCP server exposes a Model Context Protocol (MCP) API that allows clients to interact with various educational tools and resources. This API follows the standard MCP protocol as defined in [MCP Specification](https://github.com/anthropics/anthropic-tools/blob/main/mcp/README.md).

## Authentication

For production deployments, all API requests should include an API key in the `Authorization` header:

```
Authorization: Bearer your-api-key-here
```

## Base URL

Default: `http://localhost:8000`

For production: See your deployment configuration

## Tools API

Tools represent functionality that can be invoked by MCP clients. Each tool is accessed via:

```
POST /tools/{tool_name}
Content-Type: application/json

{
  "param1": "value1",
  "param2": "value2"
}
```

### Core Features

#### Adaptive Learning Engine

##### `assess_skill`

Assess a student's skill level on a specific concept.

**Request:**
```json
{
  "student_id": "student123",
  "concept_id": "math_algebra_basics"
}
```

**Response:**
```json
{
  "student_id": "student123",
  "concept_id": "math_algebra_basics",
  "skill_level": 0.75,
  "confidence": 0.85,
  "recommendations": [
    "Practice more complex problems",
    "Review related concept: algebra_linear_equations"
  ],
  "timestamp": "2025-06-07T10:30:45.123456"
}
```

##### `generate_quiz`

Generate a quiz based on specified concepts and difficulty.

**Request:**
```json
{
  "concept_ids": ["math_algebra_basics", "math_algebra_linear_equations"],
  "difficulty": 2
}
```

**Response:**
```json
{
  "quiz_id": "q12345",
  "concept_ids": ["math_algebra_basics", "math_algebra_linear_equations"],
  "difficulty": 2,
  "questions": [
    {
      "id": "q1",
      "text": "Solve for x: 2x + 3 = 7",
      "type": "algebraic_equation",
      "answer": "x = 2",
      "solution_steps": [
        "2x + 3 = 7",
        "2x = 7 - 3",
        "2x = 4",
        "x = 4/2 = 2"
      ]
    }
  ]
}
```

#### Feedback System

##### `analyze_error_patterns`

Analyze common error patterns for a student on a specific concept.

**Request:**
```json
{
  "student_id": "student123",
  "concept_id": "math_algebra_basics"
}
```

**Response:**
```json
{
  "student_id": "student123",
  "concept_id": "math_algebra_basics",
  "common_errors": [
    {
      "type": "sign_error",
      "frequency": 0.65,
      "example": "2x - 3 = 5 → 2x = 5 - 3 → 2x = 2 → x = 1 (should be x = 4)"
    }
  ],
  "recommendations": [
    "Practice more sign manipulation problems"
  ]
}
```

### Advanced Features

#### Neurological Engagement Monitor

##### `analyze_cognitive_state`

Analyze EEG data to determine cognitive state.

**Request:**
```json
{
  "eeg_data": {
    "channels": [...],
    "sampling_rate": 256,
    "duration": 10.0
  }
}
```

**Response:**
```json
{
  "attention_level": 0.82,
  "cognitive_load": 0.65,
  "stress_level": 0.25,
  "recommendations": [
    "Student is engaged but approaching cognitive overload",
    "Consider simplifying next problems slightly"
  ],
  "timestamp": "2025-06-07T10:32:15.123456"
}
```

### External Integrations

#### Learning Management Systems

##### `lms_sync_grades`

Sync grades with a Learning Management System.

**Request:**
```json
{
  "lms_type": "canvas",
  "api_url": "https://canvas.example.com/api/v1",
  "api_key": "your-api-key",
  "course_id": "course123",
  "assignment_id": "assign456",
  "grades": [
    {
      "student_id": "student123",
      "score": 85.5
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-06-07T10:35:22.123456",
  "message": "Grades successfully synced"
}
```

#### Open Educational Resources

##### `oer_search`

Search for educational resources in OER repositories.

**Request:**
```json
{
  "repository_url": "https://oer.example.com/api",
  "query": "linear equations",
  "subject": "mathematics",
  "grade_level": "8"
}
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": "resource123",
      "title": "Introduction to Linear Equations",
      "description": "A comprehensive guide to solving linear equations",
      "url": "https://oer.example.com/resources/resource123",
      "subject": "mathematics",
      "grade_level": "8-9",
      "license": "CC-BY"
    }
  ],
  "timestamp": "2025-06-07T10:36:12.123456"
}
```

#### Real-Time Personalized Tutoring

##### `schedule_tutoring_session`

Schedule a session with a real-time personalized tutoring platform.

**Request:**
```json
{
  "platform_url": "https://tutoring.example.com/api",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "student_id": "student123",
  "subject": "mathematics",
  "datetime_str": "2025-06-10T15:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "session789",
  "tutor": {
    "id": "tutor456",
    "name": "Dr. Jane Smith",
    "rating": 4.9,
    "specialization": "mathematics"
  },
  "datetime": "2025-06-10T15:00:00Z",
  "join_url": "https://tutoring.example.com/session/session789",
  "timestamp": "2025-06-07T10:37:45.123456"
}
```

## Resources API

Resources represent data that can be fetched by MCP clients. Each resource is accessed via:

```
GET /resources?uri={resource_uri}
Accept: application/json
```

### Available Resources

#### `concept-graph://`

Retrieves the full knowledge concept graph.

#### `learning-path://{student_id}`

Retrieves the personalized learning path for a student.

#### `curriculum-standards://{country_code}`

Retrieves curriculum standards for a specific country.

#### `student-dashboard://{student_id}`

Retrieves dashboard data for a specific student.

## Error Handling

API errors follow a standard format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common error codes:
- `invalid_request`: The request was malformed
- `authentication_error`: Authentication failed
- `not_found`: The requested resource does not exist
- `server_error`: Internal server error

## Rate Limiting

Production deployments implement rate limiting to prevent abuse. Clients should monitor the following headers:

- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Remaining requests for the current hour
- `X-RateLimit-Reset`: Timestamp when the limit will reset

## SDK

For easier integration, we provide client SDKs in multiple languages:

- Python: `pip install tutorx-client`
- JavaScript: `npm install tutorx-client`

Example usage (Python):

```python
from tutorx_client import TutorXClient

client = TutorXClient("http://localhost:8000", api_key="your-api-key")

# Call a tool
result = client.assess_skill("student123", "math_algebra_basics")
print(result["skill_level"])

# Access a resource
concept_graph = client.get_concept_graph()
```

## Webhooks

For real-time updates, you can register webhook endpoints:

```
POST /webhooks/register
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "url": "https://your-app.example.com/webhook",
  "events": ["assessment.completed", "badge.awarded"],
  "secret": "your-webhook-secret"
}
```

## Support

For API support, contact us at api-support@tutorx-example.com
