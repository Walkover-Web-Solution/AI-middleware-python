# Architecture Quick Reference

## System Overview
**AI Middleware System** - A FastAPI-based service providing unified access to multiple AI providers with advanced features like caching, queuing, authentication, and monitoring.

## Key Components

### 🏗️ Application Architecture
```
Client → Load Balancer → FastAPI App → Base Service → AI Providers
                                    ↓
                              Queue/Cache/Database
```

### 🎯 Core Services
- **Base Service**: Central AI abstraction layer
- **Queue Service**: RabbitMQ-based async processing  
- **Cache Service**: Redis-based response caching
- **RAG Service**: Document processing and retrieval

### 🔌 AI Provider Integration
| Provider | Models | Features |
|----------|--------|----------|
| OpenAI | GPT-4, GPT-3.5, DALL-E | Chat, Embeddings, Images |
| Anthropic | Claude | Advanced reasoning |
| Google | Gemini | Multimodal capabilities |
| Groq | Various | High-speed inference |
| Mistral | Mistral models | European AI provider |
| OpenRouter | Multiple | Model routing |

### 🗄️ Database Architecture
- **MongoDB**: Configurations, conversations, metadata
- **PostgreSQL/TimescaleDB**: Structured data, time-series metrics
- **Redis**: Caching, sessions, rate limiting

## API Structure

### Main Endpoints
```
/api/v2/model/*        - AI model operations
/chatbot/*             - Chatbot interactions  
/bridge/*              - Bridge management
/api/v1/config/*       - Configuration management
/functions/*           - Function calls
/rag/*                 - RAG operations
```

### Authentication Flow
```
Request → JWT Validation → Rate Limiting → Authorization → Processing
```

## Deployment Architecture

### Container Stack
- **Application**: FastAPI + Gunicorn + Uvicorn
- **Workers**: Background queue processors
- **Databases**: MongoDB, PostgreSQL, Redis clusters
- **Message Queue**: RabbitMQ cluster
- **Monitoring**: Prometheus, Grafana, Atatus

### Kubernetes Resources
- **Deployments**: Application pods with HPA
- **StatefulSets**: Database clusters
- **Services**: Internal load balancing
- **Ingress**: External traffic routing
- **ConfigMaps/Secrets**: Configuration management

## Performance Characteristics

### Throughput
- **Peak Load**: 10,000+ requests/minute
- **Response Time**: <500ms (cached), <2s (uncached)
- **Concurrency**: 1,000+ simultaneous connections

### Scaling
- **Horizontal**: Auto-scaling based on CPU/memory
- **Database**: Read replicas and connection pooling
- **Cache**: Redis cluster with sharding

## Security Framework

### Access Control
- **JWT Authentication**: Stateless token validation
- **Rate Limiting**: Per-user, per-thread, per-organization
- **API Keys**: Service-to-service authentication

### Data Protection
- **Encryption**: TLS 1.3 in transit, database encryption at rest
- **Key Management**: Kubernetes secrets with rotation
- **Network Security**: VPC isolation, network policies

## Monitoring Stack

### Metrics
- **Application**: Request rates, response times, errors
- **Infrastructure**: CPU, memory, disk, network
- **Business**: AI usage, token consumption, costs

### Observability
- **Logging**: Structured JSON logs with correlation IDs
- **Tracing**: Distributed tracing for request flows
- **Alerting**: Multi-channel notifications for incidents

## Development Workflow

### Local Development
```bash
# Start dependencies
docker-compose -f docker-compose.dev.yml up -d

# Run application
uvicorn index:app --reload --port 8080
```

### Production Deployment
```bash
# Build and deploy
docker build -t ai-middleware:latest .
kubectl apply -f k8s/
```

## Common Patterns

### Request Processing
1. Authentication & authorization
2. Configuration lookup
3. Request formatting per provider
4. AI provider call with retry logic
5. Response standardization
6. Caching and metrics recording

### Error Handling
1. Service-level error catching
2. Standardized error formatting
3. Metrics recording
4. Webhook notifications
5. Client error response

### Function Calling
1. Tool validation
2. Function execution
3. Response formatting
4. Follow-up AI calls
5. Result aggregation

## Troubleshooting Quick Reference

### Common Issues
- **High Response Times**: Check cache hit rates, database connections
- **Authentication Failures**: Verify JWT configuration, API keys
- **Queue Backlog**: Monitor consumer health, scaling settings
- **Database Connections**: Check connection pool settings, replica health

### Health Checks
- **Application**: `GET /healthcheck`
- **Database**: Connection pool status
- **Queue**: Consumer status and message counts
- **Cache**: Redis cluster health

### Performance Tuning
- **App Level**: Worker count, connection pooling
- **Database**: Index optimization, query performance
- **Cache**: TTL settings, memory optimization
- **Network**: Connection keep-alive, timeout settings

## Configuration Quick Reference

### Environment Variables
```bash
# Core Settings
ENVIRONMENT=PRODUCTION
PORT=8080

# Database URLs
MONGODB_CONNECTION_URI=mongodb+srv://...
TIMESCALE_SERVICE_URL=postgresql://...
REDIS_URI=redis://...

# AI Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...

# Queue Settings
QUEUE_CONNECTIONURL=amqp://...
CONSUMER_STATUS=true
```

### Key Configuration Files
- **index.py**: Application entry point and lifecycle
- **config.py**: Environment variable configuration
- **Dockerfile**: Container definition
- **k8s/**: Kubernetes deployment manifests

This quick reference provides essential information for developers, operators, and stakeholders working with the AI Middleware System.