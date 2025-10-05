"""Clean CrewAI agent and task definitions for job posting review. Business logic in YAML configs."""

import os
from threading import Lock
from typing import Optional
from loguru import logger

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ..knowledge_sources import get_knowledge_sources_from_config
from ...ai.langchain_llama import get_llamacpp_llm

import chromadb
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.storage.knowledge_storage import KnowledgeStorage


class KnowledgeSourceLoadError(Exception):
    """Exception raised when knowledge sources cannot be loaded from external dependencies."""
    pass

# IMPORT MODELS AT MODULE LEVEL for CrewAI dynamic imports
from models.creaii_schemas import BrandDimensionAnalysis, ConstraintsAnalysis, BrandMatchComplete, TldrSummary

# Make models available globally for CrewAI imports
__all__ = ["BrandDimensionAnalysis", "ConstraintsAnalysis", "BrandMatchComplete", "TldrSummary"]

# Set environment variables to minimize CrewAI logging and event issues
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_DISABLE_EVENTS", "true")



_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class JobPostingReviewCrew:
    """Clean CrewAI configuration with business logic in YAML files and tools."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize crew and apply JSON cleanup patches for Ollama models."""
        super().__init__()
        self._apply_json_cleanup_patch()

    def _apply_json_cleanup_patch(self):
        """
        Monkey patch CrewAI's converter to clean JSON responses before parsing.
        This handles Gemma3/Phi3 models that wrap JSON in markdown code blocks.
        """
        try:
            from crewai.utilities.converter import Converter
            from .rules import clean_llm_json_response

            # Save original to_pydantic method
            original_to_pydantic = Converter.to_pydantic

            def patched_to_pydantic(self, current_attempt=1):
                """Cleaned version that strips markdown before parsing."""
                # Clean the text before parsing
                if hasattr(self, 'text') and self.text:
                    self.text = clean_llm_json_response(self.text)
                # Call original method
                return original_to_pydantic(self, current_attempt)

            # Apply the patch
            Converter.to_pydantic = patched_to_pydantic
            logger.info("✅ Applied JSON cleanup patch to CrewAI converter")

        except Exception as e:
            logger.warning(f"⚠️ Could not apply JSON cleanup patch: {e}")
            logger.info("   JSON cleanup will still work via extract_json_from_crew_output")

    def _inject_knowledge_sources_into_agents(self, crew_instance):
        """ENABLE proper ChromaDB knowledge sources with error handling and retry logic."""

        import time

        # Retry connection with exponential backoff
        client = None
        for attempt in range(3):
            try:
                # Connect to external ChromaDB container
                client = chromadb.HttpClient(host="chromadb", port=8001)
                # Test connection with heartbeat
                client.heartbeat()
                logger.info(f"✅ ChromaDB connection successful (attempt {attempt + 1})")
                break
            except Exception as e:
                if attempt == 2:
                    raise KnowledgeSourceLoadError(
                        f"Cannot load knowledge sources: ChromaDB connection failed after 3 attempts: {e}. "
                        f"The job review system cannot operate without career context knowledge. "
                        f"Please ensure the ChromaDB service is running and accessible."
                    )
                else:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"⚠️ ChromaDB connection attempt {attempt + 1} failed: {e}")
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        # Setup knowledge for each agent type (only 5 dimensions now)
        knowledge_mapping = {}
        try:
            knowledge_mapping = {
                'north_star_matcher': self._setup_north_star_knowledge_source(client),
                'trajectory_mastery_matcher': self._setup_trajectory_mastery_knowledge_source(client),
                'values_compass_matcher': self._setup_values_compass_knowledge_source(client),
                'lifestyle_alignment_matcher': self._setup_lifestyle_alignment_knowledge_source(client),
                'compensation_philosophy_matcher': self._setup_compensation_philosophy_knowledge_source(client),
            }
            logger.info(f"✅ Created {len(knowledge_mapping)} knowledge sources")
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup knowledge sources: {e}")
            return

        # Assign knowledge sources to agents by matching role keywords
        # Map role keywords to knowledge sources
        role_keywords_map = {
            'north_star': 'north_star_matcher',
            'trajectory': 'trajectory_mastery_matcher',
            'values': 'values_compass_matcher',
            'lifestyle': 'lifestyle_alignment_matcher',
            'compensation': 'compensation_philosophy_matcher',
        }

        counter = 0
        for agent in crew_instance.agents:
            if hasattr(agent, 'role') and agent.role:
                role_lower = agent.role.lower()
                # Find matching knowledge source by keyword in role
                for keyword, knowledge_key in role_keywords_map.items():
                    if keyword in role_lower and knowledge_key in knowledge_mapping:
                        agent.knowledge_sources = [knowledge_mapping[knowledge_key]]
                        counter += 1
                        logger.info(f"✅ Assigned {knowledge_key} knowledge to agent: {agent.role[:50]}...")
                        break

        logger.info(f"✅ Injected knowledge sources into {counter} agents")

    def _create_filtered_knowledge_source(self, dimension_name, content_description="career brand data"):
        """Create knowledge source filtered by dimension metadata from ChromaDB.

        Documents uploaded via the UI are split by H1 headings and saved with a 'dimension'
        metadata field (e.g., 'north_star', 'trajectory_mastery', 'values', etc.).
        We filter to get only the relevant dimension's content for each agent.
        """

        try:
            # Connect to ChromaDB and get dimension-specific documents
            client = chromadb.HttpClient(host="chromadb", port=8001)
            collection = client.get_collection("career_brand")

            # Filter by dimension metadata
            results = collection.get(
                where={"dimension": dimension_name},
                limit=50,  # Get up to 50 chunks for this dimension
                include=["documents", "metadatas"]
            )

            # Combine matching documents into knowledge content
            if results and results.get('documents') and len(results['documents']) > 0:
                # Sort by seq if available to maintain chunk order
                docs_with_meta = list(zip(results['documents'], results['metadatas']))
                docs_with_meta.sort(key=lambda x: x[1].get('seq', 0))

                content_parts = [doc for doc, _ in docs_with_meta]
                content = "\n\n".join(content_parts)
                logger.info(f"✅ Loaded {len(content_parts)} documents for dimension: {dimension_name}")
            else:
                content = f"No career brand data available for {dimension_name}"
                logger.warning(f"⚠️ No documents found for dimension: {dimension_name}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load {dimension_name} data from ChromaDB: {e}")
            logger.exception(e)  # Log full traceback for debugging
            content = f"No career brand data available for {dimension_name} due to connection error: {e}"

        # Create StringKnowledgeSource with the filtered content
        knowledge = StringKnowledgeSource(content=content)

        # Note: We don't use KnowledgeStorage here since we can't filter metadata with it
        # Instead we pre-filter the content above and provide it directly

        return knowledge

    def _setup_north_star_knowledge_source(self, client):
        """North Star vision knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("north_star", "north star vision data")

    def _setup_trajectory_mastery_knowledge_source(self, client):
        """Trajectory mastery knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("trajectory_mastery", "trajectory mastery data")

    def _setup_values_compass_knowledge_source(self, client):
        """Values compass knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("values", "values compass data")

    def _setup_lifestyle_alignment_knowledge_source(self, client):
        """Lifestyle alignment knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("lifestyle_alignment", "lifestyle alignment data")

    def _setup_compensation_philosophy_knowledge_source(self, client):
        """Compensation philosophy knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("compensation_philosophy", "compensation philosophy data")

    @agent
    def north_star_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's North Star & Vision."""
        agent = Agent(config=self.agents_config["north_star_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def trajectory_mastery_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Trajectory & Mastery goals."""
        agent = Agent(config=self.agents_config["trajectory_mastery_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def values_compass_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Values Compass."""
        agent = Agent(config=self.agents_config["values_compass_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def lifestyle_alignment_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Lifestyle preferences."""
        agent = Agent(config=self.agents_config["lifestyle_alignment_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def compensation_philosophy_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Compensation Philosophy."""
        agent = Agent(config=self.agents_config["compensation_philosophy_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def brand_match_manager(self) -> Agent:
        """Manager agent that synthesizes brand dimension specialist results."""
        agent = Agent(config=self.agents_config["brand_match_manager"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def tldr_summarizer(self) -> Agent:
        """Agent that creates concise TLDR summaries for quick human review."""
        agent = Agent(config=self.agents_config["tldr_summarizer"], use_stop_words=False)  # type: ignore[index]
        return agent

    @task
    def north_star_task(self):
        """Task to analyze job alignment with North Star & Vision."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["north_star_task"]["description"],
            expected_output=self.tasks_config["north_star_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.north_star_matcher(),
            async_execution=True,
        )

    @task
    def trajectory_mastery_task(self):
        """Task to analyze job alignment with Trajectory & Mastery."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["trajectory_mastery_task"]["description"],
            expected_output=self.tasks_config["trajectory_mastery_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.trajectory_mastery_matcher(),
            async_execution=True,
        )

    @task
    def values_compass_task(self):
        """Task to analyze job alignment with Values Compass."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["values_compass_task"]["description"],
            expected_output=self.tasks_config["values_compass_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.values_compass_matcher(),
            async_execution=True,
        )

    @task
    def lifestyle_alignment_task(self):
        """Task to analyze job alignment with Lifestyle preferences."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["lifestyle_alignment_task"]["description"],
            expected_output=self.tasks_config["lifestyle_alignment_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.lifestyle_alignment_matcher(),
            async_execution=True,
        )

    @task
    def compensation_philosophy_task(self):
        """Task to analyze job alignment with Compensation Philosophy."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["compensation_philosophy_task"]["description"],
            expected_output=self.tasks_config["compensation_philosophy_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.compensation_philosophy_matcher(),
            async_execution=True,
        )

    @task
    def brand_match_task(self):
        """Task to synthesize all brand dimension analyses into final recommendation."""

        return Task(
            description="""
            SYNTHESIS TASK: Combine the 5 specialist results and CALCULATE the weighted overall_alignment_score yourself.

            Your job is:
            1. VERIFY you have all 5 specialist results as context (north_star, trajectory_mastery, values_compass, lifestyle_alignment, compensation_philosophy).
            2. CALCULATE overall_alignment_score using the weighted 0-10 conversion provided in your agent instructions and round to two decimals (numeric literal, no quotes).
            3. DETERMINE confidence level based on the calculated score and set recommend=true when the score >= 5.0.
            4. WRITE a comprehensive overall_summary (5-7 sentences, <=150 words) that cites key evidence from each dimension.
            5. OUTPUT the complete BrandMatchComplete JSON exactly once using this structure:
               {
                 "north_star": {"score": <1-5>, "summary": "..."},
                 "trajectory_mastery": {"score": <1-5>, "summary": "..."},
                 "values_compass": {"score": <1-5>, "summary": "..."},
                 "lifestyle_alignment": {"score": <1-5>, "summary": "..."},
                 "compensation_philosophy": {"score": <1-5>, "summary": "..."},
                 "overall_alignment_score": <float>,
                 "overall_summary": "...",
                 "recommend": <true|false>,
                 "confidence": "<low|medium|high>"
               }

            CRITICAL: overall_alignment_score must be the weighted calculation result and appear as an unquoted number. Do not add extra fields or free text.
            """,
            expected_output="Complete BrandMatchComplete JSON with calculated numeric overall_alignment_score and comprehensive synthesis",
            output_pydantic=BrandMatchComplete,
            agent=self.brand_match_manager(),
            context=[
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
            ]
        )

    @task
    def tldr_summary_task(self):
        """Task to create concise TLDR summary for quick human review."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["tldr_summary_task"]["description"],
            expected_output=self.tasks_config["tldr_summary_task"]["expected_output"],
            output_pydantic=TldrSummary,
            agent=self.tldr_summarizer(),
            async_execution=True,
        )

    @crew
    def crew(self) -> Crew:
        """Crew definition focused on agent/task configuration."""
        crew_instance = Crew(
            agents=[
                # 5 parallel brand dimension specialists (reduced from 9)
                self.north_star_matcher(),
                self.trajectory_mastery_matcher(),
                self.values_compass_matcher(),
                self.lifestyle_alignment_matcher(),
                self.compensation_philosophy_matcher(),
                # TLDR summarizer runs in parallel with evaluation tasks
                self.tldr_summarizer(),
                # Manager that synthesizes results
                self.brand_match_manager(),
            ],
            tasks=[
                # 5 brand analysis tasks run in parallel (async_execution=True)
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
                # TLDR summary task runs in parallel with evaluation tasks
                self.tldr_summary_task(),
                # Final synthesis task - waits for all parallel tasks
                self.brand_match_task(),
            ],
            process=Process.sequential,  # Orchestration handled externally
            verbose=True,
        )

        # Inject knowledge sources into agents programmatically
        self._inject_knowledge_sources_into_agents(crew_instance)

        return crew_instance


def get_job_posting_review_crew() -> Crew:
    """Get cached CrewAI crew instance."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = JobPostingReviewCrew().crew()
    return _cached_crew


def run_crew(job_posting_data: dict, options: dict = None, correlation_id: str = None) -> dict:
    """
    Execute the job posting review crew.

    Note: This function now delegates orchestration to the JobPostingOrchestrator
    for better separation of concerns. Direct crew execution is not recommended.
    """
    from .orchestrator import evaluate_job_posting
    return evaluate_job_posting(job_posting_data, correlation_id)


# For backward compatibility and testing
if __name__ == "__main__":
    from .orchestrator import evaluate_job_posting

    sample = {
        "title": "Senior Machine Learning Engineer",
        "company": "Acme Corp",
        "description": "Build ML systems",
        "highest_salary": 250000,
        "seniority": "Senior",
        "job_type": "remote"
    }

    result = evaluate_job_posting(sample)
    print("Job Evaluation Result:")
    print(f"Final Recommendation: {result.get('final', {}).get('recommend', 'Unknown')}")
    print(f"Confidence: {result.get('final', {}).get('confidence', 'Unknown')}")
    print(f"Rationale: {result.get('final', {}).get('rationale', 'No rationale provided')}")
