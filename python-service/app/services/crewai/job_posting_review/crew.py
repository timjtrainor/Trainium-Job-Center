from threading import Lock
from typing import Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ..tools.chroma_search import chroma_search

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class JobPostingReviewCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # === Specialists ===
    @agent
    def job_intake_agent(self) -> Agent:
        return Agent(config=self.agents_config["job_intake_agent"])  # type: ignore[index]

    @agent
    def pre_filter_agent(self) -> Agent:
        return Agent(config=self.agents_config["pre_filter_agent"])  # type: ignore[index]

    @agent
    def quick_fit_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["quick_fit_analyst"],  # type: ignore[index]
            #tools=[chroma_search],
        )

    @agent
    def brand_framework_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_framework_matcher"],  # type: ignore[index]
            #tools=[chroma_search],
        )

    # === Manager ===
    @agent
    def managing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["managing_agent"],  # type: ignore[index]
            allow_delegation=True,
        )

    # === Tasks ===
    @task
    def intake_task(self) -> Task:
        return Task(
            config=self.tasks_config["intake_task"],  # type: ignore[index]
            agent=self.job_intake_agent(),
        )

    @task
    def pre_filter_task(self) -> Task:
        return Task(
            config=self.tasks_config["pre_filter_task"],  # type: ignore[index]
            agent=self.pre_filter_agent(),
        )

    @task
    def quick_fit_task(self) -> Task:
        return Task(
            config=self.tasks_config["quick_fit_task"],  # type: ignore[index]
            agent=self.quick_fit_analyst(),
        )

    @task
    def brand_match_task(self) -> Task:
        return Task(
            config=self.tasks_config["brand_match_task"],  # type: ignore[index]
            agent=self.brand_framework_matcher(),
        )

    @task
    def orchestration_task(self) -> Task:
         """Manager controls the workflow: calls intake → pre-filter → quick-fit → brand match if needed."""
         return Task(
             config=self.tasks_config["orchestration_task"],  # type: ignore[index]
             agent=self.managing_agent(),
             async_execution=False,
         )

    # === Crew ===
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.job_intake_agent(),
                self.pre_filter_agent(),
                self.quick_fit_analyst(),
                self.brand_framework_matcher(),
            ],
            tasks=[
                self.orchestration_task(),
                self.intake_task(),
                self.pre_filter_task(),
                self.quick_fit_task(),
                self.brand_match_task(),
            ],
            process=Process.hierarchical,  # 👈 manager runs the show
            manager_agent=self.managing_agent(),
            verbose=True,
        )


def get_job_posting_review_crew() -> Crew:
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = JobPostingReviewCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


def run_crew(job_posting_data: dict, options: dict = None, correlation_id: str = None) -> dict:
    """
    Run the job posting review crew with the provided job posting data.
    
    This function executes the orchestrated CrewAI workflow:
    1. Job intake and parsing
    2. Pre-filtering based on requirements 
    3. Quick fit analysis (if passed pre-filter)
    4. Brand framework matching (if recommended for deeper review)
    5. Final orchestration and recommendation
    
    Args:
        job_posting_data: Dictionary containing job posting information
        options: Optional configuration parameters
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        Dictionary containing the crew analysis result in FitReviewResult format
    """
    try:
        crew = get_job_posting_review_crew()

        # Convert job posting to string for the crew input as expected by the YAML
        job_posting_str = str(job_posting_data)

        # Run the crew with the job posting
        result = crew.kickoff(inputs={"job_posting": job_posting_str})

        raw_output = getattr(result, "raw", str(result))

        # Generate a deterministic job ID
        import hashlib
        job_id = f"job_{hashlib.md5(job_posting_str.encode()).hexdigest()[:8]}"

        # Try to parse structured output from the crew result
        from app.services.crewai.parser import parse_crew_result

        try:
            parsed_result = parse_crew_result(raw_output)
            parsed_result["job_id"] = job_id
            return parsed_result
        except ValueError:
            pass

        # Fallback: Create structured response from crew output
        # This handles cases where the crew doesn't return perfect JSON

        # Determine recommendation based on result content
        result_lower = raw_output.lower()
        recommend = not any(reject_word in result_lower for reject_word in ['reject', 'no', 'fail', 'negative'])

        # Determine confidence based on result clarity
        if any(high_conf in result_lower for high_conf in ['strong', 'excellent', 'clear', 'definitive']):
            confidence = "high"
        elif any(low_conf in result_lower for low_conf in ['weak', 'unclear', 'uncertain', 'maybe']):
            confidence = "low"
        else:
            confidence = "medium"

        summary = raw_output.split("\n")[0][:200]

        return {
            "job_id": job_id,
            "final": {
                "recommend": recommend,
                "rationale": summary,
                "confidence": confidence
            },
            "personas": [
                {
                    "id": "job_posting_review_crew",
                    "recommend": recommend,
                    "reason": "Analyzed by job posting review crew with hierarchical orchestration"
                }
            ],
            "tradeoffs": [],
            "actions": [],
            "sources": ["job_posting_review_crew", "crewai_orchestration"]
        }
        
    except Exception as e:
        # Return error information in the expected format
        return {
            "job_id": f"error_{hash(str(job_posting_data)) % 1000000}",
            "final": {
                "recommend": False,
                "rationale": f"Analysis failed: {str(e)}",
                "confidence": "low"
            },
            "personas": [
                {
                    "id": "error_handler",
                    "recommend": False,
                    "reason": f"Crew execution failed: {str(e)}"
                }
            ],
            "tradeoffs": [],
            "actions": ["Review crew configuration", "Check system dependencies"],
            "sources": ["error_handler"]
        }


if __name__ == "__main__":
    result = get_job_posting_review_crew().kickoff(inputs={
        "job_posting": "Senior Machine Learning Engineer at Acme Corp, salary $200k, remote eligible..."
    })

    print("\n=== FINAL DECISION ===")
    print(result)