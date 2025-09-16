import hashlib
import json
import re
import os
from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ....schemas.job_posting_review import (JobPostingReviewOutput)

# Set environment variables to minimize CrewAI logging and event issues
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_DISABLE_EVENTS", "true")


from ..tools.chroma_search import (
    search_career_brands,
    search_career_research,
    search_job_search_research,
    get_career_brand_tools
)

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

    job_hash = hashlib.md5(
        json.dumps(job_posting, sort_keys=True, default=float).encode()
    ).hexdigest()
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

    # === Specialists (quick_fit_analyst removed, pre_filter and brand specialist agents added) ===

    @agent
    def pre_filter_agent(self) -> Agent:
        return Agent(config=self.agents_config["pre_filter_agent"])  # type: ignore[index]

    # === Brand Dimension Specialists ===
    @agent
    def north_star_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["north_star_matcher"],  # type: ignore[index]
            tools=get_career_brand_tools(),
        )

    @agent
    def trajectory_mastery_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["trajectory_mastery_matcher"],  # type: ignore[index]
            tools=get_career_brand_tools(),
        )

    @agent
    def values_compass_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["values_compass_matcher"],  # type: ignore[index]
            tools=get_career_brand_tools(),
        )

    @agent
    def lifestyle_alignment_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["lifestyle_alignment_matcher"],  # type: ignore[index]
            tools=get_career_brand_tools(),
        )

    @agent
    def compensation_philosophy_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["compensation_philosophy_matcher"],  # type: ignore[index]
            tools=get_career_brand_tools(),
        )

    @agent
    def brand_match_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_match_manager"],  # type: ignore[index]
        )

    # === Legacy Manager (unused) ===
    @agent
    def managing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["managing_agent"],  # type: ignore[index]
            allow_delegation=True,
        )

    # === Tasks (quick_fit_task removed, pre_filter and specialized brand tasks added) ===

    @task
    def pre_filter_task(self) -> Task:
        return Task(
            config=self.tasks_config["pre_filter_task"],  # type: ignore[index]
            agent=self.pre_filter_agent(),
        )

    # === Brand Dimension Tasks (run in parallel) ===
    @task  
    def north_star_task(self) -> Task:
        return Task(
            config=self.tasks_config["north_star_task"],  # type: ignore[index]
            agent=self.north_star_matcher(),
            async_execution=True,
        )

    @task
    def trajectory_mastery_task(self) -> Task:
        return Task(
            config=self.tasks_config["trajectory_mastery_task"],  # type: ignore[index]
            agent=self.trajectory_mastery_matcher(),
            async_execution=True,
        )

    @task
    def values_compass_task(self) -> Task:
        return Task(
            config=self.tasks_config["values_compass_task"],  # type: ignore[index]
            agent=self.values_compass_matcher(),
            async_execution=True,
        )

    @task
    def lifestyle_alignment_task(self) -> Task:
        return Task(
            config=self.tasks_config["lifestyle_alignment_task"],  # type: ignore[index]
            agent=self.lifestyle_alignment_matcher(),
            async_execution=True,
        )

    @task
    def compensation_philosophy_task(self) -> Task:
        return Task(
            config=self.tasks_config["compensation_philosophy_task"],  # type: ignore[index]
            agent=self.compensation_philosophy_matcher(),
            async_execution=True,
        )

    @task
    def brand_match_task(self) -> Task:
        return Task(
            config=self.tasks_config["brand_match_task"],  # type: ignore[index]
            agent=self.brand_match_manager(),
            context=[
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
            ],
        )

    @task
    def orchestration_task(self) -> Task:
        return Task(
            config=self.tasks_config["orchestration_task"],  # type: ignore[index]
            agent=self.managing_agent(),
            async_execution=False,
        )

    # Unused manager/orchestration definitions are intentionally omitted.

    def _parse_task_output(self, output: Any) -> Dict[str, Any]:
        """Safely extract JSON from a task output."""
        if getattr(output, "json_dict", None):
            return output.json_dict  # type: ignore[return-value]
        raw = getattr(output, "raw", None)
        if isinstance(raw, (str, bytes)):
            try:
                return json.loads(raw)
            except Exception:
                pass
        return {"raw": raw}

    def run_orchestration(self, job_posting: dict) -> Dict[str, Any]:
        """Execute optimized pipeline: pre-filter → parallel brand matching → final recommendation."""

        def _dedupe(items: list[Any]) -> list[Any]:
            seen: set[Any] = set()
            ordered: list[Any] = []
            for item in items:
                if not item:
                    continue
                if item not in seen:
                    seen.add(item)
                    ordered.append(item)
            return ordered

        def _persona_label(agent_id: str) -> str:
            labels = {
                "pre_filter_agent": "Pre-filter",
                "brand_match_manager": "Brand alignment specialist",
            }
            if agent_id in labels:
                return labels[agent_id]
            return agent_id.replace("_", " ").title()

        crew = self.crew()
        job_str = json.dumps(job_posting, default=float)

        # Execute pre-filter first
        pre_filter_task = None
        brand_task = None
        
        for task in crew.tasks:
            if hasattr(task, 'config') and 'pre_filter_task' in str(task.config):
                pre_filter_task = task
            elif hasattr(task, 'config') and 'brand_match_task' in str(task.config):
                brand_task = task

        if not pre_filter_task or not brand_task:
            # Fallback to index-based access if we can't find by config
            pre_filter_task = crew.tasks[0]  # pre_filter_task is first
            brand_task = crew.tasks[-1]  # brand_match_task is last

        personas: list[Dict[str, Any]] = []
        tradeoffs: list[str] = []
        actions: list[str] = []
        sources: list[str] = []

        # Execute pre-filter analysis
        pre_output = pre_filter_task.execute_sync(context=job_str)
        pre_json = self._parse_task_output(pre_output)

        pre_recommend = bool(pre_json.get("recommend"))
        pre_reason = pre_json.get("reason") or pre_json.get("rationale")
        pre_reason_text = pre_reason or (
            "Passes basic requirements"
            if pre_recommend
            else "Failed basic requirements"
        )
        personas.append(
            {
                "id": "pre_filter_agent",
                "recommend": pre_recommend,
                "reason": pre_reason_text,
            }
        )
        sources.append("pre_filter_agent")

        # Early termination for pre-filter rejections
        if not pre_recommend:
            final_block = {
                "recommend": False,
                "rationale": pre_reason_text,
                "confidence": "high",
            }

            return JobPostingReviewOutput(
                job_intake=job_posting,
                pre_filter=pre_json,
                quick_fit=None, # Not used with new architecture
                brand_match=None,
                final=final_block,
                personas=personas,
                tradeoffs=[],  # Keep minimal for pre-filter rejections
                actions=[],    # Keep minimal for pre-filter rejections
                sources=sources,
            ).model_dump()

        # Execute brand matching (parallel specialist tasks + manager)
        brand_output = brand_task.execute_sync(context=job_str)
        brand_json = self._parse_task_output(brand_output)
        brand_has_structured = bool(brand_json) and set(brand_json.keys()) != {"raw"}

        if brand_has_structured:
            # Use brand_match_manager's recommendation and confidence directly
            brand_recommend = brand_json.get("recommend", False)
            brand_confidence = brand_json.get("confidence", "medium")
            brand_summary = brand_json.get("overall_summary", "Brand assessment completed")
            
            # Fallback for legacy format if new format not present
            if brand_summary == "Brand assessment completed":
                brand_summary = brand_json.get("alignment_summary", "Brand assessment completed")

            personas.append(
                {
                    "id": "brand_match_manager",
                    "recommend": brand_recommend,
                    "reason": brand_summary,
                }
            )
            sources.append("brand_match_manager")

            # Add tradeoffs based on score, not recommendation
            overall_score = brand_json.get("overall_alignment_score") or brand_json.get("brand_alignment_score")
            if isinstance(overall_score, (int, float)) and overall_score < 7:
                tradeoffs.append("Brand alignment concerns")
                
            # Include detailed brand analysis data
            if "north_star" in brand_json:
                brand_json["detailed_analysis"] = True

        # Final decision logic - use brand_match_manager's decision
        if brand_has_structured:
            final_recommend = brand_recommend
            confidence = brand_confidence
        else:
            # Fallback to pre-filter only if no brand matching
            final_recommend = personas[0].get("recommend", False) if personas else False
            confidence = "medium"

        # Concise rationale - key reasons
        key_reasons = []
        for persona in personas:
            if persona.get("reason") and len(key_reasons) < 2:  # Limit to 2 key reasons
                key_reasons.append(persona["reason"])
        
        rationale = ". ".join(key_reasons) or "Assessment completed"

        final_block = {
            "recommend": final_recommend,
            "rationale": rationale,
            "confidence": confidence,
        }

        return JobPostingReviewOutput(
            job_intake=job_posting,
            pre_filter=pre_json,
            quick_fit=None,  # Not used with new architecture
            brand_match=brand_json,
            final=final_block,
            personas=personas,
            tradeoffs=_dedupe(tradeoffs),
            actions=_dedupe(actions),
            sources=_dedupe(sources),
        ).model_dump()

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.pre_filter_agent(),
                # Brand dimension specialists
                self.north_star_matcher(),
                self.trajectory_mastery_matcher(),
                self.values_compass_matcher(),
                self.lifestyle_alignment_matcher(),
                self.compensation_philosophy_matcher(),
                self.brand_match_manager(),
            ],
            tasks=[
                self.pre_filter_task(),
                # Parallel brand dimension tasks
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
                # Manager task that combines parallel results
                self.brand_match_task(),
            ],
            process=Process.sequential,  # Tasks will handle async execution internally
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
    """Run the job posting review crew using explicit orchestration."""
    try:
        crew = JobPostingReviewCrew()
        return crew.run_orchestration(job_posting_data)
    except Exception as e:
        job_hash = hashlib.md5(
            json.dumps(job_posting_data, sort_keys=True, default=float).encode()
        ).hexdigest()
        return {
            "job_id": f"error_{job_hash[:8]}",
            "correlation_id": correlation_id,
            "error": str(e),
        }
if __name__ == "__main__":
    sample = {
        "title": "Senior Machine Learning Engineer",
        "company": "Acme Corp",
        "description": "Build ML systems",
    }
    print(JobPostingReviewCrew().run_orchestration(sample))
