# System Architecture - Complete System Overview

> [!abstract] Overview
> This document provides a comprehensive overview of how all components of the French article scraper system work together. It serves as the entry point for understanding the complete architecture, data flow, and component interactions across the entire system.

## Table of Contents
- [[#System Architecture Overview|System Architecture Overview]]
- [[#Component Integration Map|Component Integration Map]]
- [[#Data Flow Through the System|Data Flow Through the System]]
- [[#Processing Pipeline|Processing Pipeline]]
- [[#Component Interactions|Component Interactions]]
- [[#System Lifecycle|System Lifecycle]]
- [[#Operational Modes|Operational Modes]]
- [[#Quality Assurance Pipeline|Quality Assurance Pipeline]]
- [[#Performance and Monitoring|Performance and Monitoring]]
- [[#Error Handling and Recovery|Error Handling and Recovery]]
- [[#Extension Points|Extension Points]]

---

## System Architecture Overview

The French article scraper is a **modular, pipeline-based system** designed for extracting and analyzing French vocabulary from news articles. The system follows a clean architecture pattern with clear separation of concerns across six main component categories.

### High-Level Architecture

```mermaid
graph TB
    subgraph "Configuration Layer"
        CONFIG[Config System]
        CONFIG --> GLOBAL[Global Settings]
        CONFIG --> SOURCES[Source Configs]
        CONFIG --> TEXT[Text Processing]
        CONFIG --> JUNK[Junk Patterns]
    end
    
    subgraph "Processing Core"
        PROCESSOR[Core Processor]
        PROCESSOR --> SCRAPER[Scrapers]
        PROCESSOR --> PARSER[Parsers]
        PROCESSOR --> UTILS[Utils]
    end
    
    subgraph "Support Infrastructure"
        UTILS --> TEXTPROC[French Text Processor]
        UTILS --> CSVWRITER[CSV Writer]
        UTILS --> VALIDATOR[Data Validator]
        UTILS --> LOGGER[Structured Logger]
    end
    
    subgraph "Quality Assurance"
        TESTING[Testing Framework]
        TESTING --> ESSENTIAL[Essential Tests]
        TESTING --> INTEGRATION[Integration Tests]
        TESTING --> OFFLINE[Offline Tests]
    end
    
    subgraph "Data Flow"
        INPUT[News Websites / Test Data]
        OUTPUT[Daily CSV Files]
        LOGS[Structured Logs]
    end
    
    CONFIG -.-> PROCESSOR
    INPUT --> SCRAPER
    SCRAPER --> PARSER
    PARSER --> TEXTPROC
    TEXTPROC --> CSVWRITER
    CSVWRITER --> OUTPUT
    PROCESSOR --> LOGGER
    LOGGER --> LOGS
    
    TESTING --> PROCESSOR
    TESTING --> UTILS
    TESTING --> CONFIG
```

### System Components

> [!note] Six Core Component Categories
> 1. **[[01-Scrapers|Scrapers]]** - URL discovery from news homepages
> 2. **[[02-Parsers|Parsers]]** - Content extraction from article pages  
> 3. **[[03-Processor|Processor]]** - Central orchestration and pipeline management
> 4. **[[04-Testing|Testing]]** - Comprehensive test framework and quality assurance
> 5. **[[05-Utils|Utils]]** - Support infrastructure (CSV writing, text processing, validation)
> 6. **[[06-Config|Config]]** - Configuration management and system settings

---

## Component Integration Map

### Integration Architecture

```mermaid
graph TD
    A[System Startup] --> B[Config Loading]
    B --> C[Component Initialization]
    C --> D[Processing Pipeline]
    
    subgraph "Configuration Integration"
        B --> B1[Global Settings]
        B --> B2[Source Definitions]  
        B --> B3[Text Processing Rules]
        B --> B4[Junk Word Patterns]
    end
    
    subgraph "Core Processing Integration"
        D --> D1[Dynamic Class Loading]
        D1 --> D2[Scraper Instantiation]
        D1 --> D3[Parser Instantiation]
        D2 --> D4[URL Discovery]
        D3 --> D5[Content Extraction]
        D5 --> D6[Text Processing]
        D6 --> D7[Data Validation]
        D7 --> D8[CSV Output]
    end
    
    subgraph "Utils Integration"
        D6 --> U1[French Text Processor]
        D7 --> U2[Data Validator]
        D8 --> U3[CSV Writer]
        D1 --> U4[Structured Logger]
    end
    
    subgraph "Testing Integration"
        T1[Essential Tests] --> C
        T2[Integration Tests] --> D
        T3[Offline Tests] --> D4
        T4[Performance Tests] --> D6
    end
    
    U4 --> L1[Performance Logs]
    U4 --> L2[Error Logs]
    U4 --> L3[Debug Logs]
```

### Integration Patterns

> [!tip] Key Integration Mechanisms
> - **Configuration-Driven Loading**: Components loaded based on string paths in config
> - **Dependency Injection**: Parameters injected through configuration system
> - **Event-Driven Logging**: All components emit structured logs for monitoring
> - **Pipeline Processing**: Data flows through well-defined processing stages
> - **Error Propagation**: Errors handled at appropriate levels with recovery
> - **Concurrent Execution**: Thread-safe operations across all components

---

## Data Flow Through the System

### Complete Data Journey

```mermaid
sequenceDiagram
    participant User as User/Scheduler
    participant Main as Main Entry Point
    participant Config as Configuration System
    participant Processor as Core Processor
    participant Scraper as URL Scraper
    participant Parser as Article Parser
    participant TextProc as French Text Processor
    participant Validator as Data Validator
    participant CSVWriter as CSV Writer
    participant Logger as Structured Logger
    
    User->>Main: Execute system
    Main->>Config: Load all configurations
    Config->>Config: Validate settings
    Config->>Main: Return validated config
    
    Main->>Processor: Initialize with config
    Processor->>Processor: Load enabled sources
    
    loop For Each News Source
        Processor->>Config: Get source configuration
        Processor->>Processor: Dynamic class loading
        Processor->>Scraper: Instantiate scraper
        Processor->>Parser: Instantiate parser
        
        alt Live Mode
            Processor->>Scraper: Discover article URLs
            Scraper->>Scraper: HTTP requests to homepage
            Scraper->>Processor: Return URL list
            
            loop For Each URL
                Processor->>Parser: Fetch article content
                Parser->>Parser: HTTP request to article
                Parser->>Processor: Return HTML content
            end
        else Offline Mode
            Processor->>Parser: Load test data files
            Parser->>Processor: Return cached content
        end
        
        loop For Each Article
            Processor->>Parser: Parse article content
            Parser->>Parser: Extract title, text, date
            Parser->>Processor: Return structured data
            
            Processor->>Validator: Validate article data
            Validator->>Processor: Return validated data
            
            Processor->>TextProc: Process French text
            TextProc->>TextProc: Clean and tokenize
            TextProc->>TextProc: Count word frequencies
            TextProc->>TextProc: Extract contexts
            TextProc->>Processor: Return word analysis
            
            Processor->>CSVWriter: Write to daily CSV
            CSVWriter->>CSVWriter: Thread-safe file write
            CSVWriter->>Processor: Confirm write
        end
        
        Processor->>Logger: Log processing stats
    end
    
    Processor->>Main: Return completion status
    Main->>User: Display results
```

### Data Transformation Stages

> [!example] Data Transformation Pipeline
> ```
> 1. RAW INPUT DATA
>    ├── Live Mode: News website homepages → Article URLs → HTML content
>    └── Offline Mode: Cached test files → HTML content
> 
> 2. CONTENT EXTRACTION (Parsers)
>    ├── HTML parsing with BeautifulSoup
>    ├── Title extraction using CSS selectors
>    ├── Content extraction from article bodies
>    ├── Date parsing and normalization
>    └── Metadata collection
> 
> 3. DATA VALIDATION (Utils/Validator)
>    ├── Content quality assessment
>    ├── Required field validation
>    ├── Data type checking
>    ├── Length and format validation
>    └── Error filtering and logging
> 
> 4. FRENCH TEXT PROCESSING (Utils/TextProcessor)
>    ├── Text cleaning and normalization
>    ├── French accent handling (à→a, é→e)
>    ├── Stopword filtering (134 French stopwords)
>    ├── Junk pattern removal (parsing artifacts)
>    ├── Word frequency counting
>    ├── Context sentence extraction
>    └── Quality filtering (spam detection)
> 
> 5. OUTPUT GENERATION (Utils/CSVWriter)
>    ├── Daily CSV file creation (YYYY-MM-DD.csv)
>    ├── Word-based row generation
>    ├── Duplicate detection and prevention
>    ├── Thread-safe file writing
>    └── Backup and recovery mechanisms
> 
> 6. MONITORING AND LOGGING (Utils/Logger)
>    ├── Structured JSON logs for analysis
>    ├── Human-readable console output
>    ├── Performance metrics collection
>    ├── Error tracking and reporting
>    └── Component-specific log levels
> ```

---

## Processing Pipeline

### Pipeline Architecture

The system operates as a **multi-stage processing pipeline** with each stage having specific responsibilities:

```mermaid
graph LR
    subgraph "Stage 1: Discovery"
        A1[URL Discovery]
        A2[Content Retrieval]
        A3[Quality Filtering]
    end
    
    subgraph "Stage 2: Extraction"
        B1[HTML Parsing]
        B2[Content Extraction]
        B3[Metadata Collection]
    end
    
    subgraph "Stage 3: Processing"
        C1[Text Cleaning]
        C2[French Analysis]
        C3[Word Frequency]
        C4[Context Extraction]
    end
    
    subgraph "Stage 4: Validation"
        D1[Data Validation]
        D2[Quality Assessment]
        D3[Error Detection]
    end
    
    subgraph "Stage 5: Output"
        E1[CSV Generation]
        E2[File Writing]
        E3[Backup Management]
    end
    
    subgraph "Stage 6: Monitoring"
        F1[Performance Logging]
        F2[Error Tracking]
        F3[Statistics Collection]
    end
    
    A1 --> A2 --> A3 --> B1 --> B2 --> B3 --> C1 --> C2 --> C3 --> C4 --> D1 --> D2 --> D3 --> E1 --> E2 --> E3
    
    A1 -.-> F1
    B1 -.-> F1
    C1 -.-> F1
    D1 -.-> F2
    E1 -.-> F1
    E3 -.-> F3
```

### Pipeline Characteristics

> [!info] Pipeline Features
> - **Streaming Processing**: Data flows through stages without intermediate storage
> - **Error Isolation**: Failures in one article don't affect others
> - **Concurrent Execution**: Multiple articles processed simultaneously
> - **Quality Gates**: Validation at each stage ensures data quality
> - **Monitoring Integration**: Performance and error tracking throughout
> - **Graceful Degradation**: System continues despite individual failures

---

## Component Interactions

### Inter-Component Communication

```mermaid
graph TD
    subgraph "Configuration Interactions"
        C1[Config] --> |Settings| P1[Processor]
        C1 --> |Source Definitions| P1
        C1 --> |Text Processing Rules| U1[Utils]
        C1 --> |Junk Patterns| U1
    end
    
    subgraph "Core Processing Interactions"
        P1 --> |Dynamic Loading| S1[Scrapers]
        P1 --> |Dynamic Loading| P2[Parsers]
        P1 --> |Text Analysis| U1
        P1 --> |Logging| U2[Logger]
        S1 --> |URLs| P2
        P2 --> |Content| U1
    end
    
    subgraph "Utils Interactions"
        U1 --> |Processed Data| U3[CSV Writer]
        U1 --> |Validation| U4[Validator]
        U2 --> |Logs| U5[Log Files]
        U3 --> |Files| U6[Output Dir]
    end
    
    subgraph "Testing Interactions"
        T1[Testing] --> |Validates| P1
        T1 --> |Validates| S1
        T1 --> |Validates| P2
        T1 --> |Validates| U1
        T1 --> |Validates| C1
    end
    
    style C1 fill:#e1f5fe
    style P1 fill:#f3e5f5
    style U1 fill:#e8f5e8
    style T1 fill:#fff3e0
```

### Communication Patterns

> [!note] Inter-Component Communication
> - **Configuration Push**: Config system pushes settings to all components
> - **Data Pull**: Processor pulls data through the pipeline
> - **Event Broadcasting**: Logger receives events from all components
> - **Validation Requests**: Components request validation from utils
> - **Error Propagation**: Errors bubble up through the call stack
> - **Performance Reporting**: All components report metrics to logger

---

## System Lifecycle

### Complete System Execution Flow

```mermaid
stateDiagram-v2
    [*] --> Initialization
    
    state Initialization {
        [*] --> LoadConfig
        LoadConfig --> ValidateConfig
        ValidateConfig --> InitComponents
        InitComponents --> [*]
    }
    
    Initialization --> Processing
    
    state Processing {
        [*] --> SourceIteration
        
        state SourceIteration {
            [*] --> LoadSource
            LoadSource --> CheckEnabled
            CheckEnabled --> CreateComponents
            CreateComponents --> ProcessArticles
            
            state ProcessArticles {
                [*] --> DiscoverURLs
                DiscoverURLs --> ExtractContent
                ExtractContent --> ProcessText
                ProcessText --> ValidateData
                ValidateData --> WriteOutput
                WriteOutput --> [*]
            }
            
            ProcessArticles --> LogResults
            LogResults --> NextSource
            NextSource --> LoadSource
            NextSource --> [*]
        }
    }
    
    Processing --> Completion
    
    state Completion {
        [*] --> CollectStats
        CollectStats --> FinalLogging
        FinalLogging --> Cleanup
        Cleanup --> [*]
    }
    
    Completion --> [*]
    
    Processing --> ErrorHandling
    ErrorHandling --> Processing : Retry
    ErrorHandling --> Completion : Fatal Error
```

### Lifecycle Phases

> [!example] System Lifecycle Phases
> ```
> 1. INITIALIZATION PHASE
>    ├── Load global settings (OFFLINE, DEBUG)
>    ├── Load source configurations
>    ├── Load text processing rules
>    ├── Load junk word patterns
>    ├── Validate all configurations
>    ├── Initialize logging system
>    └── Setup output directories
> 
> 2. PROCESSING PHASE
>    ├── Iterate through enabled sources
>    ├── Dynamic component loading
>    ├── URL discovery or test data loading
>    ├── Concurrent article processing
>    ├── Text analysis and validation
>    ├── CSV output generation
>    └── Performance monitoring
> 
> 3. COMPLETION PHASE
>    ├── Collect processing statistics
>    ├── Generate final reports
>    ├── Clean up temporary resources
>    ├── Flush logs and buffers
>    └── Return completion status
> 
> 4. ERROR HANDLING (Throughout)
>    ├── Component initialization errors
>    ├── Network and parsing errors
>    ├── Validation and quality errors
>    ├── File system and permission errors
>    └── Recovery and graceful degradation
> ```

---

## Operational Modes

The system supports two primary operational modes with different data sources and behaviors:

### Live Mode vs Offline Mode

```mermaid
graph TD
    subgraph "Live Mode (OFFLINE=False)"
        L1[Real Website Scraping]
        L1 --> L2[HTTP Requests to Homepages]
        L2 --> L3[URL Discovery]
        L3 --> L4[Article Content Fetching]
        L4 --> L5[Real-time Processing]
        L5 --> L6[Current Data Output]
        
        L7[Network Dependencies]
        L8[Variable Execution Time]
        L9[Rate Limiting Considerations]
    end
    
    subgraph "Offline Mode (OFFLINE=True)"
        O1[Cached Test Data]
        O1 --> O2[Local File Reading]
        O2 --> O3[Consistent URL Sets]
        O3 --> O4[Cached Content Processing]
        O4 --> O5[Deterministic Processing]
        O5 --> O6[Reproducible Output]
        
        O7[No Network Dependencies]
        O8[Fast Execution ~10s]
        O9[Consistent Results]
    end
    
    MODE{System Mode} --> |OFFLINE=False| L1
    MODE --> |OFFLINE=True| O1
    
    style L1 fill:#ffebee
    style O1 fill:#e8f5e8
```

### Mode Comparison

| Aspect | Live Mode | Offline Mode |
|--------|-----------|--------------|
| **Data Source** | Live websites | Cached test files |
| **Network** | Required | Not required |
| **Execution Time** | ~60 seconds | ~10 seconds |
| **Consistency** | Variable | Deterministic |
| **Development** | Integration testing | Unit/offline testing |
| **Content** | Current articles | Fixed test articles |
| **Rate Limiting** | Required | Not applicable |
| **Error Types** | Network + parsing | Parsing only |

### Debug Mode Integration

```mermaid
graph LR
    subgraph "Debug Mode (DEBUG=True)"
        D1[Verbose Logging]
        D2[Performance Timing]
        D3[Component Tracing]
        D4[Error Details]
        D5[Processing Steps]
    end
    
    subgraph "Production Mode (DEBUG=False)"
        P1[Minimal Logging]
        P2[Essential Metrics]
        P3[Error Summary]
        P4[Optimized Performance]
    end
    
    DEBUG{Debug Setting} --> |DEBUG=True| D1
    DEBUG --> |DEBUG=False| P1
    
    D1 --> D2 --> D3 --> D4 --> D5
    P1 --> P2 --> P3 --> P4
    
    style D1 fill:#fff3e0
    style P1 fill:#e8f5e8
```

---

## Quality Assurance Pipeline

### Multi-Layer Quality Assurance

```mermaid
graph TD
    subgraph "Configuration Quality"
        Q1[Config Validation]
        Q2[Schema Checking]
        Q3[Default Fallbacks]
    end
    
    subgraph "Data Quality"
        Q4[Input Validation]
        Q5[Content Assessment]
        Q6[Spam Detection]
        Q7[French Language Validation]
    end
    
    subgraph "Processing Quality"
        Q8[Pipeline Monitoring]
        Q9[Error Rate Tracking]
        Q10[Performance Bounds]
    end
    
    subgraph "Output Quality"
        Q11[CSV Validation]
        Q12[Duplicate Detection]
        Q13[Data Integrity Checks]
    end
    
    subgraph "Testing Quality"
        Q14[Essential Tests (9)]
        Q15[Integration Tests (8)]
        Q16[Offline Tests (6)]
        Q17[Performance Tests]
    end
    
    Q1 --> Q4 --> Q8 --> Q11 --> Q14
    Q2 --> Q5 --> Q9 --> Q12 --> Q15
    Q3 --> Q6 --> Q10 --> Q13 --> Q16
    Q7 --> Q17
    
    style Q14 fill:#e8f5e8
    style Q15 fill:#e3f2fd
    style Q16 fill:#fff3e0
    style Q17 fill:#fce4ec
```

### Quality Metrics

> [!warning] Quality Assurance Metrics
> - **Configuration Validation**: 100% config validation before startup
> - **Data Quality**: Multi-stage validation with spam detection
> - **Processing Success Rate**: Target >80% article processing success
> - **Test Coverage**: 23 tests covering all major components
> - **Error Recovery**: Graceful handling of all error types
> - **Performance Bounds**: Processing time and memory usage monitoring

---

## Performance and Monitoring

### Performance Architecture

```mermaid
graph TD
    subgraph "Performance Monitoring"
        M1[Execution Time Tracking]
        M2[Memory Usage Monitoring]
        M3[Throughput Measurement]
        M4[Error Rate Tracking]
        M5[Resource Utilization]
    end
    
    subgraph "Logging and Metrics"
        L1[Structured JSON Logs]
        L2[Human-Readable Console]
        L3[Performance Logs]
        L4[Error Logs]
        L5[Component-Specific Logs]
    end
    
    subgraph "Optimization Points"
        O1[Concurrent Processing]
        O2[Thread-Safe Operations]
        O3[Memory Management]
        O4[Efficient Algorithms]
        O5[Caching Strategies]
    end
    
    M1 --> L1
    M2 --> L2
    M3 --> L3
    M4 --> L4
    M5 --> L5
    
    L1 --> O1
    L2 --> O2
    L3 --> O3
    L4 --> O4
    L5 --> O5
```

### Performance Characteristics

> [!info] System Performance Metrics
> - **Live Mode**: ~60 seconds for 4 sources, 8 articles each
> - **Offline Mode**: ~10 seconds for same workload  
> - **Memory Usage**: ~50-100MB typical, ~200MB peak
> - **Concurrency**: 3-4 concurrent URLs per source
> - **Throughput**: ~0.5-1 articles per second in live mode
> - **Success Rate**: >80% article processing success rate
> - **File I/O**: Thread-safe CSV writing with backup/recovery

---

## Error Handling and Recovery

### Comprehensive Error Strategy

```mermaid
graph TD
    subgraph "Error Categories"
        E1[Configuration Errors]
        E2[Network Errors]
        E3[Parsing Errors]
        E4[Validation Errors]
        E5[File System Errors]
        E6[Resource Errors]
    end
    
    subgraph "Recovery Strategies"
        R1[Fail Fast]
        R2[Retry with Backoff]
        R3[Graceful Degradation]
        R4[Fallback Defaults]
        R5[Error Isolation]
        R6[Circuit Breakers]
    end
    
    subgraph "Error Handling"
        H1[Structured Logging]
        H2[Context Preservation]
        H3[Stack Trace Capture]
        H4[Error Aggregation]
        H5[Recovery Reporting]
    end
    
    E1 --> R1 --> H1
    E2 --> R2 --> H2
    E3 --> R3 --> H3
    E4 --> R4 --> H4
    E5 --> R5 --> H5
    E6 --> R6 --> H1
```

### Error Recovery Matrix

| Error Type | Recovery Strategy | Impact | Recovery Time |
|------------|------------------|---------|---------------|
| **Config Invalid** | Fail fast + defaults | High | Immediate |
| **Network Timeout** | Retry + circuit breaker | Medium | 30-60s |
| **Parse Failure** | Skip article + continue | Low | Immediate |
| **Validation Error** | Log + discard | Low | Immediate |
| **File Permission** | Backup restore | Medium | 5-10s |
| **Memory Exhaustion** | Reduce batch size | High | 10-30s |

---

## Extension Points

The system is designed for extensibility through well-defined extension points:

### Adding New Components

```mermaid
graph TD
    subgraph "New News Source"
        N1[Create Scraper Class]
        N2[Create Parser Class]
        N3[Add to Configuration]
        N4[Add Test Data]
        N5[Update Tests]
    end
    
    N1 --> N2 --> N3 --> N4 --> N5
```

### Extension Guidelines

> [!tip] Extension Best Practices
> 1. **Follow Existing Patterns**: Use established interfaces and conventions
> 2. **Add Configuration**: Make extensions configurable and optional
> 3. **Include Tests**: Add comprehensive tests for new functionality
> 4. **Update Documentation**: Document new components and their usage
> 5. **Maintain Compatibility**: Ensure changes don't break existing functionality
> 6. **Add Validation**: Include appropriate validation for new data types
> 7. **Consider Performance**: Monitor impact on system performance

### Current System Extension

> [!example] How New Sources Can Be Added
> The system is designed to support additional news sources following the established pattern of the current 4 sources (Slate.fr, FranceInfo.fr, TF1 Info, Depeche.fr):
> 
> 1. Create scraper class following existing pattern
> 2. Create parser class with site-specific selectors  
> 3. Add configuration to website_parser_scrapers_config.py
> 4. Add test data to test_data/raw_url_soup/
> 5. Update tests with new source validation

---

## Conclusion

The French article scraper system represents a **well-architected, modular solution** that effectively combines six specialized component categories into a cohesive, high-performance system for French language content analysis.

**System Strengths**:
- ✅ **Modular Architecture**: Clear separation of concerns with well-defined interfaces
- ✅ **Configuration-Driven**: Highly configurable without code changes
- ✅ **Quality Assurance**: Multi-layer validation and comprehensive testing
- ✅ **Performance Optimized**: Concurrent processing with monitoring and optimization
- ✅ **Error Resilient**: Comprehensive error handling and recovery mechanisms
- ✅ **Extensible Design**: Easy to add new sources, formats, and functionality
- ✅ **Production Ready**: Robust logging, monitoring, and operational features

**Technical Excellence**:
- **Pipeline Architecture**: Streaming data processing with quality gates
- **Concurrent Processing**: Thread-safe operations with resource management
- **French Language Specialization**: Optimized for French text analysis
- **Dual Mode Operation**: Seamless switching between live and offline processing
- **Comprehensive Testing**: 23 tests covering all major functionality
- **Advanced Logging**: Structured JSON logs with human-readable console output

**Integration Benefits**:
- **Developer Experience**: Clear documentation and easy debugging
- **Operational Reliability**: Production-ready with monitoring and error handling
- **Maintainability**: Well-structured code with comprehensive documentation
- **Extensibility**: Easy to add new sources and functionality
- **Quality Assurance**: Multiple validation layers ensure data integrity

This comprehensive system architecture enables reliable, scalable French content analysis while maintaining high code quality and providing excellent developer experience for ongoing maintenance and enhancement.