"""Utilities for loading persona catalog and creating persona objects."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import os
import yaml


@dataclass
class Persona:
    id: str
    role: str
    goal: str
    backstory: str
    decision_lens: str
    tone: str
    capabilities: List[str]
    crew_manifest_ref: str
    models: List[Dict[str, str]]


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
                persona = Persona(
                    id=item["id"],
                    role=item.get("role", ""),
                    goal=item.get("goal", ""),
                    backstory=item.get("backstory", ""),
                    decision_lens=item.get("decision_lens", ""),
                    tone=item.get("tone", ""),
                    capabilities=item.get("capabilities", []),
                    crew_manifest_ref=item.get("crew_manifest_ref", ""),
                    models=models,
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
