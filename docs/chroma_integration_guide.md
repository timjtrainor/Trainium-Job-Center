# ChromaDB Integration Guide for CrewAI

This guide explains how to use the enhanced ChromaDB integration with CrewAI agents for Retrieval Augmented Generation (RAG) functionality.

## Overview

The ChromaDB integration provides a comprehensive, extensible system for managing vector databases that enhance CrewAI agent capabilities with contextual information. The system supports multiple collection types and provides easy-to-use tools for agents to access relevant data.

## Architecture

### Core Components

1. **ChromaManager** (`app/services/chroma_manager.py`)
   - Manages multiple ChromaDB collections
   - Handles document chunking and embedding
   - Provides search and retrieval functionality

2. **ChromaIntegrationService** (`app/services/chroma_integration_service.py`)
   - High-level service for CrewAI workflows
   - Specialized methods for different content types
   - Context preparation for RAG

3. **Enhanced ChromaDB Tools** (`app/services/crewai/tools/chroma_search.py`)
   - CrewAI-compatible tools for vector search
   - Collection-specific search functions
   - Cross-collection search capabilities

### Collection Types

The system supports multiple predefined collection types:

- `job_postings` - Job posting documents for analysis and matching
- `company_profiles` - Company information and culture analysis  
- `career_brand` - Personal career branding and positioning document
- `interview_feedback` - Interview experiences and feedback (future use)
- `market_insights` - Industry and market analysis (future use)
- `technical_skills` - Technical documentation and skill assessments (future use)
- `documents` - Generic document storage
- `career_paths` - Holds research on candidate career trajectories, required skills, and industry trends.
- `job_search_stategies` Stores tactics, frameworks, and best practices for effective job hunting

## Quick Start

### 1. Initialize ChromaDB Collections

The system automatically initializes default collections on application startup. You can also manually initialize:

```bash
curl -X POST "http://localhost:8000/chroma-manager/initialize"
```

### 2. Upload Documents

#### Job Postings
```bash
curl -X POST "http://localhost:8000/chroma-manager/job-posting" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "company": "TechCorp",
    "description": "We are looking for an experienced Python developer...",
    "location": "San Francisco, CA",
    "skills": ["Python", "Django", "PostgreSQL"],
    "experience_level": "Senior"
  }'
```

#### Company Profiles
```bash
curl -X POST "http://localhost:8000/chroma-manager/company-profile" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp",
    "description": "Leading technology company...",
    "industry": "Software",
    "size": "1000-5000 employees",
    "culture_info": "Fast-paced, innovative environment",
    "benefits": ["Health insurance", "Remote work", "Stock options"]
  }'
```

### 3. Search Collections

```bash
curl -X POST "http://localhost:8000/chroma-manager/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer machine learning",
    "collections": ["job_postings", "company_profiles"],
    "n_results": 5
  }'
```

## Using ChromaDB Tools in CrewAI Agents

### Basic Search Tool

```python
from app.services.crewai.tools.chroma_search import chroma_search

@agent
def research_agent(self) -> Agent:
    return Agent(
        role="Job Market Researcher",
        goal="Research job market trends and opportunities",
        tools=[chroma_search]
    )
```

### Specialized Tools

```python
from app.services.crewai.tools.chroma_search import (
    search_job_postings,
    search_company_profiles,
    contextual_job_analysis
)

@agent
def job_analyst(self) -> Agent:
    return Agent(
        role="Job Opportunity Analyst", 
        goal="Analyze job opportunities and company fit",
        tools=[
            search_job_postings,
            search_company_profiles,
            contextual_job_analysis
        ]
    )
```

### Example Agent Task Using ChromaDB

```python
@task
def market_research_task(self) -> Task:
    return Task(
        description="""
        Research the job market for {{job_title}} positions at {{company_name}}.
        Use the chroma search tools to find relevant job postings and company information.
        Provide insights on:
        1. Similar job requirements in the market
        2. Company culture and values
        3. Competitive landscape
        """,
        expected_output="Comprehensive market research report with insights and recommendations",
        agent=self.research_agent(),
        tools=[search_job_postings, search_company_profiles]
    )
```

## Extending for New Use Cases

### 1. Register New Collection Type

```python
from app.services.chroma_manager import get_chroma_manager, ChromaCollectionConfig, CollectionType

# Define new collection type
class MyCollectionType(Enum):
    INTERVIEW_FEEDBACK = "interview_feedback"

# Register configuration
manager = get_chroma_manager()
config = ChromaCollectionConfig(
    name="interview_feedback",
    collection_type=MyCollectionType.INTERVIEW_FEEDBACK,
    description="Interview feedback and experiences",
    chunk_size=400,
    chunk_overlap=50,
    metadata_schema={
        "interview_type": "str",
        "company": "str",
        "position": "str", 
        "outcome": "str"
    }
)
manager.register_collection_config(config)
```

### 2. Create Specialized Tool

```python
from crewai.tools import tool
from app.services.crewai.tools.chroma_search import chroma_search

@tool
def search_interview_feedback(query: str, n_results: int = 5) -> str:
    """Search for interview feedback and experiences."""
    return chroma_search(query, "interview_feedback", n_results)
```

### 3. Add Service Method

```python
# In ChromaIntegrationService
async def add_interview_feedback(
    self,
    company: str,
    position: str,
    feedback_text: str,
    interview_type: str = "",
    outcome: str = ""
) -> ChromaUploadResponse:
    """Add interview feedback to the collection."""
    metadata = {
        "company": company,
        "position": position,
        "interview_type": interview_type,
        "outcome": outcome
    }
    
    return await self.manager.upload_document(
        collection_name="interview_feedback",
        title=f"{company} - {position} Interview",
        document_text=feedback_text,
        metadata=metadata,
        tags=["interview", company.lower(), position.lower()]
    )
```

## API Endpoints

### Collection Management

- `GET /chroma-manager/status` - Get system status
- `GET /chroma-manager/collections` - List all collections
- `GET /chroma-manager/collection-types` - List registered collection types
- `POST /chroma-manager/initialize` - Initialize default collections
- `DELETE /chroma-manager/collection/{name}` - Delete a collection

### Document Upload

- `POST /chroma-manager/job-posting` - Upload job posting
- `POST /chroma-manager/company-profile` - Upload company profile  
- `POST /chroma-manager/career-brand` - Upload career brand document
- `POST /chroma-manager/bulk-job-postings` - Bulk upload job postings

### Search and Retrieval

- `POST /chroma-manager/search` - Search across collections
- `POST /chroma-manager/prepare-rag-context` - Prepare RAG context for CrewAI

## Best Practices

### 1. Collection Design

- Use descriptive collection names that reflect their purpose
- Define clear metadata schemas for consistency
- Choose appropriate chunk sizes based on content type
- Use meaningful tags for better organization

### 2. Search Optimization

- Use specific queries rather than generic terms
- Combine multiple collections for comprehensive context
- Limit results to avoid overwhelming agents with too much data
- Include relevant metadata in search results

### 3. Agent Integration

- Provide clear tool descriptions for agents
- Use specialized tools rather than generic search when possible
- Handle search failures gracefully in agent workflows
- Cache frequently accessed information when appropriate

### 4. Performance Considerations

- Monitor collection sizes and performance
- Use appropriate embedding models for your use case
- Consider batch uploads for large datasets
- Implement proper error handling and retries

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Failed**
   - Check Docker container status: `docker ps | grep chromadb`
   - Verify environment variables: `CHROMA_URL`, `CHROMA_PORT`
   - Check container logs: `docker logs trainium_chromadb`

2. **Embedding Model Mismatch**
   - Collections created with different embedding models are incompatible
   - Delete and recreate collections or use different collection names
   - Check `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL` settings

3. **Search Returns No Results**
   - Verify documents exist: `GET /chroma-manager/collections`
   - Check collection names in search requests
   - Ensure embedding models match between upload and search

4. **Agent Tools Not Working**
   - Verify tools are properly imported and assigned to agents
   - Check ChromaDB service initialization in application startup
   - Review agent tool configuration and permissions

### Monitoring

Use the status endpoint to monitor system health:

```bash
curl http://localhost:8000/chroma-manager/status
```

This returns information about:
- Total collections and document counts
- Registered collection configurations  
- Collection metadata and health status

## Future Enhancements

The ChromaDB integration is designed for extensibility. Planned enhancements include:

- **Semantic Similarity Scoring** - Advanced relevance ranking
- **Multi-modal Embeddings** - Support for images and other media
- **Collection Versioning** - Track document changes over time
- **Advanced Filtering** - Complex metadata-based search filters
- **Real-time Updates** - Live document synchronization
- **Performance Analytics** - Search performance monitoring

For questions or support, refer to the application logs or contact the development team.