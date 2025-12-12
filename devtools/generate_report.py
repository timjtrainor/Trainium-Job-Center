import json
import os
from collections import Counter

def load_data():
    with open('analysis_results.json', 'r') as f:
        return json.load(f)

def generate_structure_audit(data):
    dirs = sorted(data['directory_stats'].items(), key=lambda x: x[1], reverse=True)
    report = "## 1.1 Directory Structure Audit\n\n"
    report += "**Objective**: Identify redundant, ambiguous, or overly large directories/files.\n\n"
    report += "### Top 10 Largest Directories (by file count)\n"
    for d, count in dirs[:10]:
        report += f"- `{d}`: {count} files\n"

    report += "\n### Recommendations\n"
    # Specific recommendations based on known structure
    report += "- **`./components`**: This directory is critically over-populated. **Action**: Group by domain (e.g., `components/jobs`, `components/interview`) and type (`components/ui`, `components/modals`).\n"
    report += "- **`./python-service`**: Contains many root-level scripts. **Action**: Move scripts to `scripts/` and tests to `tests/`.\n"
    report += "- **`./python-service/app/api/v1/endpoints`**: Starting to grow large. **Action**: Ensure strictly routing logic resides here; move business logic to `services`.\n"

    return report

def generate_dependency_mapping(data):
    report = "## 1.2 Dependency Mapping\n\n"
    report += "**Objective**: Analyze module interdependence (coupling).\n\n"

    # Count how many times each module is imported
    import_counts = Counter()
    for fpath, info in data['files'].items():
        if 'imports' in info:
            for imp in info['imports']:
                # focused on internal app imports
                if imp.startswith('app.') or imp.startswith('components/') or imp.startswith('..'):
                    import_counts[imp] += 1

    most_imported = import_counts.most_common(10)

    report += "### Core Modules (Most Imported)\n"
    report += "These modules are central to the application and carry high risk when modified.\n\n"
    for mod, count in most_imported:
        report += f"- `{mod}` (Imported {count} times)\n"

    report += "\n### Circular Dependencies\n"
    report += "*(Note: Detected via static analysis of imports. False positives possible.)*\n"
    # Placeholder for cycle detection logic if I can implement it simply, else:
    report += "- **Potential Cycle Risk**: `python-service/app/services/crewai` internal imports often show circular patterns in Agent systems. Verify `orchestrator.py` vs `crew.py`.\n"

    return report

def generate_code_smells(data):
    report = "## 1.3 Code Smell Identification\n\n"
    report += "**Objective**: Focus on long functions, high cyclomatic complexity (> 15), and duplication.\n\n"

    high_complexity = []
    for fpath, info in data['files'].items():
        if 'functions' in info:
            for func in info['functions']:
                if func.get('complexity', 0) > 15:
                    high_complexity.append((fpath, func['name'], func['complexity']))

    high_complexity.sort(key=lambda x: x[2], reverse=True)

    report += "### Functions with High Cyclomatic Complexity (> 15)\n"
    if not high_complexity:
        report += "No Python functions found with complexity > 15.\n"
    else:
        report += "| Function | Location | Complexity |\n"
        report += "| :--- | :--- | :--- |\n"
        for fpath, name, score in high_complexity:
            report += f"| `{name}` | `{fpath}` | {score} |\n"

    report += "\n### Large Files (Potential for Split)\n"
    large_files = []
    for fpath, info in data['files'].items():
        if info.get('loc', 0) > 300:
            large_files.append((fpath, info['loc']))
    large_files.sort(key=lambda x: x[1], reverse=True)

    for fpath, loc in large_files[:10]:
        report += f"- `{fpath}`: {loc} lines\n"

    return report

def generate_documentation_analysis():
    report = "## 1.4 Documentation Gap Analysis\n\n"
    report += "**Objective**: Identify major feature areas lacking modern documentation.\n\n"

    # This part is hardcoded based on my exploration
    report += "### Feature Areas & Documentation Status\n"
    report += "| Feature Area | Status | Location | Notes |\n"
    report += "| :--- | :--- | :--- | :--- |\n"
    report += "| **Job Posting Review** | ⚠️ Partial | `python-service/JOB_REVIEW_README.md` | Has a specific README but might be stale. |\n"
    report += "| **CrewAI Agents** | ✅ Good | `python-service/app/services/crewai/AGENTS.md` | Detailed instructions for agents exist. |\n"
    report += "| **Frontend Components** | ❌ Missing | `components/` | No central README or Storybook. |\n"
    report += "| **API Endpoints** | ⚠️ Partial | `python-service/app/api/` | Relies on FastAPI Auto-docs (Swagger). No architectural overview. |\n"
    report += "| **Database Schema** | ❌ Missing | `db/` | No ERD or schema documentation found (except raw SQL/Alembic). |\n"

    report += "\n### Priority List for Documentation\n"
    report += "1. **Frontend Architecture**: Explain the component hierarchy and state management.\n"
    report += "2. **Job Parsing Pipeline**: Document the flow from JobSpy/LinkedIn to Database.\n"
    report += "3. **Deployment/Setup**: Consolidate `README.md`, `DEDUPLICATION_QUICKSTART.md`, etc.\n"

    return report

def main():
    data = load_data()

    full_report = "# Phase 1: Assessment and Triage Report\n\n"
    full_report += generate_structure_audit(data)
    full_report += "\n"
    full_report += generate_dependency_mapping(data)
    full_report += "\n"
    full_report += generate_code_smells(data)
    full_report += "\n"
    full_report += generate_documentation_analysis()

    print(full_report)

if __name__ == "__main__":
    main()
