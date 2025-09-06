# API Structure and Routing Hierarchy

## Overview

This document outlines the complete API structure of the AI Middleware system, including all endpoints, their purposes, authentication requirements, and routing hierarchy.

## API Routing Structure

```mermaid
graph TB
    Root[Root /] --> Health[/healthcheck]
    Root --> Test[/90-sec]
    Root --> Stream[/stream]
    
    Root --> V1Model[/api/v1/model]
    Root --> V2Model[/api/v2/model]
    Root --> Chatbot[/chatbot]
    Root --> Bridge[/bridge]
    Root --> Config[/api/v1/config]
    Root --> Functions[/functions]
    Root --> BridgeVersions[/bridge/versions]
    Root --> ImageProcessing[/image/processing]
    Root --> Utils[/utils]
    Root --> RAG[/rag]
    Root --> Internal[/internal]
    Root --> Testcases[/testcases]
    
    V1Model --> V1Deprecated[Deprecated Routes]
    V2Model --> V2Active[Active Model Routes]
    
    Chatbot --> ChatbotSend[/{botId}/sendMessage]
    Chatbot --> ChatbotReset[/{botId}/resetchat]
    
    Bridge --> BridgeMain[Bridge Operations]
    
    Config --> ConfigOps[Configuration Management]
    
    Functions --> FunctionCalls[API Function Calls]
    
    BridgeVersions --> VersionMgmt[Version Management]
    
    ImageProcessing --> ImageOps[Image Processing]
    
    Utils --> UtilityOps[Utility Operations]
    
    RAG --> RAGOps[RAG Operations]
    
    Internal --> InternalOps[Internal Operations]
    
    Testcases --> TestOps[Test Case Management]
```

## Detailed API Endpoints

### Core System Endpoints

#### Health and Monitoring
```
GET /healthcheck
- Purpose: System health check
- Authentication: None
- Response: System status information

GET /90-sec  
- Purpose: Long-running request test (90 seconds)
- Authentication: None
- Response: Test completion status

GET /stream
- Purpose: Server-sent events streaming endpoint
- Authentication: None
- Response: Event stream data
```

### Model API Endpoints

#### V1 Model API (Deprecated)
```
POST /api/v1/model/chat/completion
- Status: Deprecated (Returns 410)
- Migration: Use /api/v2/model/chat/completion

POST /api/v1/model/playground/chat/completion/{bridge_id}
- Purpose: Playground chat completion
- Authentication: JWT required
- Parameters: bridge_id (path)
- Middleware: Configuration injection
```

#### V2 Model API (Active)
```
POST /api/v2/model/chat/completion
- Purpose: Main chat completion endpoint
- Authentication: Based on configuration
- Features: Multi-provider AI integration
- Response: Standardized AI response format

POST /api/v2/model/playground/chat/completion/{bridge_id}
- Purpose: V2 playground endpoint
- Authentication: JWT required
- Parameters: bridge_id (path)
```

### Chatbot Endpoints

```
POST /chatbot/{botId}/sendMessage
- Purpose: Send message to chatbot
- Authentication: Dual auth (chatbot auth OR agents auth)
- Rate Limiting: 
  - 100 requests per slugName
  - 20 requests per threadId
- Parameters: botId (path)

POST /chatbot/{botId}/resetchat
- Purpose: Reset chatbot conversation
- Authentication: Chatbot authentication
- Rate Limiting: Applied
- Parameters: botId (path)
```

### Bridge Management

```
/bridge/*
- Purpose: Bridge configuration and management
- Authentication: Varies by endpoint
- Features: Bridge lifecycle management
```

### Configuration Management

```
/api/v1/config/*
- Purpose: System configuration management
- Authentication: JWT required
- Operations: CRUD operations on configurations
```

### Function Calls

```
/functions/*
- Purpose: External API function calls
- Authentication: Based on function requirements
- Features: Function call routing and execution
```

### Bridge Versions

```
/bridge/versions/*
- Purpose: Bridge version management
- Authentication: Required
- Operations: Version CRUD operations
```

### Image Processing

```
/image/processing/*
- Purpose: Image processing operations
- Authentication: Required
- Features: Image manipulation and analysis
```

### Utilities

```
/utils/*
- Purpose: Utility functions and helpers
- Authentication: Varies
- Features: Common utility operations
```

### RAG (Retrieval-Augmented Generation)

```
/rag/*
- Purpose: RAG operations
- Authentication: Required
- Features: Document processing and retrieval
```

### Internal Operations

```
/internal/*
- Purpose: Internal system operations
- Authentication: Internal authentication
- Features: System maintenance and operations
```

### Test Cases

```
/testcases/*
- Purpose: Test case management
- Authentication: Required
- Features: Test execution and management
```

## Authentication Matrix

| Endpoint Group | Authentication Type | Rate Limiting | Special Requirements |
|---------------|--------------------|--------------|--------------------|
| Health/Monitor | None | No | Public access |
| V1 Model | JWT | Yes | Deprecated |
| V2 Model | JWT/API Key | Yes | Bridge configuration |
| Chatbot | Dual Auth | Yes | Bot-specific limits |
| Bridge | JWT | Yes | Admin access |
| Config | JWT | Yes | Admin access |
| Functions | Variable | Yes | Function-dependent |
| Versions | JWT | Yes | Version control |
| Image | JWT | Yes | Processing limits |
| Utils | Variable | Variable | Utility-dependent |
| RAG | JWT | Yes | Document access |
| Internal | Internal Auth | No | System operations |
| Testcases | JWT | Yes | Test environment |

## Middleware Stack

### Global Middleware (Applied to All Routes)
1. **CORS Middleware**
   - Allow all origins (*)
   - Allow all methods
   - Allow all headers
   - Max age: 86400 seconds

2. **Atatus Middleware**
   - Application performance monitoring
   - Only in production environment

### Route-Specific Middleware

#### Authentication Middleware
- **JWT Middleware**: Token validation and user extraction
- **Chatbot Auth**: Bot-specific authentication
- **Agents Auth**: Agent-based authentication

#### Rate Limiting Middleware
- **User-based limiting**: Per user request limits
- **Thread-based limiting**: Per conversation thread limits
- **Slug-based limiting**: Per bot slug limits

#### Configuration Middleware
- **Bridge Configuration**: Injects bridge-specific configuration
- **User Data**: Adds user context to requests

## Error Handling

### Standard Error Responses
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `410`: Gone (deprecated endpoints)
- `429`: Too Many Requests (rate limiting)
- `500`: Internal Server Error

## Request/Response Patterns

### Standard Request Format
```json
{
  "model": "gpt-4",
  "messages": [...],
  "temperature": 0.7,
  "max_tokens": 1000,
  "tools": [...],
  "stream": false
}
```

### Standard Response Format
```json
{
  "success": true,
  "data": {
    "id": "response_id",
    "choices": [...],
    "usage": {
      "prompt_tokens": 100,
      "completion_tokens": 200,
      "total_tokens": 300
    }
  },
  "metadata": {
    "provider": "openai",
    "model": "gpt-4",
    "latency": 1500
  }
}
```

## API Versioning Strategy

### Version 1 (v1)
- **Status**: Deprecated
- **Endpoints**: `/api/v1/*`
- **Migration Path**: Use v2 equivalents

### Version 2 (v2)
- **Status**: Active
- **Endpoints**: `/api/v2/*`
- **Features**: Enhanced functionality, better error handling

### Unversioned Endpoints
- Core system endpoints (health, streaming)
- Domain-specific endpoints (chatbot, bridge, etc.)

This API structure provides a comprehensive interface for AI middleware operations while maintaining backward compatibility and clear separation of concerns.