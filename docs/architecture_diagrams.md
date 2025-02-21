# Architecture Diagrams

## System Overview

```mermaid
graph TB
    User[User/Family] --> API[FastAPI Interface]
    API --> Orchestrator[Orchestrator Agent]
    
    subgraph "Agent System"
        Orchestrator --> WebSurfer[WebSurfer Agent]
        Orchestrator --> Coder[Coder Agent]
        Orchestrator --> FileSurfer[FileSurfer Agent]
        
        WebSurfer --> ExternalAPIs[External APIs]
        Coder --> DataProcessing[Data Processing]
        FileSurfer --> Storage[Storage System]
    end
    
    subgraph "External Services"
        ExternalAPIs --> TravelAPI[Travel APIs]
        ExternalAPIs --> WeatherAPI[Weather APIs]
        ExternalAPIs --> MapsAPI[Maps APIs]
    end
    
    subgraph "Storage Layer"
        subgraph "Primary Storage"
            PostgreSQL[(PostgreSQL DB)]
            style PostgreSQL fill:#f9f,stroke:#333,stroke-width:2px
        end
        
        subgraph "Caching Layer"
            Redis[(Redis Cache)]
            style Redis fill:#bbf,stroke:#333,stroke-width:2px
        end
        
        subgraph "File Storage"
            FileSystem[Local FileSystem]
            style FileSystem fill:#bfb,stroke:#333,stroke-width:2px
        end
        
        Storage --> PostgreSQL
        Storage --> Redis
        Storage --> FileSystem
    end

    subgraph "Monitoring"
        API --> HealthChecks[Health Checks]
        HealthChecks --> ServiceStatus[Service Status]
        ServiceStatus --> PostgreSQL
        ServiceStatus --> Redis
    end

    classDef implemented fill:#9f9,stroke:#333,stroke-width:2px;
    classDef inProgress fill:#ff9,stroke:#333,stroke-width:2px;
    classDef planned fill:#f99,stroke:#333,stroke-width:2px;
    
    class PostgreSQL implemented;
    class Redis inProgress;
    class FileSystem planned;
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant O as Orchestrator
    participant W as WebSurfer
    participant DB as PostgreSQL
    participant R as Redis
    
    U->>API: Submit Trip Requirements
    API->>DB: Validate User & Session
    API->>O: Forward Request
    
    O->>R: Check Cache
    O->>W: Request Data Collection
    activate W
    W->>W: Collect Travel Data
    W-->>O: Return Results
    deactivate W
    
    O->>DB: Store Trip Data
    O->>R: Update Cache
    O-->>API: Return Response
    API-->>U: Present Results
```

## Component Dependencies

```mermaid
graph TD
    subgraph "API Layer"
        FastAPI[FastAPI]
        Endpoints[API Endpoints]
        Health[Health Checks]
    end
    
    subgraph "Agent Layer"
        Base[Base Agent]
        Orchestrator[Orchestrator]
        WebSurfer[WebSurfer]
        TaskSystem[Task System]
    end
    
    subgraph "Service Layer"
        Config[Configuration]
        Logging[Logging Service]
        Cache[Redis Cache]
    end
    
    subgraph "Data Layer"
        Models[SQLAlchemy Models]
        Migrations[Alembic]
        PostgreSQL[(PostgreSQL)]
    end
    
    FastAPI --> Endpoints
    FastAPI --> Health
    
    Endpoints --> Orchestrator
    Orchestrator --> Base
    WebSurfer --> Base
    Orchestrator --> TaskSystem
    
    Base --> Config
    Base --> Logging
    TaskSystem --> Cache
    
    Endpoints --> Models
    Models --> PostgreSQL
    Migrations --> PostgreSQL
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Environment"
        API[FastAPI App]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        
        API --> DB
        API --> Cache
    end
    
    subgraph "Health Monitoring"
        Health[Health Checks]
        Services[Service Status]
        
        Health --> Services
        Services --> DB
        Services --> Cache
    end
    
    Client-->API
    Health-->API
```

## Development Workflow

```mermaid
gitGraph
    commit id: "initial"
    branch develop
    checkout develop
    commit id: "project-setup"
    commit id: "docker-setup"
    commit id: "database-models"
    commit id: "base-agent"
    commit id: "orchestrator"
    commit id: "health-checks"
    branch feature/websurfer
    commit id: "init-websurfer"
    checkout develop
    merge feature/websurfer
    branch feature/redis-cache
    commit id: "init-redis"
```

These diagrams provide different views of the system architecture:
1. **System Overview**: Shows the current high-level components and their interactions
2. **Data Flow**: Illustrates the sequence of operations during a typical trip planning process
3. **Component Dependencies**: Details how different components depend on each other
4. **Deployment Architecture**: Shows the current Docker environment setup
5. **Development Workflow**: Reflects our current Git branching strategy and progress

The diagrams will be updated as we implement new features and components. 