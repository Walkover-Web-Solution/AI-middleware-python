# Deployment and Infrastructure Architecture

## Overview

The AI Middleware system is designed for cloud-native deployment with containerization, microservices architecture, and horizontal scalability. This document outlines the infrastructure components, deployment patterns, and operational requirements.

## Infrastructure Architecture

```mermaid
graph TB
    subgraph "External Services"
        OpenAI[OpenAI API]
        Anthropic[Anthropic API]
        Google[Google Gemini API]
        Groq[Groq API]
        Mistral[Mistral API]
        OpenRouter[OpenRouter API]
        Atatus[Atatus Monitoring]
    end
    
    subgraph "Load Balancer Layer"
        LB[Load Balancer<br/>Nginx/HAProxy]
        SSL[SSL Termination]
    end
    
    subgraph "Application Layer"
        subgraph "Container Orchestration"
            K8s[Kubernetes Cluster]
        end
        
        subgraph "Application Pods"
            App1[FastAPI App 1<br/>Gunicorn + Uvicorn]
            App2[FastAPI App 2<br/>Gunicorn + Uvicorn]
            App3[FastAPI App N<br/>Gunicorn + Uvicorn]
        end
        
        subgraph "Background Workers"
            Worker1[Queue Consumer 1]
            Worker2[Queue Consumer 2]
            Worker3[Queue Consumer N]
        end
    end
    
    subgraph "Message Queue Layer"
        RabbitMQ[RabbitMQ Cluster<br/>High Availability]
        RabbitMQ_LB[RabbitMQ Load Balancer]
    end
    
    subgraph "Database Layer"
        subgraph "MongoDB Cluster"
            MongoDB_Primary[(MongoDB Primary)]
            MongoDB_Secondary1[(MongoDB Secondary)]
            MongoDB_Secondary2[(MongoDB Secondary)]
        end
        
        subgraph "PostgreSQL/TimescaleDB"
            PostgreSQL_Primary[(PostgreSQL Primary<br/>TimescaleDB Extension)]
            PostgreSQL_Replica[(PostgreSQL Read Replica)]
        end
        
        subgraph "Redis Cluster"
            Redis_Master[(Redis Master)]
            Redis_Replica[(Redis Replica)]
        end
    end
    
    subgraph "Monitoring & Logging"
        Prometheus[Prometheus<br/>Metrics Collection]
        Grafana[Grafana<br/>Dashboards]
        ElasticSearch[ElasticSearch<br/>Log Storage]
        Kibana[Kibana<br/>Log Analysis]
        AlertManager[Alert Manager<br/>Notifications]
    end
    
    subgraph "Storage"
        FileStorage[Object Storage<br/>S3/GCS/Azure Blob]
        ConfigMaps[ConfigMaps<br/>Environment Variables]
        Secrets[Kubernetes Secrets<br/>API Keys & Credentials]
    end
    
    %% Client Connections
    Client[Client Applications] --> LB
    LB --> SSL
    SSL --> K8s
    
    %% Application Layer Connections
    K8s --> App1
    K8s --> App2
    K8s --> App3
    K8s --> Worker1
    K8s --> Worker2
    K8s --> Worker3
    
    %% External API Connections
    App1 --> OpenAI
    App1 --> Anthropic
    App1 --> Google
    App1 --> Groq
    App1 --> Mistral
    App1 --> OpenRouter
    App1 --> Atatus
    
    %% Database Connections
    App1 --> MongoDB_Primary
    App1 --> PostgreSQL_Primary
    App1 --> Redis_Master
    App2 --> MongoDB_Primary
    App2 --> PostgreSQL_Primary
    App2 --> Redis_Master
    
    %% Message Queue Connections
    App1 --> RabbitMQ_LB
    Worker1 --> RabbitMQ_LB
    RabbitMQ_LB --> RabbitMQ
    
    %% Monitoring Connections
    App1 --> Prometheus
    PostgreSQL_Primary --> Prometheus
    MongoDB_Primary --> Prometheus
    Redis_Master --> Prometheus
    Prometheus --> Grafana
    Prometheus --> AlertManager
    
    %% Configuration
    K8s --> ConfigMaps
    K8s --> Secrets
    K8s --> FileStorage
```

## Container Architecture

### Docker Configuration

```dockerfile
# Production Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY req.txt /app/req.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r req.txt

# Copy application code
COPY . /app

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthcheck || exit 1

# Expose port
EXPOSE 8080

# Start application with Gunicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "--timeout", "300", "--keep-alive", "5", "index:app"]
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-middleware
  labels:
    app: ai-middleware
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-middleware
  template:
    metadata:
      labels:
        app: ai-middleware
    spec:
      containers:
      - name: ai-middleware
        image: ai-middleware:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "PRODUCTION"
        - name: MONGODB_CONNECTION_URI
          valueFrom:
            secretKeyRef:
              name: ai-middleware-secrets
              key: mongodb-uri
        - name: REDIS_URI
          valueFrom:
            secretKeyRef:
              name: ai-middleware-secrets
              key: redis-uri
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-middleware-secrets
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /healthcheck
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthcheck
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Queue Worker Deployment

```yaml
# worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-middleware-worker
  labels:
    app: ai-middleware-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-middleware-worker
  template:
    metadata:
      labels:
        app: ai-middleware-worker
    spec:
      containers:
      - name: worker
        image: ai-middleware:latest
        command: ["python", "-c"]
        args: ["from src.services.commonServices.queueService.queueService import queue_obj; import asyncio; asyncio.run(queue_obj.consume_messages())"]
        env:
        - name: CONSUMER_STATUS
          value: "true"
        - name: QUEUE_CONNECTIONURL
          valueFrom:
            secretKeyRef:
              name: ai-middleware-secrets
              key: rabbitmq-uri
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
```

## Service Configuration

### Service and Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-middleware-service
spec:
  selector:
    app: ai-middleware
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-middleware-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: tls-secret
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-middleware-service
            port:
              number: 80
```

## Database Infrastructure

### MongoDB Cluster Configuration

```yaml
# mongodb-cluster.yaml
apiVersion: mongodbcommunity.mongodb.com/v1
kind: MongoDBCommunity
metadata:
  name: ai-middleware-mongodb
spec:
  members: 3
  type: ReplicaSet
  version: "7.0.0"
  security:
    authentication:
      modes: ["SCRAM"]
  users:
    - name: ai-middleware-user
      db: admin
      passwordSecretRef:
        name: mongodb-secret
      roles:
        - name: readWriteAnyDatabase
          db: admin
  additionalMongodConfig:
    storage.wiredTiger.engineConfig.journalCompressor: zlib
    storage.wiredTiger.collectionConfig.blockCompressor: snappy
```

### PostgreSQL/TimescaleDB Configuration

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: timescale/timescaledb:latest-pg14
        env:
        - name: POSTGRES_DB
          value: ai_middleware
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

### Redis Cluster Configuration

```yaml
# redis-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --cluster-enabled
        - "yes"
        - --cluster-config-file
        - nodes.conf
        - --cluster-node-timeout
        - "5000"
        - --appendonly
        - "yes"
        ports:
        - containerPort: 6379
        - containerPort: 16379
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    
    scrape_configs:
    - job_name: 'ai-middleware'
      static_configs:
      - targets: ['ai-middleware-service:80']
      metrics_path: '/metrics'
      
    - job_name: 'postgres'
      static_configs:
      - targets: ['postgres:5432']
      
    - job_name: 'mongodb'
      static_configs:
      - targets: ['ai-middleware-mongodb:27017']
      
    - job_name: 'redis'
      static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "AI Middleware Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "AI Provider Usage",
        "type": "pie",
        "targets": [
          {
            "expr": "sum by (provider) (ai_requests_total)",
            "legendFormat": "{{provider}}"
          }
        ]
      }
    ]
  }
}
```

## Environment Configurations

### Development Environment
```bash
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=LOCAL
      - MONGODB_CONNECTION_URI=mongodb://mongo:27017
      - REDIS_URI=redis://redis:6379
    depends_on:
      - mongo
      - redis
      - postgres
      
  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
      
  postgres:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: ai_middleware
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  mongo_data:
  postgres_data:
```

### Production Environment Variables
```bash
# Production .env template
ENVIRONMENT=PRODUCTION
PORT=8080

# Database Connections
MONGODB_CONNECTION_URI=mongodb+srv://user:pass@cluster.mongodb.net/ai_middleware
TIMESCALE_SERVICE_URL=postgresql://user:pass@timescale.host:5432/ai_middleware
REDIS_URI=redis://redis.host:6379

# AI Provider Keys (Encrypted)
OPENAI_API_KEY=encrypted_key
ANTHROPIC_API_KEY=encrypted_key
GOOGLE_API_KEY=encrypted_key

# Queue Configuration
QUEUE_CONNECTIONURL=amqp://user:pass@rabbitmq.host:5672
QUEUE_NAME=ai-middleware-queue
CONSUMER_STATUS=true
PREFETCH_COUNT=10

# Security
JWT_TOKEN_SECRET=jwt_secret
ENCRYPTION_KEY=encryption_key

# Monitoring
ATATUS_LICENSE_KEY=atatus_key

# Performance
MAX_WORKERS=4
```

## Scaling and Performance

### Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-middleware-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-middleware
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Resource Requirements

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit | Storage |
|-----------|-------------|-----------|----------------|--------------|---------|
| FastAPI App | 250m | 500m | 512Mi | 1Gi | - |
| Queue Worker | 100m | 200m | 256Mi | 512Mi | - |
| MongoDB | 500m | 1000m | 1Gi | 2Gi | 100Gi |
| PostgreSQL | 500m | 1000m | 1Gi | 2Gi | 100Gi |
| Redis | 100m | 200m | 256Mi | 512Mi | 10Gi |

## Security Considerations

### Network Security
- TLS termination at load balancer
- Internal service mesh with mTLS
- Network policies for pod-to-pod communication
- VPC/subnet isolation

### Application Security
- Secret management with Kubernetes secrets
- API key encryption at rest
- JWT token validation
- Rate limiting and DDoS protection

### Database Security
- Database connection encryption
- Role-based access control
- Regular security updates
- Backup encryption

This infrastructure provides high availability, scalability, and security for the AI Middleware system while maintaining operational efficiency and cost optimization.