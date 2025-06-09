# TutorX-MCP Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow](#data-flow)
4. [Technical Stack](#technical-stack)
5. [Security & Performance](#security--performance)
6. [Deployment Architecture](#deployment-architecture)

## System Overview

TutorX-MCP is an advanced educational AI tutoring platform that leverages the Model Context Protocol (MCP) for tool integration and provides a comprehensive suite of educational features through both MCP clients and a web interface.

```mermaid
graph TD
    A[Student] --> B[Web Interface]
    A --> C[MCP Client]
    B --> D[TutorX-MCP Server]
    C --> D
    D --> E[Core Features]
    D --> F[Advanced Features]
    D --> G[Multi-Modal Features]
    D --> H[Assessment Features]
```

## Architecture Components

### 1. Core Components

```mermaid
graph LR
    A[MCP Server] --> B[Core Features]
    A --> C[Advanced Features]
    A --> D[Multi-Modal Features]
    A --> E[Assessment Features]
    
    B --> B1[Adaptive Learning]
    B --> B2[Concept Graph]
    B --> B3[Learning Paths]
    
    C --> C1[Neurological Monitor]
    C --> C2[Knowledge Fusion]
    C --> C3[Lesson Authoring]
    
    D --> D1[Text Processing]
    D --> D2[Voice Processing]
    D --> D3[Handwriting Processing]
    
    E --> E1[Quiz Generation]
    E --> E2[Assessment Creation]
    E --> E3[Analytics]
```

### 2. Client-Server Architecture

```mermaid
sequenceDiagram
    participant C as Client
    participant S as MCP Server
    participant T as Tools
    participant R as Resources
    
    C->>S: HTTP Request
    S->>T: Tool Execution
    T->>S: Response
    S->>C: HTTP Response
    
    C->>S: Resource Request
    S->>R: Resource Fetch
    R->>S: Resource Data
    S->>C: Resource Response
```

## MCP Server Architecture (v0.1.0 - v0.2.0)

- The MCP server is structured to use a single shared `mcp` instance, defined in a dedicated module (`mcp_instance.py`)
- All tool modules import this shared instance to register their tools, ensuring all tools are available to the running server and MCP clients
- The server exposes the SSE transport at `/sse` for protocol-compliant client connections (e.g., MCP Inspector, Claude Desktop, etc.)
- Circular import issues are avoided by isolating the MCP instance from the main server and tool modules
- The server is fully compatible with MCP Inspector and other clients for tool discovery and invocation

**Updates in v0.2.0:**
- Added database integration for persistent storage of resources and user data
- Implemented role-based access control for secure API access
- Added Memory Bank for stateful interactions and learning progress tracking
- Enhanced model fallback mechanisms for improved reliability 
- Implemented caching strategies for frequently accessed resources

```mermaid
graph TD
    APIGateway[API Gateway Layer] --> AuthLayer[Authentication Layer]
    APIGateway --> SSEEndpoint[SSE Transport]
    
    AuthLayer --> ToolRegistry[Tool Registry]
    SSEEndpoint --> ToolRegistry
    
    ToolRegistry --> CoreTools[Core Tools]
    ToolRegistry --> AdvancedTools[Advanced Tools]
    ToolRegistry --> MemoryTools[Memory Tools]
    
    CoreTools --> ResourceAccess[Resource Access]
    AdvancedTools --> ResourceAccess
    MemoryTools --> ResourceAccess
    
    ResourceAccess --> CacheLayer[Cache Layer]
    CacheLayer --> Database[(Database)]
    CacheLayer --> ExternalAPIs[External APIs]
```

### Key Responsibilities
- **API Gateway:** Exposes HTTP endpoints for all core features (concepts, lessons, quizzes, learning paths, assessments, OCR, originality checking, etc.).
- **Tool Registration:** Uses MCP decorators to register modular tools from `mcp-server/tools/`. Each tool is an async function, making the system highly extensible.
- **Resource Management:** Manages the concept graph and curriculum standards as in-memory resources, enabling adaptive learning and standards alignment.
- **Model Integration:** Integrates Google Gemini Flash models for advanced text and quiz generation, with automatic fallback for reliability.
- **Multi-Modal Input:** Supports text, voice, and handwriting (via OCR) for student interaction.
- **Assessment & Analytics:** Provides endpoints for skill assessment, originality checking, and analytics.

### Extensibility
- **Adding Tools:** New educational tools can be added by creating an async function in `mcp-server/tools/` and registering it with the MCP instance. The server auto-discovers and exposes these tools via API endpoints.
- **Resource Expansion:** The concept graph and curriculum standards can be extended to support new subjects, countries, or educational standards.

### Example: Tool Registration
```python
@mcp.tool()
async def generate_quiz_tool(concept: str, difficulty: str = "medium") -> Dict[str, Any]:
    # ... implementation ...
```

## Memory Bank Implementation (v0.2.0)

The **Memory Bank** provides persistent or session-based memory for the TutorX-MCP platform. This feature:
- Stores and retrieves user/session context, learning progress, and conversation history
- Enables personalized, context-aware tutoring by allowing tools and endpoints to access relevant past interactions
- Supports both in-memory (for development) and persistent (database-backed) storage options
- Exposes memory operations (read, write, update, clear) as MCP tools for integration with the tutoring workflow
- Is designed for easy extension to support advanced analytics, recommendations, and adaptive learning features

**Architecture Integration:**
- The Memory Bank is implemented as a set of MCP tools in `memory_bank/memory_tools.py`
- It interacts with the concept graph, learning path, and assessment tools to provide a seamless, stateful tutoring experience
- Incorporates security and privacy protections with role-based access control

```mermaid
graph TD
    Client[Client Apps] -->|Request| MCP[MCP Server]
    MCP -->|Read/Write| MemoryBank[Memory Bank]
    MemoryBank -->|Store| SessionMemory[Session Memory]
    MemoryBank -->|Store| UserMemory[User Memory]
    MemoryBank -->|Store| ConceptMemory[Concept Memory]
    SessionMemory -->|Persist| DB[(Database)]
    UserMemory -->|Persist| DB
    ConceptMemory -->|Persist| DB
```

The Memory Bank exposes these key operations as MCP tools:
- `read_memory(memory_type, key)`: Retrieve stored memory
- `write_memory(memory_type, key, value)`: Store new memory
- `update_memory(memory_type, key, update)`: Modify existing memory
- `clear_memory(memory_type, key)`: Remove stored memory

## Data Flow

### 1. Student Interaction & Tool Invocation Flow

```mermaid
graph TD
    A[Student Input] --> B{Input Type}
    B -->|Text| C[API: /api/text-interaction]
    B -->|Voice| D[API: /api/voice-interaction]
    B -->|Handwriting| E[API: /api/pdf-ocr or /api/image-to-text]
    C & D & E --> F[MCP Tool Execution]
    F --> G[Response Generation]
    G --> H[Student Feedback]
    H --> I[Learning Path Update]
    I --> J[Concept Graph Update]
```

### 2. Tool Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant MCP_Server as MCP Server
    participant Tool
    Client->>MCP_Server: API Request (e.g., /api/generate-quiz)
    MCP_Server->>Tool: Invoke Registered Tool
    Tool-->>MCP_Server: Tool Response
    MCP_Server-->>Client: API Response
```

## Technical Stack

### 1. Technology Stack

```mermaid
graph TD
    A[TutorX-MCP] --> B[Backend]
    A --> C[Frontend]
    A --> D[Infrastructure]
    B --> B1[Python 3.12]
    B --> B2[FastAPI]
    B --> B3[FastMCP]
    B --> B4[Google Gemini Flash]
    B --> B5[Gradio]
    C --> C1[Web Interface]
    C --> C2[MCP Client]
    D --> D1[HTTP Server]
    D --> D2[Resource Management]
```

### 2. Dependencies

```mermaid
graph LR
    A[TutorX-MCP] --> B[mcp[cli] >= 1.9.3]
    A --> C[gradio >= 4.19.0]
    A --> D[numpy >= 1.24.0]
    A --> E[pillow >= 10.0.0]
    A --> F[fastapi]
    A --> G[google-generativeai]
    A --> H[pytesseract]
```

## Security & Performance

### 1. Security Architecture

```mermaid
graph TD
    A[Client Request] --> B[Authentication]
    B --> C[Authorization]
    C --> D[Request Validation]
    D --> E[Tool Execution]
    E --> F[Response Sanitization]
    F --> G[Client Response]
```

### 2. Performance Optimization

```mermaid
graph LR
    A[Request] --> B{Cache Check}
    B -->|Hit| C[Cache Response]
    B -->|Miss| D[Process Request]
    D --> E[Update Cache]
    E --> F[Response]
    C --> F
```

## Deployment Architecture

### 1. Deployment Model

```mermaid
graph TD
    A[Load Balancer] --> B[Server Instance 1]
    A --> C[Server Instance 2]
    A --> D[Server Instance N]
    
    B --> E[Database]
    C --> E
    D --> E
    
    B --> F[Cache]
    C --> F
    D --> F
```

### 2. Scaling Strategy

```mermaid
graph LR
    A[Monitoring] --> B{Load Check}
    B -->|High| C[Scale Up]
    B -->|Low| D[Scale Down]
    C --> E[New Instance]
    D --> F[Remove Instance]
```

## Key Features Implementation

### 1. MCP Server & Modular Tool System
- **Modular Tools:** All educational features (concepts, quizzes, lessons, learning paths, OCR, originality checking) are implemented as modular async tools in `mcp-server/tools/` and registered with the MCP server.
- **API Endpoints:** Each tool is exposed via a FastAPI endpoint, making the system easy to extend and integrate.
- **Model Integration:** Quiz and lesson generation leverage Google Gemini Flash models for advanced content creation.
- **Resource Management:** The server manages a concept graph and curriculum standards for adaptive learning and standards alignment.

### 2. Adaptive Learning Engine
- **Concept Graph:** Tracks student progress and concept relationships.
- **Personalized Learning Paths:** Generated based on prerequisites and student level.
- **Skill Assessment:** Tools for assessing student understanding and providing targeted feedback.

### 3. Multi-Modal Interaction
- **Text, Voice, Handwriting:** Supported via dedicated endpoints and tools (text interaction, OCR, etc.).
- **Real-Time Feedback:** Immediate responses and suggestions based on student input.

### 4. Assessment Suite
- **Automated Quiz Generation:** Using Gemini models and prompt templates.
- **Plagiarism Detection:** Originality checking tool compares submissions to reference sources.
- **Performance Analytics:** Endpoints for tracking and analyzing student progress.

### 5. Extensibility & Integration
- **Add New Tools:** Simply create a new async function in `mcp-server/tools/` and register with `@mcp.tool()`.
- **Expand Resources:** Update concept graph or curriculum standards for new subjects or regions.
- **API-First:** All features are accessible via HTTP API for easy integration with web clients or third-party systems.

## Future Considerations

1. **Scalability**
   - Implement horizontal scaling
   - Add caching layers
   - Optimize database queries

2. **Feature Expansion**
   - Add more interaction modes
   - Enhance analytics capabilities
   - Implement advanced AI features

3. **Integration**
   - Support for more educational standards
   - Integration with LMS systems
   - API expansion for third-party tools

4. **Performance**
   - Implement request batching
   - Add response compression
   - Optimize resource loading

## Conclusion

TutorX-MCP provides a robust, scalable, and feature-rich educational platform that leverages modern technologies and architectural patterns to deliver an exceptional learning experience. The system's modular design allows for easy expansion and maintenance while ensuring high performance and security. 