"""Utilities for loading persona catalog and creating persona objects."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any
import os
import yaml


@dataclass
class Persona:
    id: str
    role: str
    goal: str
    backstory: str
    max_iter: int
    max_execution_time: int
    tools: List[str]
    models: List[Dict[str, str]]
    # Metadata fields
    decision_lens: str
    tone: str
    capabilities: List[str]
    crew_manifest_ref: str


class PersonaCatalog:
    """Loads personas from YAML catalog."""

    def __init__(self, path: Path):
        data = yaml.safe_load(Path(path).read_text())
        self.personas: Dict[str, Persona] = {}
        self.groups: Dict[str, List[str]] = {}

        default_models = self._parse_llm_preference(os.getenv("LLM_PREFERENCE", ""))

        for group, items in data.items():
            ids = []
            for item in items:
                models = (
                    item["models"]
                    if "models" in item
                    else [dict(m) for m in default_models]
                )
                
                # Extract metadata fields
                metadata = item.get("metadata", {})
                
                persona = Persona(
                    id=item["id"],
                    role=item.get("role", ""),
                    goal=item.get("goal", ""),
                    backstory=item.get("backstory", ""),
                    max_iter=item.get("max_iter", 1),
                    max_execution_time=item.get("max_execution_time", 30),
                    tools=item.get("tools", []),
                    models=models,
                    # Metadata fields with defaults
                    decision_lens=metadata.get("decision_lens", ""),
                    tone=metadata.get("tone", ""),
                    capabilities=metadata.get("capabilities", []),
                    crew_manifest_ref=metadata.get("crew_manifest_ref", ""),
                )
                self.personas[persona.id] = persona
                ids.append(persona.id)
            self.groups[group] = ids

    @staticmethod
    def _parse_llm_preference(preference: str) -> List[Dict[str, str]]:
        """Parse LLM_PREFERENCE env var into provider/model pairs."""
        models: List[Dict[str, str]] = []
        for pref in preference.split(","):
            pref = pref.strip()
            if not pref:
                continue
            if ":" in pref:
                provider, model = pref.split(":", 1)
                models.append({"provider": provider.strip(), "model": model.strip()})
        return models

    def get_personas_by_group(self, group: str) -> List[Persona]:
        """Return list of personas for a group."""
        return [self.personas[i] for i in self.groups.get(group, [])]

    def get(self, persona_id: str) -> Persona:
        return self.personas[persona_id]

    def get_models(self, persona_id: str) -> List[Dict[str, str]]:
        """Return available models for a persona."""
        return self.get(persona_id).models

    def get_default_model(self, persona_id: str) -> Dict[str, str]:
        """Return the default provider/model pair for a persona."""
        models = self.get_models(persona_id)
        return models[0] if models else {"provider": "", "model": ""}

    def get_tools(self, persona_id: str) -> List[str]:
        """Return tool names for a persona."""
        return self.get(persona_id).tools

    def create_agent_config(self, persona_id: str) -> Dict[str, Any]:
        """Create agent configuration dictionary from persona data."""
        persona = self.get(persona_id)
        return {
            "role": persona.role,
            "goal": persona.goal,
            "backstory": persona.backstory,
            "max_iter": persona.max_iter,
            "max_execution_time": persona.max_execution_time,
            "tools": persona.tools,  # Tool names - actual instances need to be resolved in Python
            "verbose": True,  # CrewAI standard parameter
        }
