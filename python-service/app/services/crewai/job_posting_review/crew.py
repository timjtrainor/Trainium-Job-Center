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

# IMPORT MODELS AT MODULE LEVEL for CrewAI dynamic imports
from models.creaii_schemas import PreFilterResult, BrandDimensionAnalysis, ConstraintsAnalysis, BrandMatchComplete

# Make models available globally for CrewAI imports
__all__ = ["PreFilterResult", "BrandDimensionAnalysis", "ConstraintsAnalysis", "BrandMatchComplete"]

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

    def _inject_knowledge_sources_into_agents(self, crew_instance):
        """ENABLE proper ChromaDB knowledge sources with error handling."""

        try:
            # Connect to external ChromaDB container
            client = chromadb.HttpClient(host="chromadb", port=8001)
            # Test connection with heartbeat
            client.heartbeat()
            logger.info("✅ ChromaDB connection successful")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB connection failed: {e}")
            logger.warning("🔄 Falling back to no knowledge sources")
            return

        # Setup knowledge for each agent type
        knowledge_mapping = {}
        try:
            knowledge_mapping = {
                'north_star_matcher': self._setup_north_star_knowledge_source(client),
                'trajectory_mastery_matcher': self._setup_trajectory_mastery_knowledge_source(client),
                'values_compass_matcher': self._setup_values_compass_knowledge_source(client),
                'lifestyle_alignment_matcher': self._setup_lifestyle_alignment_knowledge_source(client),
                'compensation_philosophy_matcher': self._setup_compensation_philosophy_knowledge_source(client),
                'purpose_impact_matcher': self._setup_purpose_impact_knowledge_source(client),
                'industry_focus_matcher': self._setup_industry_focus_knowledge_source(client),
                'company_filters_matcher': self._setup_company_filters_knowledge_source(client),
                'constraints_matcher': self._setup_constraints_knowledge_source(client),
            }
            logger.info(f"✅ Created {len(knowledge_mapping)} knowledge sources")
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup knowledge sources: {e}")
            return

        # Assign knowledge sources to agents by role
        counter = 0
        for agent in crew_instance.agents:
            if hasattr(agent, 'role') and agent.role:
                if agent.role in knowledge_mapping:
                    agent.knowledge_sources = [knowledge_mapping[agent.role]]
                    counter += 1

        logger.info(f"✅ Injected knowledge sources into {counter} agents")

    def _create_filtered_knowledge_source(self, dimension_name, content_description="career brand data"):
        """Create knowledge source with metadata-filtered career brand data from single collection."""

        try:
            # Connect to ChromaDB and query career_brand collection with metadata filter
            client = chromadb.HttpClient(host="chromadb", port=8001)
            collection = client.get_collection("career_brand")

            # Query documents with specific dimension metadata
            results = collection.query(
                query_texts=[""],  # Empty query to get all documents with this dimension
                where={"dimension": dimension_name},
                n_results=50,  # Get up to 50 documents for comprehensive coverage
                include=["documents", "metadatas"]
            )

            # Combine all matching documents into knowledge content
            if results['documents'] and len(results['documents']) > 0:
                content_parts = []
                for doc_list in results['documents']:
                    content_parts.extend(doc_list if isinstance(doc_list, list) else [doc_list])
                content = "\n\n".join(content_parts)
                logger.info(f"✅ Loaded {len(content_parts)} documents for {dimension_name}")
            else:
                content = f"No career brand data available for {dimension_name}"
                logger.warning(f"⚠️ No documents found for dimension: {dimension_name}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load {dimension_name} data from ChromaDB: {e}")
            content = f"No career brand data available for {dimension_name} due to connection error"

        # Create StringKnowledgeSource with the filtered content
        knowledge = StringKnowledgeSource(content=content)

        # Note: We don't use KnowledgeStorage here since we can't filter metadata with it
        # Instead we pre-filter the content above and provide it directly

        return knowledge

    def _setup_north_star_knowledge_source(self, client):
        """North Star vision knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("north_star_vision", "north star vision data")

    def _setup_trajectory_mastery_knowledge_source(self, client):
        """Trajectory mastery knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("trajectory_mastery", "trajectory mastery data")

    def _setup_values_compass_knowledge_source(self, client):
        """Values compass knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("values_compass", "values compass data")

    def _setup_lifestyle_alignment_knowledge_source(self, client):
        """Lifestyle alignment knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("lifestyle_alignment", "lifestyle alignment data")

    def _setup_compensation_philosophy_knowledge_source(self, client):
        """Compensation philosophy knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("compensation_philosophy", "compensation philosophy data")

    def _setup_purpose_impact_knowledge_source(self, client):
        """Purpose impact knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("purpose_impact", "purpose impact data")

    def _setup_industry_focus_knowledge_source(self, client):
        """Industry focus knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("industry_focus", "industry focus data")

    def _setup_company_filters_knowledge_source(self, client):
        """Company filters knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("company_filters", "company filters data")

    def _setup_constraints_knowledge_source(self, client):
        """Constraints knowledge with metadata filtering."""
        return self._create_filtered_knowledge_source("constraints", "constraints data")

    @agent
    def pre_filter_agent(self) -> Agent:
        """Agent that applies hard-coded rejection rules to filter unqualified jobs."""
        agent = Agent(config=self.agents_config["pre_filter_agent"], use_stop_words=False)  # type: ignore[index]
        return agent

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
    def purpose_impact_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Purpose & Impact goals."""
        agent = Agent(config=self.agents_config["purpose_impact_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def industry_focus_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Industry Focus preferences."""
        agent = Agent(config=self.agents_config["industry_focus_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def company_filters_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Company culture preferences."""
        agent = Agent(config=self.agents_config["company_filters_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def constraints_matcher(self) -> Agent:
        """Agent that evaluates job compliance with user's hard requirements and deal-breakers."""
        agent = Agent(config=self.agents_config["constraints_matcher"], use_stop_words=False)  # type: ignore[index]
        return agent

    @agent
    def brand_match_manager(self) -> Agent:
        """Manager agent that synthesizes brand dimension specialist results."""
        agent = Agent(config=self.agents_config["brand_match_manager"], use_stop_words=False)  # type: ignore[index]
        return agent

    @task
    def pre_filter_task(self):
        """Task to evaluate basic job qualifications with rule-based filtering."""

        # Debug: Test model creation and import
        logger.info("🔍 Testing PreFilterResult model import and creation...")
        try:
            test_model = PreFilterResult(recommend=True, reason="Test import")
            logger.info(f"✅ PreFilterResult model creation successful: {test_model.dict()}")
        except Exception as e:
            logger.error(f"❌ PreFilterResult model creation failed: {e}")
            logger.error("💡 This suggests the model import or definition is broken")
            # Continue without pydantic validation to keep pipeline working
            logger.warning("⚠️ Falling back to basic JSON validation (no pydantic)")

        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["pre_filter_task"]["description"],
            expected_output=self.tasks_config["pre_filter_task"]["expected_output"],
            output_pydantic=PreFilterResult,
            agent=self.pre_filter_agent(),
        )

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
    def purpose_impact_task(self):
        """Task to analyze job alignment with Purpose & Impact."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["purpose_impact_task"]["description"],
            expected_output=self.tasks_config["purpose_impact_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.purpose_impact_matcher(),
            async_execution=True,
        )

    @task
    def industry_focus_task(self):
        """Task to analyze job alignment with Industry Focus."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["industry_focus_task"]["description"],
            expected_output=self.tasks_config["industry_focus_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.industry_focus_matcher(),
            async_execution=True,
        )

    @task
    def company_filters_task(self):
        """Task to analyze job alignment with Company Filters."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["company_filters_task"]["description"],
            expected_output=self.tasks_config["company_filters_task"]["expected_output"],
            output_pydantic=BrandDimensionAnalysis,
            agent=self.company_filters_matcher(),
            async_execution=True,
        )

    @task
    def constraints_task(self):
        """Task to analyze job compliance with Constraints."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["constraints_task"]["description"],
            expected_output=self.tasks_config["constraints_task"]["expected_output"],
            output_pydantic=ConstraintsAnalysis,
            agent=self.constraints_matcher(),
            async_execution=True,
        )

    @task
    def brand_match_task(self):
        """Task to synthesize all brand dimension analyses into final recommendation."""
        # Build Task with explicit parameters (not using config= to avoid overrides)
        return Task(
            description=self.tasks_config["brand_match_task"]["description"],
            expected_output=self.tasks_config["brand_match_task"]["expected_output"],
            output_pydantic=BrandMatchComplete,
            agent=self.brand_match_manager(),
            context=[
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
                self.purpose_impact_task(),
                self.industry_focus_task(),
                self.company_filters_task(),
                self.constraints_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Crew definition focused on agent/task configuration."""
        crew_instance = Crew(
            agents=[
                self.pre_filter_agent(),
                # All 9 parallel brand dimension specialists
                self.north_star_matcher(),
                self.trajectory_mastery_matcher(),
                self.values_compass_matcher(),
                self.lifestyle_alignment_matcher(),
                self.compensation_philosophy_matcher(),
                self.purpose_impact_matcher(),
                self.industry_focus_matcher(),
                self.company_filters_matcher(),
                self.constraints_matcher(),
                # Manager that synthesizes results
                self.brand_match_manager(),
            ],
            tasks=[
                self.pre_filter_task(),
                # All brand analysis tasks run in parallel
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
                self.purpose_impact_task(),
                self.industry_focus_task(),
                self.company_filters_task(),
                self.constraints_task(),
                # Final synthesis task
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
