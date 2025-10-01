# Component Interaction Diagrams

## Detailed Component Interaction Flow

### 1. Chat Completion Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI as FastAPI App
    participant Auth as Auth Middleware
    participant Controller as Model Controller
    participant BaseService as Base Service
    participant Cache as Redis Cache
    participant Provider as AI Provider
    participant Queue as RabbitMQ
    participant MongoDB as MongoDB
    participant TimescaleDB as TimescaleDB

    Client->>FastAPI: POST /api/v2/model/chat/completion
    FastAPI->>Auth: Validate JWT token
    Auth->>Controller: Authorized request
    Controller->>BaseService: Process chat request
    
    BaseService->>Cache: Check cached response
    alt Cache Hit
        Cache->>BaseService: Return cached response
        BaseService->>Controller: Cached result
    else Cache Miss
        BaseService->>Provider: Send AI request
        Provider->>BaseService: AI response
        BaseService->>Cache: Store response in cache
    end
    
    BaseService->>MongoDB: Store conversation
    BaseService->>TimescaleDB: Store metrics
    BaseService->>Queue: Queue background tasks
    
    BaseService->>Controller: Final response
    Controller->>FastAPI: JSON response
    FastAPI->>Client: HTTP response
```

### 2. Function Call Processing Flow

```mermaid
flowchart TD
    Start([AI Request with Tools]) --> ValidateTools{Validate Tool Calls}
    ValidateTools -->|Valid| ProcessTools[Process Tool Calls]
    ValidateTools -->|Invalid| ErrorResponse[Return Error]
    
    ProcessTools --> RunTools[Execute Function Calls]
    RunTools --> UpdateConfig[Update Configuration]
    UpdateConfig --> SecondAICall[Make Follow-up AI Call]
    SecondAICall --> CheckMoreTools{More Tool Calls?}
    
    CheckMoreTools -->|Yes| ProcessTools
    CheckMoreTools -->|No| FinalResponse[Return Final Response]
    
    FinalResponse --> StoreResults[Store in Database]
    StoreResults --> End([End])
    
    ErrorResponse --> End
```

### 3. Queue Processing Flow

```mermaid
graph LR
    subgraph "Queue Producer"
        Request[Incoming Request] --> QueueService[Queue Service]
        QueueService --> RabbitMQ[(RabbitMQ)]
    end
    
    subgraph "Queue Consumer"
        RabbitMQ --> Consumer[Background Consumer]
        Consumer --> ProcessMessage[Process Message]
        ProcessMessage --> AICall[AI Provider Call]
        AICall --> StoreResult[Store Result]
        StoreResult --> Complete[Mark Complete]
    end
    
    subgraph "Error Handling"
        ProcessMessage --> Error{Error?}
        Error -->|Yes| Retry[Retry Logic]
        Error -->|No| Success[Success]
        Retry -->|Max Retries| DeadLetter[Dead Letter Queue]
        Retry -->|Retry| ProcessMessage
    end
```

### 4. Configuration Management Flow

```mermaid
graph TB
    subgraph "Configuration Sources"
        EnvVars[Environment Variables]
        MongoDB[MongoDB Configs]
        DefaultVals[Default Values]
    end
    
    subgraph "Configuration Loading"
        ConfigLoader[Configuration Loader]
        ModelConfig[Model Configuration]
        ServiceKeys[Service Keys]
    end
    
    subgraph "Change Detection"
        ChangeStream[MongoDB Change Stream]
        Listener[Background Listener]
        Refresh[Refresh Configuration]
    end
    
    subgraph "Application Usage"
        BaseService[Base Service]
        Controllers[Controllers]
        Middlewares[Middlewares]
    end
    
    EnvVars --> ConfigLoader
    MongoDB --> ConfigLoader
    DefaultVals --> ConfigLoader
    
    ConfigLoader --> ModelConfig
    ConfigLoader --> ServiceKeys
    
    MongoDB --> ChangeStream
    ChangeStream --> Listener
    Listener --> Refresh
    Refresh --> ModelConfig
    
    ModelConfig --> BaseService
    ServiceKeys --> Controllers
    ModelConfig --> Middlewares
```

### 5. Authentication & Rate Limiting Flow

```mermaid
graph TD
    Request[Incoming Request] --> AuthCheck{Authentication Required?}
    
    AuthCheck -->|Yes| ValidateJWT[Validate JWT Token]
    AuthCheck -->|No| RateLimit[Check Rate Limits]
    
    ValidateJWT -->|Valid| RateLimit
    ValidateJWT -->|Invalid| AuthError[Return 401 Unauthorized]
    
    RateLimit --> CheckUserLimit{User Rate Limit}
    CheckUserLimit -->|Within Limit| CheckThreadLimit{Thread Rate Limit}
    CheckUserLimit -->|Exceeded| RateLimitError[Return 429 Too Many Requests]
    
    CheckThreadLimit -->|Within Limit| ProcessRequest[Process Request]
    CheckThreadLimit -->|Exceeded| RateLimitError
    
    ProcessRequest --> Success[Continue to Controller]
    
    AuthError --> End[Return Error Response]
    RateLimitError --> End
    Success --> End
```

### 6. Database Interaction Pattern

```mermaid
graph LR
    subgraph "Application Layer"
        Services[Services]
        Controllers[Controllers]
    end
    
    subgraph "Database Services"
        MongoService[MongoDB Service]
        TimescaleService[TimescaleDB Service]
        CacheService[Redis Service]
    end
    
    subgraph "Data Storage"
        MongoDB[(MongoDB<br/>Configurations<br/>Conversations<br/>API Calls)]
        TimescaleDB[(TimescaleDB<br/>Metrics<br/>Analytics<br/>Time-series)]
        Redis[(Redis<br/>Cache<br/>Sessions<br/>Rate Limits)]
    end
    
    Services --> MongoService
    Services --> TimescaleService
    Services --> CacheService
    Controllers --> MongoService
    
    MongoService --> MongoDB
    TimescaleService --> TimescaleDB
    CacheService --> Redis
```

### 7. Error Handling & Monitoring Flow

```mermaid
graph TB
    Request[Request Processing] --> Error{Error Occurred?}
    
    Error -->|No| Success[Successful Response]
    Error -->|Yes| LogError[Log Error Details]
    
    LogError --> SendMetrics[Send to Metrics Service]
    LogError --> NotifyAtatus[Send to Atatus]
    LogError --> CheckWebhook{Webhook Configured?}
    
    CheckWebhook -->|Yes| SendWebhook[Send Error Webhook]
    CheckWebhook -->|No| FormatError[Format Error Response]
    
    SendWebhook --> FormatError
    SendMetrics --> TimescaleDB[(TimescaleDB)]
    NotifyAtatus --> Atatus[Atatus Monitoring]
    
    FormatError --> ClientResponse[Return Error to Client]
    Success --> ClientResponse
```

### 8. AI Provider Abstraction Layer

```mermaid
graph TB
    subgraph "Service Selection"
        Request[AI Request] --> ServiceRouter{Select AI Service}
        ServiceRouter --> OpenAI[OpenAI Service]
        ServiceRouter --> Anthropic[Anthropic Service]
        ServiceRouter --> Groq[Groq Service]
        ServiceRouter --> Gemini[Gemini Service]
        ServiceRouter --> Mistral[Mistral Service]
        ServiceRouter --> OpenRouter[OpenRouter Service]
    end
    
    subgraph "Request Processing"
        OpenAI --> FormatRequest[Format Request]
        Anthropic --> FormatRequest
        Groq --> FormatRequest
        Gemini --> FormatRequest
        Mistral --> FormatRequest
        OpenRouter --> FormatRequest
        
        FormatRequest --> MakeAPICall[Make API Call]
        MakeAPICall --> ProcessResponse[Process Response]
        ProcessResponse --> StandardizeFormat[Standardize Format]
    end
    
    subgraph "Response Handling"
        StandardizeFormat --> TokenCalculation[Calculate Token Usage]
        TokenCalculation --> StoreMetrics[Store Usage Metrics]
        StoreMetrics --> ReturnResponse[Return Standardized Response]
    end
```

## Key Integration Points

### 1. Service-to-Service Communication
- **Synchronous**: Direct function calls between services
- **Asynchronous**: RabbitMQ message queues for background tasks
- **Caching**: Redis for frequently accessed data

### 2. Data Persistence Patterns
- **MongoDB**: Document storage for configurations and conversations
- **TimescaleDB**: Time-series data for metrics and analytics
- **Redis**: Temporary storage for cache and session data

### 3. External API Integration
- **AI Providers**: RESTful API calls with retry logic
- **Webhooks**: Outbound notifications for events
- **Monitoring**: Atatus APM integration

### 4. Background Processing
- **Queue Workers**: Process messages asynchronously
- **Change Stream Listeners**: React to database changes
- **Scheduled Tasks**: Periodic maintenance operations

### 5. Error Propagation
- **Service Level**: Errors bubble up through service layers
- **Client Level**: Standardized error responses
- **Monitoring Level**: Error tracking and alerting

This interaction model ensures loose coupling between components while maintaining data consistency and providing comprehensive error handling and monitoring capabilities.