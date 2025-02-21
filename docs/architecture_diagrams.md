# Architecture Diagrams

## System Overview

```mermaid
graph TB
    User[User/Family] --> UI[Web Interface]
    UI --> Orchestrator[Orchestrator Agent]
    
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
        Storage --> LocalFS[Local FileSystem]
        Storage --> Database[(Database)]
        Storage --> Cache[(Redis Cache)]
    end
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant W as WebSurfer
    participant C as Coder
    participant F as FileSurfer
    participant DB as Database
    
    U->>O: Submit Trip Requirements
    activate O
    
    O->>W: Request Destination Research
    activate W
    W->>W: Search Travel Options
    W-->>O: Return Research Results
    deactivate W
    
    O->>C: Process Data & Create Plan
    activate C
    C->>C: Generate Itinerary
    C->>C: Calculate Budget
    C-->>O: Return Processed Plan
    deactivate C
    
    O->>F: Generate Documents
    activate F
    F->>DB: Store Trip Plan
    F->>F: Create PDF Reports
    F-->>O: Return Document Links
    deactivate F
    
    O-->>U: Present Complete Plan
    deactivate O
```

## Component Dependencies

```mermaid
graph TD
    subgraph "Frontend Layer"
        UI[Web Interface]
        API[API Gateway]
    end
    
    subgraph "Agent Layer"
        Orchestrator[Orchestrator Agent]
        WebSurfer[WebSurfer Agent]
        Coder[Coder Agent]
        FileSurfer[FileSurfer Agent]
    end
    
    subgraph "Service Layer"
        AuthService[Authentication]
        CacheService[Caching Service]
        LoggingService[Logging Service]
    end
    
    subgraph "Data Layer"
        DB[(Database)]
        Cache[(Redis)]
        FileStore[File Storage]
    end
    
    UI --> API
    API --> Orchestrator
    
    Orchestrator --> AuthService
    Orchestrator --> WebSurfer
    Orchestrator --> Coder
    Orchestrator --> FileSurfer
    
    WebSurfer --> CacheService
    Coder --> CacheService
    FileSurfer --> FileStore
    
    AuthService --> DB
    CacheService --> Cache
    LoggingService --> FileStore
```

## State Management

```mermaid
stateDiagram-v2
    [*] --> Initialization
    
    Initialization --> GatheringRequirements
    
    GatheringRequirements --> ResearchingDestinations
    ResearchingDestinations --> PlanningItinerary
    ResearchingDestinations --> GatheringRequirements: Insufficient Info
    
    PlanningItinerary --> CalculatingBudget
    PlanningItinerary --> ResearchingDestinations: Need More Research
    
    CalculatingBudget --> GeneratingDocuments
    CalculatingBudget --> PlanningItinerary: Budget Constraints
    
    GeneratingDocuments --> ReviewingPlan
    
    ReviewingPlan --> [*]: Plan Approved
    ReviewingPlan --> PlanningItinerary: Revisions Needed
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB[Load Balancer]
        
        subgraph "Application Cluster"
            API1[API Server 1]
            API2[API Server 2]
            Worker1[Worker 1]
            Worker2[Worker 2]
        end
        
        subgraph "Data Storage"
            Master[(Primary DB)]
            Replica[(DB Replica)]
            Redis1[(Redis Primary)]
            Redis2[(Redis Replica)]
        end
        
        subgraph "Monitoring"
            Prometheus[Prometheus]
            Grafana[Grafana]
            ELK[ELK Stack]
        end
    end
    
    Client-->LB
    LB-->API1
    LB-->API2
    API1-->Worker1
    API1-->Worker2
    API2-->Worker1
    API2-->Worker2
    
    Worker1-->Master
    Worker2-->Master
    Master-->Replica
    
    Worker1-->Redis1
    Worker2-->Redis1
    Redis1-->Redis2
    
    API1-->Prometheus
    API2-->Prometheus
    Worker1-->Prometheus
    Worker2-->Prometheus
    Prometheus-->Grafana
    
    API1-->ELK
    API2-->ELK
    Worker1-->ELK
    Worker2-->ELK
```

## Development Workflow

```mermaid
gitGraph
    commit id: "initial"
    branch develop
    checkout develop
    commit id: "feature/setup"
    branch feature/orchestrator
    commit id: "add-orchestrator"
    commit id: "test-orchestrator"
    checkout develop
    merge feature/orchestrator
    branch feature/websurfer
    commit id: "add-websurfer"
    commit id: "test-websurfer"
    checkout develop
    merge feature/websurfer
    branch feature/coder
    commit id: "add-coder"
    commit id: "test-coder"
    checkout develop
    merge feature/coder
    branch feature/filesurfer
    commit id: "add-filesurfer"
    commit id: "test-filesurfer"
    checkout develop
    merge feature/filesurfer
    checkout main
    merge develop
    commit id: "release-v1.0"
```

These diagrams provide different views of the system architecture:
1. **System Overview**: Shows the high-level components and their interactions
2. **Data Flow**: Illustrates the sequence of operations during a typical trip planning process
3. **Component Dependencies**: Details how different components depend on each other
4. **State Management**: Shows the different states of the trip planning process
5. **Deployment Architecture**: Illustrates the production environment setup
6. **Development Workflow**: Shows the Git branching strategy and development process

The diagrams can be updated as the architecture evolves or requirements change. 