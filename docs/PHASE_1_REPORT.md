# Phase 1: Assessment and Triage Report

## 1.1 Directory Structure Audit

**Objective**: Identify redundant, ambiguous, or overly large directories/files.

### Top 10 Largest Directories (by file count)
- `./components`: 95 files
- `.`: 48 files
- `./python-service`: 31 files
- `./python-service/app/api/v1/endpoints`: 20 files
- `./docs`: 17 files
- `./python-service/app/schemas`: 15 files
- `./python-service/app/services/infrastructure`: 13 files
- `./tests/services`: 12 files
- `./python-service/app/services`: 11 files
- `./python-service/app/services/ai`: 11 files

### Recommendations
- **`./components`**: This directory is critically over-populated. **Action**: Group by domain (e.g., `components/jobs`, `components/interview`) and type (`components/ui`, `components/modals`).
- **`./python-service`**: Contains many root-level scripts. **Action**: Move scripts to `scripts/` and tests to `tests/`.
- **`./python-service/app/api/v1/endpoints`**: Starting to grow large. **Action**: Ensure strictly routing logic resides here; move business logic to `services`.

## 1.2 Dependency Mapping

**Objective**: Analyze module interdependence (coupling).

### Core Modules (Most Imported)
These modules are central to the application and carry high risk when modified.

- `../types` (Imported 97 times)
- `../services/geminiService` (Imported 26 times)
- `../services/apiService` (Imported 13 times)
- `app.core.config` (Imported 9 times)
- `app.services.mcp` (Imported 9 times)
- `../utils` (Imported 8 times)
- `app.schemas.jobspy` (Imported 5 times)
- `../constants` (Imported 5 times)
- `app.services.infrastructure.database` (Imported 5 times)
- `app.services.infrastructure.queue` (Imported 5 times)

### Circular Dependencies
*(Note: Detected via static analysis of imports. False positives possible.)*
- **Potential Cycle Risk**: `python-service/app/services/crewai` internal imports often show circular patterns in Agent systems. Verify `orchestrator.py` vs `crew.py`.

## 1.3 Code Smell Identification

**Objective**: Focus on long functions, high cyclomatic complexity (> 15), and duplication.

### Functions with High Cyclomatic Complexity (> 15)
| Function | Location | Complexity |
| :--- | :--- | :--- |
| `FILE_LEVEL_CHECK` | `./services/apiService.ts` | 108 |
| `FILE_LEVEL_CHECK` | `./App.tsx` | 96 |
| `FILE_LEVEL_CHECK` | `./promptsData.ts` | 95 |
| `FILE_LEVEL_CHECK` | `./components/ChromaUploadView.tsx` | 72 |
| `FILE_LEVEL_CHECK` | `./components/DownloadResumeStep.tsx` | 67 |
| `FILE_LEVEL_CHECK` | `./types.ts` | 59 |
| `upload_full_career_brand_document` | `./python-service/app/api/v1/endpoints/chroma.py` | 51 |
| `process_scheduled_sites` | `./python-service/app/services/infrastructure/scheduler.py` | 45 |
| `FILE_LEVEL_CHECK` | `./services/geminiService.ts` | 43 |
| `FILE_LEVEL_CHECK` | `./components/InterviewStudioView.tsx` | 42 |
| `scrape_jobs_sync` | `./python-service/app/services/jobspy/scraping.py` | 41 |
| `FILE_LEVEL_CHECK` | `./components/JobCardView.tsx` | 36 |
| `FILE_LEVEL_CHECK` | `./components/InterviewCopilotView.tsx` | 34 |
| `update_resume_document` | `./python-service/app/services/chroma_integration_service.py` | 32 |
| `_parse_crew_result` | `./python-service/app/services/crewai/job_posting_review/orchestrator.py` | 29 |
| `FILE_LEVEL_CHECK` | `./components/ResumeEditorView.tsx` | 28 |
| `scrape_jobs_async` | `./python-service/app/services/jobspy/ingestion.py` | 27 |
| `FILE_LEVEL_CHECK` | `./components/CompanyDetailView.tsx` | 27 |
| `FILE_LEVEL_CHECK` | `./components/ContactModal.tsx` | 25 |
| `FILE_LEVEL_CHECK` | `./components/ScheduleManagementView.tsx` | 25 |
| `FILE_LEVEL_CHECK` | `./components/ApplicationDetailView.tsx` | 25 |
| `process_job_review` | `./python-service/app/services/infrastructure/worker.py` | 24 |
| `_build_job_posting` | `./python-service/app/services/infrastructure/pre_filter_backfill.py` | 24 |
| `FILE_LEVEL_CHECK` | `./components/interview-copilot/shims/react-grid-layout.tsx` | 24 |
| `map_section_to_career_brand_category` | `./python-service/app/api/v1/endpoints/chroma.py` | 23 |
| `get_documents` | `./python-service/app/api/v1/endpoints/chroma.py` | 23 |
| `FILE_LEVEL_CHECK` | `./components/EngagementModal.tsx` | 23 |
| `_scrape_sync` | `./python-service/app/services/jobspy/ingestion.py` | 22 |
| `get_reviewed_jobs` | `./python-service/app/services/infrastructure/database.py` | 21 |
| `_coerce_output_value` | `./python-service/app/services/crewai/job_posting_review/orchestrator.py` | 21 |
| `FILE_LEVEL_CHECK` | `./components/TailorResumeStep.tsx` | 21 |
| `FILE_LEVEL_CHECK` | `./components/ManualJobCreate.tsx` | 21 |
| `get_multi_section_career_brand_digest` | `./python-service/app/services/fit_review/retrieval.py` | 20 |
| `FILE_LEVEL_CHECK` | `./components/IconComponents.tsx` | 20 |
| `_prepare_proof_point_rollover_metadata` | `./python-service/app/services/chroma_integration_service.py` | 19 |
| `create_company` | `./python-service/app/services/infrastructure/database.py` | 19 |
| `chroma_search` | `./python-service/app/services/crewai/tools/chroma_search.py` | 18 |
| `_coerce_mcp_job_details` | `./python-service/app/api/v1/endpoints/linkedin_jobs.py` | 18 |
| `dashboard_style_monitoring` | `./python-service/examples/health_monitoring.py` | 18 |
| `FILE_LEVEL_CHECK` | `./components/CoreNarrativeLab.tsx` | 18 |
| `FILE_LEVEL_CHECK` | `./components/DashboardView.tsx` | 18 |
| `main` | `./python-service/job_review_cli.py` | 17 |
| `_prepare_resume_rollover_metadata` | `./python-service/app/services/chroma_integration_service.py` | 17 |
| `list_documents` | `./python-service/app/services/chroma_service.py` | 17 |
| `get_document_detail` | `./python-service/app/services/chroma_service.py` | 17 |
| `update_document` | `./python-service/app/services/chroma_service.py` | 17 |
| `clear_orphaned_locks` | `./python-service/app/services/infrastructure/queue.py` | 17 |
| `get_career_brand_digest` | `./python-service/app/services/fit_review/retrieval.py` | 17 |
| `FILE_LEVEL_CHECK` | `./components/interview-copilot/widgets/ImpactStoriesWidget.tsx` | 17 |
| `get_latest_document_by_dimension` | `./python-service/app/services/chroma_service.py` | 16 |
| `poll_and_enqueue_jobs` | `./python-service/app/services/infrastructure/poller.py` | 16 |
| `scrape_jobs_worker` | `./python-service/app/services/infrastructure/worker.py` | 16 |
| `run_linkedin_job_search` | `./python-service/app/services/infrastructure/worker.py` | 16 |
| `run` | `./python-service/app/services/infrastructure/pre_filter_backfill.py` | 16 |
| `delete_document_by_id` | `./python-service/app/api/v1/endpoints/chroma.py` | 16 |
| `performance_metrics_monitoring` | `./python-service/examples/health_monitoring.py` | 16 |
| `FILE_LEVEL_CHECK` | `./components/DailySprintView.tsx` | 16 |
| `FILE_LEVEL_CHECK` | `./components/JobReviewModal.tsx` | 16 |

### Large Files (Potential for Split)
- `./services/apiService.ts`: 2173 lines
- `./App.tsx`: 1929 lines
- `./promptsData.ts`: 1915 lines
- `./components/ChromaUploadView.tsx`: 1440 lines
- `./components/DownloadResumeStep.tsx`: 1341 lines
- `./python-service/app/services/infrastructure/database.py`: 1222 lines
- `./types.ts`: 1182 lines
- `./python-service/app/services/chroma_manager.py`: 1083 lines
- `./python-service/app/services/crewai/job_posting_review/orchestrator.py`: 947 lines
- `./python-service/app/services/chroma_service.py`: 910 lines

## 1.4 Documentation Gap Analysis

**Objective**: Identify major feature areas lacking modern documentation.

### Feature Areas & Documentation Status
| Feature Area | Status | Location | Notes |
| :--- | :--- | :--- | :--- |
| **Job Posting Review** | ⚠️ Partial | `python-service/JOB_REVIEW_README.md` | Has a specific README but might be stale. |
| **CrewAI Agents** | ✅ Good | `python-service/app/services/crewai/AGENTS.md` | Detailed instructions for agents exist. |
| **Frontend Components** | ❌ Missing | `components/` | No central README or Storybook. |
| **API Endpoints** | ⚠️ Partial | `python-service/app/api/` | Relies on FastAPI Auto-docs (Swagger). No architectural overview. |
| **Database Schema** | ❌ Missing | `db/` | No ERD or schema documentation found (except raw SQL/Alembic). |

### Priority List for Documentation
1. **Frontend Architecture**: Explain the component hierarchy and state management.
2. **Job Parsing Pipeline**: Document the flow from JobSpy/LinkedIn to Database.
3. **Deployment/Setup**: Consolidate `README.md`, `DEDUPLICATION_QUICKSTART.md`, etc.
