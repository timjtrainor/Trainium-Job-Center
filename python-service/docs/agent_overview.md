# Agent Overview

## CrewAI Job Review Agents

| Agent | Inputs | Outputs | Decision Lens | Source |
|-------|--------|---------|---------------|--------|
| SkillsAnalysisAgent | Job description and title | Required skills, preferred skills, experience level, education requirements | Evaluates skills and requirements | [crew.py](../app/services/crewai/job_review/crew.py#L57-L83) |
| CompensationAnalysisAgent | Salary range and description | Salary analysis, benefits mentioned | Reviews compensation and benefits | [crew.py](../app/services/crewai/job_review/crew.py#L177-L200) |
| QualityAssessmentAgent | Job description, title, company | Job quality score, completeness, red and green flags | Checks posting quality and flags | [crew.py](../app/services/crewai/job_review/crew.py#L268-L292) |

## Persona Catalog Agents

### Advisory

| Agent | Inputs | Outputs | Decision Lens | Source |
|-------|--------|---------|---------------|--------|
| headhunter | Job posting details and market data | Market intelligence, future demand | Does this role give me an edge before others see it? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L2-L10) |
| recruiter | Resume and job description | ATS check, resume alignment | Would a recruiter put me in the 'yes' pile? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L11-L19) |
| career_coach | Career history and goals | Trajectory mapping, skill stacking advice | Will this role move me closer to my ultimate career goals? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L20-L28) |
| life_coach | Job offer and lifestyle priorities | Balance assessment, fulfillment check | Will this job help me live the life I want? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L29-L37) |
| hiring_manager | Candidate profile | Outcome review, team fit insights | Would I hire this person to solve my problems? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L38-L46) |
| peer_mentor | Company culture cues | Culture check, daily work insights | Will I actually enjoy working here? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L47-L55) |
| negotiator | Offer details | Compensation analysis, leverage advice | Is this job worth it financially, and can I push for more? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L56-L64) |
| data_analyst | Salary and company metrics | Salary benchmarks, company metrics | Does the data suggest this is a smart move? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L65-L73) |
| researcher | Job questions | Quick facts via Google search | What quick facts can guide this decision? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L74-L82) |
| strategist | Industry trends | Trend analysis, AI adoption review | Is this role positioned for the future? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L83-L91) |
| skeptic | Job description | Risk assessment, red flag detection | What's the catch? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L92-L100) |
| optimizer | Resume and pitch | Resume tweaks, pitch sharpening | How can I raise my chances of landing this role? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L101-L109) |
| stakeholder | Collaboration context | Collaboration check, trust building | Would I want this person as a partner? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L110-L118) |
| technical_leader | Engineering plans | Feasibility review, engineering credibility | Can this person help us ship sustainably? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L119-L127) |
| ceo | Leadership profile | Vision alignment, leadership review | Would I trust this person in front of customers, investors, and the board? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L128-L136) |

### Motivational

| Agent | Inputs | Outputs | Decision Lens | Source |
|-------|--------|---------|---------------|--------|
| builder | Career path details | Growth mapping, leadership path | Does this role move me closer to mastery? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L138-L146) |
| maximizer | Compensation package | Pay comparison, equity review | Does this maximize my financial return? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L147-L155) |
| harmonizer | Company values and culture | Culture fit, values alignment | Will I feel at home here? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L156-L164) |
| pathfinder | Lifestyle needs | Lifestyle check, flexibility review | Does this role fit into the life I want to live? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L165-L173) |
| adventurer | Purpose motivations | Purpose alignment, impact estimate | Will my work here matter to the world? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L174-L182) |

### Decision

| Agent | Inputs | Outputs | Decision Lens | Source |
|-------|--------|---------|---------------|--------|
| visionary | Career aspirations | North star check, purpose projection | Does this take me closer to my long-term destiny? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L184-L192) |
| realist | Practical constraints | Logistics check, cost of living review | Can this actually work in real life? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L193-L201) |
| guardian | Stability factors | Stability review, resilience check | Will this job safeguard my future? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L202-L210) |

### Judge

| Agent | Inputs | Outputs | Decision Lens | Source |
|-------|--------|---------|---------------|--------|
| judge | All prior agent insights | Verdict synthesis, trade-off analysis | Considering everything, is this role truly worth pursuing? | [persona_catalog.yaml](../app/services/persona_catalog.yaml#L212-L220) |
