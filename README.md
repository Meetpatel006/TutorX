# TutorX-MCP Server

A Model Context Protocol (MCP) server for educational AI tutoring as specified in the PRD.

## Overview

TutorX-MCP is an adaptive, multi-modal, and collaborative AI tutoring platform that leverages the Model Context Protocol (MCP) for tool integration and provides APIs for educational features.

## Features

- **Adaptive Learning Engine**: Concept graph, skill assessment, and personalized learning paths
- **Assessment Suite**: Quiz generation, solution analysis
- **Feedback System**: Error pattern analysis and contextual suggestions
- **Multi-Modal Interaction**: Text-based Q&A (with planned voice and handwriting recognition)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Dependencies as listed in pyproject.toml

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tutorx-mcp.git
cd tutorx-mcp

# Install dependencies
uv install
```

### Running the Server

```bash
python main.py
```

By default, the server will run in development mode and you can access it at http://localhost:8000.

## MCP Tool Integration

The server exposes MCP tools for:
- Skill assessment
- Quiz generation
- Error pattern analysis

And MCP resources for:
- Concept graph
- Learning paths

## License

This project is licensed under the MIT License - see the LICENSE file for details.