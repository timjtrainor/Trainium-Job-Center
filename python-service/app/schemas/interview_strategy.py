from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

class DiagnosticIntel(BaseModel):
    failure_state_portfolio: str = Field(description="The 'failure state' or specific problem identified from research.")
    composite_antidote_persona: str = Field(description="Diagnostic evidence connecting the problem to the candidate's mastered capability.")
    experience_anchoring: str = Field(description="A specific experience from the candidate that anchors the antidote.")
    mandate_quadrant: str = Field(description="The strategic quadrant for this mandate.")
    functional_gravity_stack: List[str] = Field(description="The core functional areas of focus.")
    strategic_friction_hooks: List[str] = Field(description="Hooks for strategic discovery.")

class EconomicLogicGates(BaseModel):
    primary_value_driver: str = Field(description="The main driver of value for this role.")
    metric_hierarchy: List[str] = Field(description="Key metrics for success.")

class ContentIntelligence(BaseModel):
    vocabulary_mirror: List[str] = Field(description="Key industry or company vocabulary.")
    must_have_tech_signals: List[str] = Field(description="Critical technical signals.")

class JobProblemAnalysis(BaseModel):
    diagnostic_intel: DiagnosticIntel
    economic_logic_gates: EconomicLogicGates
    content_intelligence: ContentIntelligence

class InterviewStrategy(BaseModel):
    """Overall Application Strategy (Strategy Studio)"""
    job_problem_analysis: JobProblemAnalysis
    strategic_fit_score: int
    assumed_requirements: List[str]

class ScriptedOpening(BaseModel):
    hook: str = Field(description="The 'Company Friction' or specific problem identified from research. Peer-to-peer tone.")
    bridge: str = Field(description="Diagnostic evidence connecting the problem to the candidate's mastered capability.")
    pivot: str = Field(description="A strategic discovery question to shift the focus to a solution discussion.")

class DiagnosticRow(BaseModel):
    friction_point: str = Field(description="A specific pain point or headwind facing the company.")
    proposed_intervention: str = Field(description="The candidate's specific past experience that addresses this pain point.")

class ExpectedQuestion(BaseModel):
    question: str = Field(description="A likely question this specific interviewer will ask based on their persona.")
    strategic_answer: str = Field(description="The suggested peer-to-peer response mapping back to a diagnostic intervention.")
    rationale: str = Field(description="Why this interviewer is likely to ask this and what they are looking for.")

class InterviewerIntel(BaseModel):
    name: str
    role: str
    persona_type: Literal['Talent Sifter', 'The Owner', 'Deep Diver', 'Visionary']
    expected_questions: List[ExpectedQuestion]

class InterviewPrep(BaseModel):
    """Individual Interview Blueprint (Consultant Blueprint)"""
    scripted_opening: ScriptedOpening
    diagnostic_matrix: List[DiagnosticRow]
    interviewer_intel: List[InterviewerIntel] = Field(default_factory=list)
