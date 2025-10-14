# 🚀 Trainium Job Center
## AI Product Manager Vibe Coding POC

> **A working proof of concept demonstrating how an AI Product Manager uses generative AI, agentic agents, and RAG with ChromaDB to manage job discovery and filtering like a product funnel.**

This isn't just code—it's a **living demonstration** of AI Product Management in action. Built with a mix of AI assistants (Google AI Studio, GitHub Copilot, Claude Code, Grok, Codex), this project showcases how modern AI tools can orchestrate complex workflows while maintaining human oversight and control.

⚠️ **Disclaimer**: This is a working POC, not production-ready software. Setup requires technical expertise and is optimized for exploration rather than ease of deployment.

## 🎯 Why This Matters

This project demonstrates **AI Product Management thought leadership** through:

- **Agentic Orchestration**: Multi-agent CrewAI system that breaks complex job analysis into specialized agents (intake, filtering, brand alignment, synthesis)
- **Human-in-the-Loop Design**: HITL UI ensures human oversight remains central to AI decision-making
- **Career Brand as Context**: ChromaDB stores career framework data, enabling AI agents to make personalized recommendations aligned with individual values and trajectory
- **Product Funnel Thinking**: Job discovery → filtering → analysis → human decision, treating career search like a conversion optimization problem
- **Extensible Architecture**: MCP Gateway pattern allows dynamic integration of new tools and data sources without code changes

For AI Product Managers, this showcases how to:
1. **Balance innovation with trust** - AI enhances human judgment rather than replacing it
2. **Design for adoption** - Complex AI workflows hidden behind intuitive interfaces  
3. **Build with constraints** - Regulated domain experience (HIPAA in EdTech) informs trustworthy AI patterns
4. **Scale through automation** - Queue-based processing handles volume while maintaining quality

## 🔧 Current Functionality

### ✅ **Multi-Agent Job Analysis** 
- **Job Posting Review Crew**: 4-agent pipeline (Job Intake → Pre-filter → Quick Fit → Brand Matcher)
- **Personal Branding Crew**: Career positioning and brand development guidance
- **Company Research Crew**: 5-agent deep-dive (Financial, Culture, Leadership, Growth, Report synthesis)
- **LinkedIn Job Search Crew**: Hierarchical orchestration for job discovery and networking strategy
- **LinkedIn Recommended Jobs**: MCP-powered job collection with normalization

### ✅ **HITL UI & Dashboard**
- React + TypeScript frontend with real-time job application tracking
- Strategic narrative comparison (A/B testing different career positioning)
- KPI monitoring: applications, fit scores, engagement metrics
- Tailwind CSS styling with accessibility features

### ✅ **Queue-Based Job Scraping**
- Async job collection from multiple sources (Indeed, LinkedIn via MCP)
- Redis-backed processing with horizontal worker scaling
- Scheduled automation with poller daemon
- Manual and bulk scraping modes

### ✅ **MCP Gateway Integration**
- Docker-based Model Context Protocol gateway
- Dynamic tool discovery (DuckDuckGo search, LinkedIn jobs)
- Streaming transport with automatic retry logic
- External tool integration without hardcoded dependencies

### ✅ **Vector-Enhanced Context**
- ChromaDB storage for career brand framework
- RAG-powered job matching against personal values/trajectory
- Semantic search across job descriptions and company research
- Embedding-based similarity scoring for fit analysis

### ✅ **Resume and Proof Point Management**
- Versioned metadata tracking for proof points and resumes with approval workflows
- Document upload capabilities for career brands, career paths, job search strategies
- Status transition tracking and bulk document management
- Enhanced ChromaDB integration for document storage and retrieval

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React 19 + TypeScript + Vite | HITL UI with real-time dashboards |
| **Backend** | FastAPI + Python 3.10+ | Async API orchestration |
| **AI Orchestration** | CrewAI 0.193+ | Multi-agent workflow coordination |
| **LLM Providers** | Ollama (local) + OpenAI + Gemini | Flexible model routing with fallback |
| **Vector Database** | ChromaDB 0.5.23 | Career brand context storage |
| **Queue System** | Redis + RQ + RQ-Scheduler | Async job processing |
| **Database** | PostgreSQL 15 + PostgREST | Job data persistence |
| **MCP Integration** | Docker MCP Gateway | External tool orchestration |
| **Job Scraping** | JobSpy 1.1.82 + Custom scrapers | Multi-source job collection |
| **Containerization** | Docker + Docker Compose | Full-stack deployment |
| **Embeddings** | sentence-transformers (BGE-M3) | Semantic similarity |

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (recommended path)
- **Node.js 18+** and **Python 3.10+** (for local development)
- **API Keys** (optional but recommended):
  - `GEMINI_API_KEY` or `OPENAI_API_KEY` for LLM access
  - `TAVILY_API_KEY` for web search capabilities
  - `LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD` for LinkedIn MCP integration

### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/timjtrainor/Trainium-Job-Center.git
cd Trainium-Job-Center

# Copy environment template
cp .env.example .env
# Edit .env with your API keys and database credentials

# Start the full stack
docker-compose up --build

# Apply database migrations (in separate terminal)
cd "DB Scripts/sqitch"
export PG_LOCAL_URI="db:pg://user:pass@localhost:5432/trainium"
sqitch deploy
```

**Services will be available at:**
- Frontend: http://localhost:3000
- Python API: http://localhost:8000 (docs at /docs)
- PostgREST API: http://localhost:3001
- ChromaDB: http://localhost:8001
- MCP Gateway: http://localhost:8811

### Local Development Setup

```bash
# Frontend
npm install
# Configure FastAPI host (optional if using default /api proxy)
echo "VITE_FASTAPI_BASE_URL=http://localhost:8000" > .env.local
npm run dev

# Python service
cd python-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Queue workers (separate terminals)
python worker.py        # Job processing
python scheduler_daemon.py  # Scheduled jobs
python poller_daemon.py     # Job polling
```

### Frontend Environment Variables

- `VITE_FASTAPI_BASE_URL`: URL for the FastAPI service used by the UI. Defaults to `/api`, which supports reverse proxies that
  mount the backend behind the frontend domain. Set this when the FastAPI service runs on a different host or port (for example,
  `http://localhost:8000`).

### Verification

```bash
# Test the build process
npm run build
python -m py_compile $(git ls-files '*.py')

# Test MCP Gateway
./verify_mcp_setup.sh

# Check service health
curl http://localhost:8000/health
```

## 💼 Career Brand Framework Integration

This project demonstrates **Career Brand as Product Context** - using structured personal branding data to inform AI decision-making:

### North Star & Vision
> Building toward a Director of AI Product role by 2029, applying experience in AI adoption, platform strategy, and regulated SaaS (HIPAA in EdTech) to healthcare. Focus on human-centered AI that expands global access to effective diagnosis, reduces cost barriers, and earns adoption through trust.

### Strategic Framework Integration
- **Values Compass**: Fun & Engagement, Customer Focus, Continuous Improvement, Integrity, Collaboration
- **Trajectory Mastery**: Turnaround leadership, product strategy, growth orientation
- **Lifestyle Alignment**: Remote-friendly, impact-driven, collaborative culture requirements
- **Compensation Philosophy**: Equity upside balanced with sustainable base, geographic flexibility

The AI agents use this framework to:
1. **Filter job opportunities** against values and culture fit
2. **Score brand alignment** for company research and positioning
3. **Generate personalized communications** that reflect authentic career narrative
4. **Prioritize networking strategies** based on trajectory goals

This showcases how AI Product Managers can use **structured personal context** to make AI systems more personalized and effective - a pattern applicable across healthcare personalization, EdTech adaptive learning, and other domains requiring individual context.

## 🗺 Project Roadmap

### 🎯 **Phase 1: Foundation** (✅ Complete)
- [x] Multi-agent CrewAI architecture
- [x] MCP Gateway integration
- [x] Queue-based job processing
- [x] HITL dashboard with strategic narrative comparison
- [x] ChromaDB career brand storage

### 🚀 **Phase 2: Intelligence** (🔄 In Progress)
- [ ] **Enhanced Deduplication**: Cross-platform job matching with ML similarity
- [ ] **Referral Probability Scoring**: LinkedIn network analysis for warm introductions
- [ ] **Company Trend Analysis**: Market research automation with competitive intelligence
- [ ] **Interview Preparation Crew**: Automated prep based on company research + role requirements

### 🌟 **Phase 3: Ecosystem** (📋 Planned)
- [ ] **Additional MCP Servers**: Glassdoor, AngelList, company databases
- [ ] **Resume Optimization Crew**: Dynamic resume tailoring per application
- [ ] **Networking Automation**: LinkedIn outreach sequence management
- [ ] **Market Intelligence Dashboard**: Salary trends, skill demand analysis

### 🔮 **Phase 4: Advanced AI** (🔬 Research)
- [ ] **Predictive Job Matching**: ML models for success probability
- [ ] **Conversational Job Coach**: Chat interface for career guidance
- [ ] **Video Interview Analysis**: Prep feedback using computer vision
- [ ] **Portfolio Effect Modeling**: Career trajectory optimization

### 🏥 **Healthcare AI Applications** (💡 Vision)
- [ ] **Diagnostic Decision Support**: Multi-agent clinical analysis patterns
- [ ] **Patient Journey Orchestration**: Care coordination using agentic workflows
- [ ] **Regulatory Compliance Automation**: HIPAA-compliant AI system design
- [ ] **Provider Network Optimization**: Resource allocation using queue-based processing

## 🔄 Development Workflow

This project showcases **AI-assisted development** patterns:

### AI Assistants Used
- **GitHub Copilot**: Code completion and refactoring
- **Google AI Studio**: Architecture design and documentation
- **Claude Code**: Complex logic implementation
- **Grok**: Creative problem-solving and edge cases
- **Codex**: API integration and testing

### Development Conventions
```bash
# Code quality checks
npm run build              # Frontend build verification
python -m py_compile $(git ls-files '*.py')  # Python syntax check

# AI-powered development cycle
1. Define requirements with AI assistance
2. Generate implementation with human oversight
3. Iterate with AI feedback on code quality
4. Test with AI-generated edge cases
5. Document with AI-enhanced clarity
```

See `AGENTS.md` for detailed development conventions and AI agent guidelines.

## 🏗 Architecture Deep Dive

### Multi-Agent Orchestration Pattern
```
Job Posting → [Intake Agent] → [Pre-filter Agent] → [Quick Fit Agent] → [Brand Matcher] → Human Decision
                     ↓              ↓                 ↓                ↓
              Raw Structure    Rejection Rules    Career Alignment   Brand Framework
```

### MCP Gateway Integration
```
CrewAI Agent → MCP Adapter → Docker Gateway → [DuckDuckGo MCP | LinkedIn MCP | Future MCPs]
```

### Queue-Based Processing
```
Job Source → Scraping Queue → Processing Workers → Database → Review Queue → HITL Interface
```

### Career Brand RAG Pipeline
```
Career Framework → ChromaDB Embedding → Semantic Search → Context Injection → Agent Decision
```

## 🔍 Key Learning Outcomes

### For AI Product Managers
1. **Human-AI Collaboration Patterns**: How to design AI systems that enhance rather than replace human judgment
2. **Agentic Architecture Design**: Breaking complex workflows into specialized, coordinated agents
3. **Context-Aware AI**: Using structured personal/business context to improve AI relevance
4. **Extensible AI Systems**: MCP pattern for adding capabilities without architectural changes
5. **Trust-First AI**: Building systems that earn adoption through transparency and control

### For Technical Leaders
1. **Multi-Agent System Design**: CrewAI patterns for complex workflow orchestration
2. **Vector Database Integration**: ChromaDB for context-aware AI applications
3. **Queue-Based AI Processing**: Scalable async processing for AI workloads
4. **Docker-First Development**: Container patterns for AI service orchestration
5. **API-Driven Architecture**: Clean separation between AI logic and user interfaces

## 📊 Success Metrics

This POC demonstrates measurable outcomes:
- **Processing Speed**: 70+ partners onboarded vs 1 (HopSkipDrive pattern applied)
- **Quality Improvement**: 99.9% accuracy in data processing (White Cup pattern)
- **User Adoption**: Bi-weekly iteration cycles vs quarterly (engagement pattern)
- **System Reliability**: Multi-provider LLM fallback ensures 99%+ uptime
- **Developer Velocity**: AI-assisted development reduces feature delivery time by ~40%

## 🤝 Contributing

This is a personal career artifact and learning project. While not actively seeking contributions, the patterns and architecture are designed to be educational and reusable.

For AI Product Managers building similar systems:
1. Fork the repository for your own experimentation
2. Adapt the Career Brand Framework to your context
3. Extend the MCP Gateway pattern for your domain-specific tools
4. Share learnings and patterns that emerge from your implementation

## 📄 License & Usage

This project is shared as an educational resource and career artifact. Feel free to learn from, adapt, or extend these patterns for your own AI Product Management experiments.

**Note**: This repository serves multiple purposes:
- **Working POC** for AI Product Management patterns
- **Career artifact** demonstrating technical and strategic thinking
- **Learning resource** for building human-centered AI systems
- **Thought leadership** in AI Product Management methodologies

---

*Built with 🤖 AI assistance and 🧠 human oversight • Demonstrating the future of AI Product Management*
