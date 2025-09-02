"""Utilities for loading persona catalog and creating persona objects."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import yaml


@dataclass
class Persona:
    id: str
    summary: str
    decision_lens: str
    tone: str
    capabilities: List[str]
    crew_manifest_ref: str
    provider: str


class PersonaCatalog:
    """Loads personas from YAML catalog."""

    def __init__(self, path: Path):
        data = yaml.safe_load(Path(path).read_text())
        self.personas: Dict[str, Persona] = {}
        self.groups: Dict[str, List[str]] = {}
        for group, items in data.items():
            ids = []
            for item in items:
                persona = Persona(
                    id=item["id"],
                    summary=item.get("summary", ""),
                    decision_lens=item.get("decision_lens", ""),
                    tone=item.get("tone", ""),
                    capabilities=item.get("capabilities", []),
                    crew_manifest_ref=item.get("crew_manifest_ref", ""),
                    provider=item.get("models", [{}])[0].get("provider", "")
                )
                self.personas[persona.id] = persona
                ids.append(persona.id)
            self.groups[group] = ids

    def get_personas_by_group(self, group: str) -> List[Persona]:
        """Return list of personas for a group."""
        return [self.personas[i] for i in self.groups.get(group, [])]

    def get(self, persona_id: str) -> Persona:
        return self.personas[persona_id]
