import hashlib
import json
import re
from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ....schemas.job_posting_review import (JobPostingReviewOutput)


from ..tools.chroma_search import (
    #chroma_search,
    #search_job_postings,
    #search_company_profiles,
    #contextual_job_analysis,
    search_career_brands
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
        )

    @agent
    def brand_framework_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_framework_matcher"],  # type: ignore[index]
            tools=[search_career_brands],
        )

    # === Legacy Manager (unused) ===
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
        """Execute pipeline: intake → pre-filter → quick-fit → brand match."""

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
        intake, pre, quick, brand = crew.tasks
        job_str = json.dumps(job_posting, default=float)

        intake_output = intake.execute_sync(context=job_str)
        intake_json = self._parse_task_output(intake_output)

        pre_output = pre.execute_sync(context=json.dumps(intake_json, default=float))
        pre_json = self._parse_task_output(pre_output)

        personas: list[Dict[str, Any]] = []
        tradeoffs: list[str] = []
        actions: list[str] = []
        sources: list[str] = []

        pre_recommend = bool(pre_json.get("recommend"))
        pre_reason = pre_json.get("reason") or pre_json.get("rationale")
        pre_reason_text = pre_reason or (
            "No salary or seniority guardrails were triggered."
            if pre_recommend
            else "Failed salary or seniority guardrails."
        )
        personas.append(
            {
                "id": "pre_filter_agent",
                "recommend": pre_recommend,
                "reason": pre_reason_text,
            }
        )
        sources.append("pre_filter_agent")

        if not pre_recommend:
            lower_reason = pre_reason_text.lower()
            if "salary" in lower_reason:
                tradeoffs.append("Compensation does not meet minimum salary requirements.")
                actions.append("Target roles with stronger compensation before applying.")
            elif "seniority" in lower_reason:
                tradeoffs.append("Role seniority conflicts with required experience level.")
                actions.append("Focus on senior-level opportunities to satisfy guardrails.")
            else:
                tradeoffs.append("Failed automated pre-filter evaluation.")
                actions.append("Review pre-filter criteria against the job details.")

            final_block = {
                "recommend": False,
                "rationale": f"Pre-filter rejection: {pre_reason_text}",
                "confidence": "high",
            }

            return JobPostingReviewOutput(
                job_intake=intake_json,
                pre_filter=pre_json,
                quick_fit=None,
                brand_match=None,
                final=final_block,
                personas=personas,
                tradeoffs=_dedupe(tradeoffs),
                actions=_dedupe(actions),
                sources=_dedupe(sources),
            ).model_dump()

        quick_output = quick.execute_sync(context=json.dumps(intake_json, default=float))
        quick_json = self._parse_task_output(quick_output)

        brand_output = brand.execute_sync(context=json.dumps(intake_json, default=float))
        brand_json = self._parse_task_output(brand_output)

        quick_has_structured = bool(quick_json) and set(quick_json.keys()) != {"raw"}
        brand_has_structured = bool(brand_json) and set(brand_json.keys()) != {"raw"}

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
        quick_reason_parts = []
        if quick_overall:
            quick_reason_parts.append(f"overall fit {quick_overall}")
        if quick_recommendation:
            quick_reason_parts.append(f"recommends {quick_recommendation.replace('_', ' ')}")
        quick_reason = "; ".join(quick_reason_parts) or "Quick fit analyst shared limited feedback."

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

            if quick_overall == "medium":
                tradeoffs.append("Quick fit analyst rated the role as a medium overall fit.")
            elif quick_overall == "low":
                tradeoffs.append("Quick fit analyst rated the role as a low overall fit.")

            comp_score = quick_json.get("compensation_score")
            if isinstance(comp_score, (int, float)) and comp_score < 7:
                tradeoffs.append("Compensation score below 7/10.")

            if quick_recommendation == "approve":
                actions.append("Move forward with the application process.")
            elif quick_recommendation == "review_deeper":
                actions.append("Schedule a deeper evaluation before committing.")
            elif quick_recommendation == "reject":
                actions.append("Skip applying based on quick fit assessment.")

        if brand_has_structured:
            brand_notes = brand_json.get("alignment_notes") or []
            brand_score = brand_json.get("brand_alignment_score")
        else:
            brand_notes = []
            brand_score = None
        brand_reason_parts = []
        if isinstance(brand_score, (int, float)):
            brand_reason_parts.append(f"brand alignment score {brand_score}/10")
        if brand_notes:
            brand_reason_parts.append(brand_notes[0])
        brand_reason = "; ".join(brand_reason_parts) or "Brand matcher provided limited feedback."

        brand_support = True
        if isinstance(brand_score, (int, float)):
            if brand_score <= 4:
                brand_support = False
            elif brand_score >= 7:
                brand_support = True
            else:
                brand_support = True

        if brand_has_structured:
            personas.append(
                {
                    "id": "brand_framework_matcher",
                    "recommend": brand_support,
                    "reason": brand_reason,
                }
            )
            sources.append("brand_framework_matcher")

            if isinstance(brand_score, (int, float)) and brand_score < 7:
                tradeoffs.append(
                    f"Brand alignment score {brand_score}/10 indicates potential fit concerns."
                )
            if isinstance(brand_score, (int, float)) and brand_score >= 7:
                actions.append("Leverage strong brand alignment during outreach.")

            for note in brand_notes[1:]:
                tradeoffs.append(note)

        executed_personas = [p for p in personas if p.get("recommend") is not None]
        total_votes = len(executed_personas)
        positive_votes = sum(1 for p in executed_personas if p["recommend"])
        negative_votes = total_votes - positive_votes

        majority_recommend = positive_votes >= negative_votes

        final_recommend = majority_recommend
        if quick_recommendation == "reject":
            final_recommend = False
        elif quick_recommendation == "review_deeper":
            if isinstance(brand_score, (int, float)):
                final_recommend = brand_score >= 7
            else:
                final_recommend = False

        if final_recommend and isinstance(brand_score, (int, float)) and brand_score <= 4:
            final_recommend = False

        if total_votes <= 1:
            confidence = "medium" if final_recommend else "high"
        else:
            consensus_ratio = abs(positive_votes - negative_votes) / total_votes
            if consensus_ratio >= 0.66:
                confidence = "high"
            elif consensus_ratio >= 0.33:
                confidence = "medium"
            else:
                confidence = "low"

        rationale_parts = []
        for persona in personas:
            label = _persona_label(persona["id"])
            reason_text = persona.get("reason")
            if reason_text:
                rationale_parts.append(f"{label}: {reason_text}")
        rationale = " ".join(rationale_parts) or "No detailed rationale provided."

        final_block = {
            "recommend": final_recommend,
            "rationale": rationale,
            "confidence": confidence,
        }

        return JobPostingReviewOutput(
            job_intake=intake_json,
            pre_filter=pre_json,
            quick_fit=quick_json,
            brand_match=brand_json,
            final=final_block,
            personas=personas,
            tradeoffs=_dedupe(tradeoffs),
            actions=_dedupe(actions),
            sources=_dedupe(sources),
        ).model_dump()

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
                self.intake_task(),
                self.pre_filter_task(),
                self.quick_fit_task(),
                self.brand_match_task(),
            ],
            process=Process.sequential,
            verbose=False,
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
