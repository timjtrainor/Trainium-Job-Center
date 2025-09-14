import hashlib
import json
import re
from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ..tools.chroma_search import chroma_search

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


def _format_crew_result(
    result: str | Dict[str, Any],
    job_posting: Dict[str, Any],
    correlation_id: str | None,
) -> Dict[str, Any]:
    """Parse crew output and construct FitReviewResult structure.

    Args:
        result: Raw string or dict returned from crew.kickoff.
        job_posting: Original job posting data.
        correlation_id: Correlation identifier for tracing.

    Returns:
        Structured result dictionary.

    Raises:
        ValueError: If required fields cannot be parsed.
    """

    if isinstance(result, str):
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result, re.DOTALL)
            if not match:
                match = re.search(r"(\{.*\})", result, re.DOTALL)
            if not match:
                raise ValueError("No JSON payload found in crew output")
            data = json.loads(match.group(1))
    else:
        data = result

    job_hash = hashlib.md5(json.dumps(job_posting, sort_keys=True).encode()).hexdigest()
    job_id = f"job_{job_hash[:8]}"

    # Handle new format from orchestration_task (preferred)
    if "final" in data and "personas" in data:
        result_obj = {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "final": data.get("final", {
                "recommend": False,
                "rationale": "Unknown decision",
                "confidence": "low"
            }),
            "personas": data.get("personas", []),
            "tradeoffs": data.get("tradeoffs", []),
            "actions": data.get("actions", []),
            "sources": data.get("sources", [])
        }
        
        # Include any additional metrics under 'data' key
        additional_data = {
            k: v for k, v in data.items() 
            if k not in {"final", "personas", "tradeoffs", "actions", "sources", "data"}
        }
        if data.get("data") or additional_data:
            result_obj["data"] = {**data.get("data", {}), **additional_data}
        
        return result_obj

    # Fallback: Handle legacy motivational_verdicts format
    if "motivational_verdicts" not in data:
        raise ValueError("Missing required fields in crew output")

    raw_verdicts = data.get("motivational_verdicts", [])
    formatted_verdicts = []
    positive = 0
    for verdict in raw_verdicts:
        vid = verdict.get("persona_id") or verdict.get("id")
        recommend = bool(verdict.get("recommend"))
        if recommend:
            positive += 1
        formatted_verdicts.append(
            {
                "id": vid,
                "recommend": recommend,
                "reason": verdict.get("reason", ""),
                "notes": verdict.get("notes", []),
                "sources": verdict.get("sources", []),
            }
        )

    total = len(formatted_verdicts)
    if total == 0:
        raise ValueError("No persona verdicts provided")

    recommend_final = positive > (total / 2)
    ratio_text = f"{positive}/{total} agents"
    confidence_ratio = positive / total
    if confidence_ratio >= 0.8:
        confidence = "high"
    elif confidence_ratio >= 0.6:
        confidence = "medium"
    else:
        confidence = "low"

    metrics = {
        k: v
        for k, v in data.items()
        if k not in {"motivational_verdicts", "helper_snapshot"}
    }

    result_obj: Dict[str, Any] = {
        "job_id": job_id,
        "correlation_id": correlation_id,
        "final": {
            "recommend": recommend_final,
            "rationale": f"{ratio_text} recommend this job" if recommend_final else f"{ratio_text} advise caution",
            "confidence": confidence,
        },
        "personas": [
            {"id": v["id"], "recommend": v["recommend"], "reason": v.get("reason", "")}
            for v in formatted_verdicts
        ],
        "tradeoffs": [],
        "actions": [],
        "sources": ["crew_analysis"],
        "data": metrics,
    }

    return result_obj


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
                self.managing_agent(),
                self.job_intake_agent(),
                self.pre_filter_agent(),
                self.quick_fit_analyst(),
                self.brand_framework_matcher(),
            ],
            tasks=[
                self.orchestration_task(),  # Only run orchestration - it will delegate to others as needed
            ],
            process=Process.hierarchical,
            manager_agent=self.managing_agent(),
            verbose=False,  # Disable verbose for better performance
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
    """Run the motivational fan-out crew and return formatted results."""
    try:
        crew = get_job_posting_review_crew()
        job_posting_str = str(job_posting_data)
        inputs: Dict[str, Any] = {"job_posting": job_posting_str}
        if options:
            inputs["options"] = options
        result = crew.kickoff(inputs=inputs)
        raw_output = getattr(result, "raw", result)
        return _format_crew_result(raw_output, job_posting_data, correlation_id)
    except Exception as e:
        job_hash = hashlib.md5(json.dumps(job_posting_data, sort_keys=True).encode()).hexdigest()
        return {
            "job_id": f"error_{job_hash[:8]}",
            "correlation_id": correlation_id,
            "final": {
                "recommend": False,
                "rationale": f"Analysis failed: {str(e)}",
                "confidence": "low",
            },
            "personas": [
                {
                    "id": "error_handler",
                    "recommend": False,
                    "reason": f"Crew execution failed: {str(e)}",
                }
            ],
            "tradeoffs": [],
            "actions": ["Review crew configuration", "Check system dependencies"],
            "sources": ["error_handler"],
        }
if __name__ == "__main__":
    result = get_job_posting_review_crew().kickoff(inputs={
        "job_posting": "Senior Machine Learning Engineer at Acme Corp, salary $200k, remote eligible..."
    })

    print("\n=== FINAL DECISION ===")
    print(result)
