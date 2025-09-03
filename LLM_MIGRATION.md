# LLM Stack Migration Guide

## 🚨 **IMPORTANT: Host-based Ollama Setup (GPU Enabled)**

**UPDATE: Ollama now runs on the host machine to enable GPU acceleration.**

### Quick Setup
1. **Install Ollama on your host machine**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull required model**:
   ```bash
   ollama pull gemma3:1b
   ```

3. **Start Ollama server** (must be running before starting Docker services):
   ```bash
   ollama serve  # Runs on localhost:11434
   ```

4. **Start Docker services**:
   ```bash
   docker-compose up --build
   ```

### Why This Change?
- **GPU Access**: Docker containers cannot access host GPU, limiting inference performance
- **Better Performance**: Direct host access enables CUDA/GPU acceleration
- **Simplified Setup**: No container management for Ollama service

---

This document outlines the migration from Hugging Face to a multi-provider LLM stack (Ollama + OpenAI + Gemini).

## Changes Made

### 1. LLM Provider Architecture

**Replaced**: Single HuggingFace provider  
**With**: Multi-provider system with automatic fallback

- **Ollama (Default)**: Local gemma3:1b model for privacy and cost efficiency
- **OpenAI**: Cloud-based GPT models for high-quality responses
- **Gemini**: Google's AI models with integrated web search capabilities

### 2. Key Components Added

#### LLM Router (`app/services/llm_clients.py`)
- Automatic provider selection based on availability
- Graceful fallback to next provider if primary fails
- Centralized configuration via `LLM_PREFERENCE` environment variable

#### Web Search Tool (`app/services/web_search.py`)
- Tavily-powered web search for real-time information
- Company research capabilities
- Industry trend analysis
- Job market insights

#### Enhanced CrewAI Agents
All agents now support LLM-powered analysis:
- **SkillsAnalysisAgent**: Intelligent skills extraction and categorization
- **CompensationAnalysisAgent**: Market-aware salary analysis with web research
- **QualityAssessmentAgent**: AI-powered job posting quality assessment

### 3. Configuration Changes

#### Environment Variables (Updated `.env.example`)
```bash
# Removed
HUGGING_FACE_API_KEY=your_hugging_face_api_key

# Updated for host-based Ollama
LLM_PREFERENCE=ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash
OLLAMA_HOST=http://host.docker.internal:11434  # Points to host machine
OLLAMA_PORT=11434
TAVILY_API_KEY=your_tavily_api_key
```

#### Docker Configuration
- **Removed**: Ollama Docker service and persistent volume
- **Updated**: All services now connect to host-based Ollama via `host.docker.internal:11434`
- **Benefit**: Enables GPU acceleration for inference

### 4. Files Modified

#### Core LLM System
- `app/services/llm_clients.py` - Completely rewritten with new providers
- `app/services/persona_llm.py` - Updated to use LLM router
- `app/core/config.py` - Removed HF config, added LLM routing config

#### CrewAI Integration  
- `app/services/crewai_job_review.py` - Enhanced agents with LLM capabilities
- `app/services/web_search.py` - New web search tool for agents

#### Infrastructure
- `docker-compose.yml` - Removed Ollama service, updated environment variables to point to host
- `app/core/config.py` - Updated default Ollama host to localhost
- `.env.example` - Updated OLLAMA_HOST to use host.docker.internal

#### Documentation & Tests
- `README.md` - Updated with new LLM configuration instructions
- `test_llm_router.py` - New tests for LLM routing functionality
- `test_web_search.py` - New tests for web search capabilities
- `test_evaluation_pipeline.py` - Updated to use new providers

## Migration Benefits

### Reliability
- **Automatic Fallback**: If Ollama is unavailable, system falls back to OpenAI or Gemini
- **Provider Diversity**: Reduces single-point-of-failure risks

### Performance
- **Local Processing**: Ollama runs locally for fast, private inference
- **Smart Routing**: Most suitable provider selected based on availability and needs

### Capabilities  
- **Web Search**: Agents can now access real-time information
- **Market Intelligence**: Compensation analysis includes current market data
- **Quality Assessment**: AI-powered job posting quality evaluation

### Cost Optimization
- **Local Default**: Primary processing uses free local Ollama instance
- **Cloud Fallback**: Paid APIs used only when needed
- **Efficient Usage**: Targeted prompts minimize token consumption

## Usage Examples

### Basic LLM Usage
```python
from app.services.llm_clients import LLMRouter

router = LLMRouter()  # Uses default preferences
response = router.generate("Analyze this job posting...")
```

### CrewAI Enhanced Analysis
```python
from app.services.crewai_job_review import get_crewai_job_review_service

service = get_crewai_job_review_service()
analysis = await service.analyze_job(job_data)

# Analysis now includes:
# - LLM-powered skills extraction
# - Market-aware compensation insights
# - AI quality assessment
# - Company research via web search
```

### Web Search for Agents
```python
from app.services.web_search import get_web_search_tool

search = get_web_search_tool()
company_info = search.search_company("OpenAI")
market_trends = search.search_job_market("Software Engineer", "San Francisco")
```

## Provider Configuration

### Ollama Setup (Default - Host-based)
```bash
# Install Ollama on host machine (enables GPU access)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required model
ollama pull gemma3:1b

# Start Ollama server (must be running before Docker services)
ollama serve  # Runs on localhost:11434
```

### OpenAI Setup
```bash
export OPENAI_API_KEY="sk-..."
```

### Gemini Setup  
```bash
export GEMINI_API_KEY="AIza..."
```

### Web Search Setup
```bash
export TAVILY_API_KEY="tvly-..."
```

## Health Monitoring

Check provider status at `/health` endpoint:
```json
{
  "data": {
    "dependencies": {
      "llm_providers": {
        "preference": "ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash",
        "available": [
          {"provider": "ollama", "model": "gemma3:1b", "available": true},
          {"provider": "openai", "model": "gpt-4o-mini", "available": true},
          {"provider": "gemini", "model": "gemini-1.5-flash", "available": false}
        ]
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

**Ollama Not Available**  
- Ensure Ollama is installed and running on host: `ollama serve`
- Check if model is available: `ollama list`
- Verify host connection from Docker: Test `host.docker.internal:11434` accessibility

**OpenAI API Errors**
- Verify API key: `echo $OPENAI_API_KEY`
- Check quotas in OpenAI dashboard

**No LLM Providers Available**
- System falls back to rule-based analysis
- Check health endpoint for provider status

### Model Storage
Ollama models are now stored on the host machine (not in Docker volumes):
```bash
# Models stored in host directory
~/.ollama/models/

# View available models on host
ollama list
```

## Backward Compatibility

- **API Surface**: All existing endpoints remain unchanged
- **Response Format**: Enhanced with new fields, existing fields preserved  
- **Graceful Degradation**: Falls back to rule-based analysis if all LLM providers fail

## Performance Considerations

- **First Run**: Ollama downloads gemma3:1b (~2GB) on initial startup
- **Memory Usage**: Ollama requires ~4GB RAM for gemma3:1b
- **Startup Time**: Allow 60-120 seconds for Ollama service to be ready

## Security Notes

- **Local Processing**: Ollama keeps sensitive data on-premises
- **API Keys**: Store securely in environment variables, not in code
- **Network**: Ollama service only accessible within Docker network by default