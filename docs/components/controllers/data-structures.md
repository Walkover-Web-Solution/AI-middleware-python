# Data Structures - Request & Response Formats

## 📥 Request Data Structures

### Chat Completion Request
```json
{
  "bridge_id": "string",
  "user": "string",
  "service": "openai",
  "model": "gpt-4",
  "thread_id": "string",
  "sub_thread_id": "string",
  "org_id": "string",
  "variables": {
    "key": "value"
  },
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather information",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name"
            }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "response_format": {
    "type": "default"
  },
  "temperature": 0.7,
  "max_tokens": 1000,
  "files": ["file_id_1", "file_id_2"],
  "images": ["image_url_1", "image_url_2"],
  "is_playground": false
}
```

### Required Fields
- **bridge_id**: Bridge identifier for configuration lookup
- **user**: User message content (required unless images provided)
- **service**: AI service provider (openai, anthropic, gemini, etc.)
- **model**: Specific model name

### Optional Fields
- **thread_id**: Conversation thread identifier
- **sub_thread_id**: Sub-conversation identifier
- **org_id**: Organization identifier
- **variables**: Key-value pairs for prompt variable replacement
- **tools**: Available function tools for the AI
- **response_format**: Response formatting configuration
- **temperature**: Model creativity parameter (0.0-2.0)
- **max_tokens**: Maximum response length
- **files**: Array of uploaded file identifiers
- **images**: Array of image URLs or identifiers
- **is_playground**: Flag for playground vs production mode

## 📤 Response Data Structures

### Standard Success Response
```json
{
  "success": true,
  "output": [
    {
      "type": "text",
      "content": {
        "text": "AI response content here"
      },
      "metadata": {
        "content_type": "text/plain",
        "length": 123
      }
    }
  ],
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "total_tokens": 150,
    "input_cost": 0.003,
    "output_cost": 0.003,
    "total_cost": 0.006
  },
  "metadata": {
    "service": "openai",
    "model": "gpt-4",
    "processing_time_ms": 1250,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Function Call Response
```json
{
  "success": true,
  "output": [
    {
      "type": "function_call",
      "content": {
        "name": "get_weather",
        "arguments": {
          "location": "New York"
        },
        "result": {
          "temperature": "22°C",
          "condition": "Sunny"
        }
      },
      "metadata": {
        "execution_time_ms": 500,
        "success": true
      }
    },
    {
      "type": "text",
      "content": {
        "text": "The weather in New York is 22°C and sunny."
      },
      "metadata": {
        "content_type": "text/plain",
        "length": 45
      }
    }
  ],
  "usage": {
    "input_tokens": 120,
    "output_tokens": 75,
    "total_tokens": 195,
    "total_cost": 0.008
  },
  "metadata": {
    "service": "openai",
    "model": "gpt-4",
    "processing_time_ms": 1750,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "type": "VALIDATION_ERROR",
    "message": "Missing required field: user",
    "code": "MISSING_REQUIRED_FIELD",
    "details": {
      "field": "user",
      "expected_type": "string"
    }
  },
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_123456"
  }
}
```

## 🔧 Internal Data Structures

### Parsed Request Data (Internal)
```python
class ParsedRequestData:
    """Internal representation of parsed request"""
    
    # Core identifiers
    bridge_id: str
    org_id: str
    thread_id: Optional[str]
    sub_thread_id: Optional[str]
    
    # AI configuration
    service: str
    model: str
    configuration: Dict[str, Any]
    apikey: str
    
    # Content
    user: str
    variables: Dict[str, Any]
    tools: List[Dict]
    files: List[str]
    images: List[str]
    
    # Settings
    temperature: Optional[float]
    max_tokens: Optional[int]
    response_format: Dict[str, Any]
    is_playground: bool
    
    # Enriched data (added by middleware)
    rag_data: List[Dict]
    gpt_memory: bool
    tool_id_mapping: Dict[str, str]
    pre_tools: Optional[Dict]
```

### Service Parameters
```python
class ServiceParameters:
    """Parameters passed to AI service handlers"""
    
    customConfig: Dict[str, Any]
    configuration: Dict[str, Any]
    apikey: str
    user: str
    tools: List[Dict]
    org_id: str
    bridge_id: str
    thread_id: str
    model: str
    service: str
    token_calculator: TokenCalculator
    variables: Dict[str, Any]
    memory: str
    rag_data: List[Dict]
    conversation: List[Dict]  # Formatted conversation history
    temperature: Optional[float]
    max_tokens: Optional[int]
    stream: bool = False
```

### Usage Metrics
```python
class UsageMetrics:
    """Token usage and cost calculation"""
    
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model: str
    service: str
    
    # Additional metrics
    reasoning_tokens: Optional[int] = None
    input_tokens_details: Optional[Dict] = None
    output_tokens_details: Optional[Dict] = None
```

## 🎯 Service-Specific Formats

### OpenAI Conversation Format
```python
openai_conversation = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    },
    {
        "role": "user",
        "content": "Hello, how are you?"
    },
    {
        "role": "assistant",
        "content": "I'm doing well, thank you!"
    }
]
```

### Anthropic Conversation Format
```python
anthropic_conversation = [
    {
        "role": "user",
        "content": "Hello, how are you?"
    },
    {
        "role": "assistant", 
        "content": "I'm doing well, thank you!"
    }
]
# Note: System prompt passed separately in Anthropic API
```

### Gemini Conversation Format
```python
gemini_conversation = [
    {
        "role": "user",
        "parts": [
            {
                "text": "Hello, how are you?"
            }
        ]
    },
    {
        "role": "model",
        "parts": [
            {
                "text": "I'm doing well, thank you!"
            }
        ]
    }
]
```

## 📊 Database Schema Structures

### Raw Data Table
```sql
CREATE TABLE raw_data (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255),
    bridge_id VARCHAR(255),
    org_id VARCHAR(255),
    user_input TEXT,
    ai_response TEXT,
    model VARCHAR(100),
    service VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_cost DECIMAL(10,6),
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Conversation History Table
```sql
CREATE TABLE conversations (
    chat_id VARCHAR(255) PRIMARY KEY,
    thread_id VARCHAR(255),
    sub_thread_id VARCHAR(255),
    bridge_id VARCHAR(255),
    org_id VARCHAR(255),
    conversation_data JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### TimescaleDB Metrics Table
```sql
CREATE TABLE metrics_timeseries (
    time TIMESTAMPTZ NOT NULL,
    bridge_id VARCHAR(255),
    org_id VARCHAR(255),
    service VARCHAR(100),
    model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_cost DECIMAL(10,6),
    latency_ms INTEGER,
    success_rate DECIMAL(5,2),
    error_count INTEGER,
    request_count INTEGER
);
```

## 🔄 Configuration Structures

### Bridge Configuration
```json
{
  "_id": "ObjectId(...)",
  "bridge_id": "bridge_123",
  "org_id": "org_456",
  "name": "Customer Support Bot",
  "configuration": {
    "prompt": "You are a helpful customer support assistant...",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "tool_choice": "auto"
  },
  "tools": [
    {
      "name": "search_knowledge_base",
      "description": "Search the knowledge base",
      "parameters": {...}
    }
  ],
  "apikeys": {
    "openai": "sk-...",
    "anthropic": "sk-ant-..."
  },
  "rag_data": [
    {
      "document_id": "doc_123",
      "content": "Document content...",
      "metadata": {...}
    }
  ],
  "settings": {
    "gpt_memory": true,
    "max_tool_calls": 5,
    "enable_streaming": false
  }
}
```

### Model Configuration
```json
{
  "service": "openai",
  "models": [
    {
      "name": "gpt-4",
      "display_name": "GPT-4",
      "max_tokens": 8192,
      "supports_tools": true,
      "supports_vision": false,
      "supports_streaming": true,
      "cost_per_1k_input": 0.03,
      "cost_per_1k_output": 0.06,
      "fallback_models": ["gpt-4-turbo", "gpt-3.5-turbo"]
    }
  ]
}
```

## 🚨 Error Code Definitions

### Validation Errors (400)
- **MISSING_REQUIRED_FIELD**: Required field is missing
- **INVALID_FIELD_TYPE**: Field has incorrect data type
- **INVALID_FIELD_VALUE**: Field value is outside acceptable range
- **INVALID_MODEL_SERVICE_COMBINATION**: Model not available for service

### Authentication Errors (401)
- **INVALID_JWT_TOKEN**: JWT token is invalid or expired
- **MISSING_AUTHORIZATION**: Authorization header missing
- **INSUFFICIENT_PERMISSIONS**: User lacks required permissions

### Rate Limiting Errors (429)
- **RATE_LIMIT_EXCEEDED**: Request rate limit exceeded
- **DAILY_QUOTA_EXCEEDED**: Daily usage quota exceeded
- **CONCURRENT_LIMIT_EXCEEDED**: Too many concurrent requests

### Service Errors (500)
- **AI_SERVICE_ERROR**: Error from AI service provider
- **DATABASE_ERROR**: Database connection or query error
- **INTERNAL_PROCESSING_ERROR**: Internal processing failure
- **CONFIGURATION_ERROR**: Bridge or model configuration error

This comprehensive data structure documentation provides clear specifications for all request/response formats and internal data representations used throughout the AI middleware system.
