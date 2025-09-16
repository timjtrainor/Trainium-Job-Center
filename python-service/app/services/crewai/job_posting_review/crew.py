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

    # === Specialists (job_intake_agent removed - data already structured) ===
    # job_intake_agent removed - job data is already structured from database

    @agent
    def pre_filter_agent(self) -> Agent:
        return Agent(config=self.agents_config["pre_filter_agent"])  # type: ignore[index]

    @agent
    def quick_fit_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["quick_fit_analyst"],  # type: ignore[index]
        )

    @agent
    def brand_framework_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_framework_matcher"],  # type: ignore[index]
            tools=get_career_brand_tools(),
        )

    # === Legacy Manager (unused) ===
    @agent
    def managing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["managing_agent"],  # type: ignore[index]
            allow_delegation=True,
        )

    # === Tasks (intake_task removed - data already structured) ===
    # intake_task removed - job data is already structured from database

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
        """Execute optimized pipeline: pre-filter → quick-fit → brand match (if needed)."""

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
                "quick_fit_analyst": "Quick fit analyst",
                "brand_framework_matcher": "Brand matcher",
            }
            if agent_id in labels:
                return labels[agent_id]
            return agent_id.replace("_", " ").title()

        crew = self.crew()
        pre, quick, brand = crew.tasks  # Skip intake task - data already structured
        job_str = json.dumps(job_posting, default=float)

        # Start directly with pre-filter since job data is already structured
        pre_output = pre.execute_sync(context=job_str)
        pre_json = self._parse_task_output(pre_output)

        personas: list[Dict[str, Any]] = []
        tradeoffs: list[str] = []
        actions: list[str] = []
        sources: list[str] = []

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
                job_intake=job_posting,  # Use original data since intake agent removed
                pre_filter=pre_json,
                quick_fit=None,
                brand_match=None,
                final=final_block,
                personas=personas,
                tradeoffs=[],  # Keep minimal for pre-filter rejections
                actions=[],    # Keep minimal for pre-filter rejections
                sources=sources,
            ).model_dump()

        # Continue with quick fit analysis
        quick_output = quick.execute_sync(context=job_str)
        quick_json = self._parse_task_output(quick_output)

        quick_has_structured = bool(quick_json) and set(quick_json.keys()) != {"raw"}
        quick_recommendation = (
            str(quick_json.get("quick_recommendation", "")).lower()
            if quick_has_structured
            else ""
        )
        quick_overall = (
            str(quick_json.get("overall_fit", "")).lower()
            if quick_has_structured
            else ""
        )

        # Use concise reason from quick fit
        quick_reason = quick_json.get("key_reason", "Quick assessment completed")
        if not quick_reason and quick_overall:
            quick_reason = f"Overall fit: {quick_overall}"

        quick_persona_recommend = True
        if quick_recommendation == "reject" or quick_overall == "low":
            quick_persona_recommend = False
        elif quick_recommendation == "review_deeper":
            quick_persona_recommend = False

        if quick_has_structured:
            personas.append(
                {
                    "id": "quick_fit_analyst",
                    "recommend": quick_persona_recommend,
                    "reason": quick_reason,
                }
            )
            sources.append("quick_fit_analyst")

            # Minimal tradeoffs/actions for conciseness
            if quick_overall == "low":
                tradeoffs.append("Low overall fit rating")
            if quick_recommendation == "approve":
                actions.append("Proceed with application")
            elif quick_recommendation == "reject":
                actions.append("Skip this opportunity")

        # Brand match only if needed
        brand_json = {}
        brand_has_structured = False
        
        if quick_recommendation == "review_deeper":
            brand_output = brand.execute_sync(context=job_str)
            brand_json = self._parse_task_output(brand_output)
            brand_has_structured = bool(brand_json) and set(brand_json.keys()) != {"raw"}

            if brand_has_structured:
                brand_score = brand_json.get("brand_alignment_score")
                brand_summary = brand_json.get("alignment_summary", "Brand assessment completed")
                
                brand_support = True
                if isinstance(brand_score, (int, float)) and brand_score <= 4:
                    brand_support = False

                personas.append(
                    {
                        "id": "brand_framework_matcher",
                        "recommend": brand_support,
                        "reason": brand_summary,
                    }
                )
                sources.append("brand_framework_matcher")

                if isinstance(brand_score, (int, float)) and brand_score < 7:
                    tradeoffs.append("Brand alignment concerns")

        # Final decision logic
        executed_personas = [p for p in personas if p.get("recommend") is not None]
        total_votes = len(executed_personas)
        positive_votes = sum(1 for p in executed_personas if p["recommend"])

        final_recommend = positive_votes >= (total_votes / 2)
        
        # Override based on specific recommendations
        if quick_recommendation == "reject":
            final_recommend = False
        elif quick_recommendation == "review_deeper" and brand_has_structured:
            brand_score = brand_json.get("brand_alignment_score")
            if isinstance(brand_score, (int, float)) and brand_score <= 4:
                final_recommend = False

        # Concise confidence calculation
        if total_votes <= 1:
            confidence = "medium"
        else:
            consensus_ratio = abs(positive_votes * 2 - total_votes) / total_votes
            confidence = "high" if consensus_ratio >= 0.5 else "medium"

        # Concise rationale - just the key reasons
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
            job_intake=job_posting,  # Use original data since intake agent removed
            pre_filter=pre_json,
            quick_fit=quick_json,
            brand_match=brand_json,
            final=final_block,
            personas=personas,
            tradeoffs=_dedupe(tradeoffs),
            actions=_dedupe(actions),
            sources=_dedupe(sources),
        ).model_dump()

    # === Crew (optimized without job_intake_agent) ===
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.pre_filter_agent(),
                self.quick_fit_analyst(),
                self.brand_framework_matcher(),
            ],
            tasks=[
                self.pre_filter_task(),
                self.quick_fit_task(),
                self.brand_match_task(),
            ],
            process=Process.sequential,
            verbose=True,  # Enable verbose to ensure proper EventBus initialization
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
