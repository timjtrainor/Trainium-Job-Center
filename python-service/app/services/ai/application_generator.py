"""AI-powered application generation service for LinkedIn workflow."""

import json
from typing import Dict, Any, List, Optional
from loguru import logger
from google import genai

from ...core.config import get_settings

settings = get_settings()


class ApplicationGeneratorService:
    """Service for generating application content using AI."""

    def __init__(self):
        """Initialize the AI service with Gemini."""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = 'gemini-2.0-flash-exp'

    async def generate_resume_tailoring_data(
        self,
        job_description: str,
        full_resume_json: Dict[str, Any],
        resume_summary: str,
        company_context: Dict[str, Any],
        narrative: Dict[str, Any],
        job_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate resume tailoring suggestions using AI.

        Args:
            job_description: Full job description
            full_resume_json: Complete resume data
            resume_summary: Current resume summary
            company_context: Company mission, values, etc.
            narrative: User's positioning/mastery
            job_analysis: Optional job analysis data

        Returns:
            Dict with keywords, guidance, processed experience, suggestions
        """

        # Build the prompt
        prompt = f"""
You are an expert resume optimization engine. Your task is to analyze a candidate's full resume against a specific job description and its strategic context. You will return a single, valid JSON object that includes keywords, guidance, and resume tailoring suggestions.

**CONTEXT:**
- Job Description: {job_description}
- Candidate's Original Resume JSON: {json.dumps(full_resume_json)}
- Candidate's Original Summary: {resume_summary}
- Target Company Mission: {company_context.get('mission', {}).get('text', 'Not provided')}
- Target Company Values: {company_context.get('values', {}).get('text', 'Not provided')}
- Candidate's Positioning: {narrative.get('positioning_statement', 'Not provided')}
- Candidate's Signature Capability: {narrative.get('signature_capability', 'Not provided')}

**INSTRUCTIONS:**

**PART 1: KEYWORDS & GUIDANCE**
First, generate keywords and strategic guidance based on the job description.
- **Keywords**: Identify and categorize 'hard_keywords' and 'soft_keywords'. For each, provide keyword, frequency, emphasis, reason, is_required, match_strength, resume_boost.
- **Guidance**: Provide strategic advice for the resume summary and bullets.

**PART 2: RESUME TAILORING**
Then, use the keywords and guidance you just generated to perform the following tailoring tasks:
- **Executive Summary**: Generate a single, powerful executive summary. Provide a `headline` (max 8 words) and a `paragraph` (75-100 words).
- **Work Experience Processing**: For each accomplishment in the resume, provide:
    - `bucket_category`: A short label (1-2 words) that categorizes the skill/impact (e.g., "Stakeholder Alignment", "Cloud Architecture").
    - `description`: The tailored text of the accomplishment.
    - `relevance_score`, `original_score`, and `keyword_suggestions`.
- **Skills**: Suggest differentiating capabilities and domain expertise.
    - `comprehensive_skills`: Create a comprehensive FLAT LIST of 15-20 relevant, differentiating skills.
    - `ai_selected_skills`: From the comprehensive list, pre-select the 9 most critical skills for this specific job.
- **Missing Keywords**: Identify any `hard_keywords` that are NOT found in the original resume.

**PART 3: ALIGNMENT SCORE**
- **Initial Alignment Score**: Provide an `initial_alignment_score` as a float from 0.0 to 10.0.

**OUTPUT FORMAT:**

Return ONLY a single, valid JSON object with all the following top-level keys. No markdown, no extra text.

{{
  "keywords": {{
    "hard_keywords": [
      {{ "keyword": "...", "frequency": 0, "emphasis": false, "reason": "...", "is_required": false, "match_strength": 0.0, "resume_boost": false }}
    ],
    "soft_keywords": [
      {{ "keyword": "...", "frequency": 0, "emphasis": false, "reason": "...", "is_required": false, "match_strength": 0.0, "resume_boost": false }}
    ]
  }},
  "guidance": {{
    "summary": ["...", "..."],
    "bullets": ["...", "..."],
    "keys": ["...", "..."]
  }},
  "processed_work_experience": [
    {{
       "company_name": "...",
       "job_title": "...",
       "accomplishments": [
         {{
           "bucket_category": "...",
           "description": "...",
           "relevance_score": 0.0,
           "original_score": {{ "overall_score": 0.0, "clarity": 0.0, "drama": 0.0 }},
           "keyword_suggestions": ["..."]
         }}
       ]
    }}
  ],
  "summary": {{
    "headline": "...",
    "paragraph": "..."
  }},
  "comprehensive_skills": [...],
  "ai_selected_skills": [...],
  "missing_keywords": [...],
  "initial_alignment_score": 8.2
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            result_text = response.text.strip()

            # Clean response (remove markdown if present)
            if result_text.startswith('```json'):
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif result_text.startswith('```'):
                result_text = result_text.split('```')[1].split('```')[0].strip()

            result = json.loads(result_text)
            logger.info("Successfully generated resume tailoring data")
            return result

        except Exception as e:
            logger.error(f"Failed to generate resume tailoring data: {e}")
            raise

    async def generate_application_message(
        self,
        job_title: str,
        job_description: str,
        company_context: Dict[str, Any],
        narrative: Dict[str, Any],
        resume_summary: str
    ) -> str:
        """
        Generate a compelling application message.

        Args:
            job_title: Target job title
            job_description: Full job description
            company_context: Company mission, values, etc.
            narrative: User's positioning/mastery
            resume_summary: Resume summary text

        Returns:
            Generated application message (under 150 words)
        """

        prompt = f"""
You are a career strategist and expert copywriter. Your task is to write a compelling, concise message to the hiring team for a job application.

The tone must be professional, confident, and direct. The message must be short (under 150 words).

**CONTEXT:**
- Job Title: {job_title}
- Job Description: {job_description}
- Company Mission: {company_context.get('mission', {}).get('text', 'Not provided')}
- Company Values: {company_context.get('values', {}).get('text', 'Not provided')}
- Company Goals: {company_context.get('goals', {}).get('text', 'Not provided')}
- Candidate's Positioning: {narrative.get('positioning_statement', 'Not provided')}
- Candidate's Signature Capability: {narrative.get('signature_capability', 'Not provided')}
- Resume Summary: {resume_summary}

**INSTRUCTIONS:**

Write a compelling message that:
1. Opens with why you're drawn to the company (reference mission/values)
2. Connects your core strength to the job's core need
3. Closes with confidence and a forward-looking statement

Return ONLY the message text, no JSON, no extra formatting.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            message = response.text.strip()
            logger.info("Successfully generated application message")
            return message

        except Exception as e:
            logger.error(f"Failed to generate application message: {e}")
            raise

    async def generate_application_answers(
        self,
        questions: List[str],
        job_title: str,
        job_description: str,
        company_context: Dict[str, Any],
        resume_summary: str,
        user_thoughts: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Generate answers to application questions.

        Args:
            questions: List of application questions
            job_title: Target job title
            job_description: Full job description
            company_context: Company mission, values, etc.
            resume_summary: Resume summary text
            user_thoughts: Optional user's initial thoughts for each question

        Returns:
            List of dicts with 'question' and 'answer' keys
        """

        if not questions:
            return []

        user_thoughts = user_thoughts or ["" for _ in questions]

        prompt = f"""
You are a career strategist helping a candidate answer supplemental application questions. Your tone should be professional, confident, and authentic.

**CONTEXT:**
- Job Title: {job_title}
- Job Description Summary: {job_description[:500]}...
- Company Mission: {company_context.get('mission', {}).get('text', 'Not provided')}
- Company Values: {company_context.get('values', {}).get('text', 'Not provided')}
- Company Goals: {company_context.get('goals', {}).get('text', 'Not provided')}
- Candidate's Resume Highlights: {resume_summary}
- Questions to Answer: {json.dumps(questions)}
- User's Initial Thoughts: {json.dumps(user_thoughts)}

**INSTRUCTIONS:**

1. For each question, draft a compelling, concise answer.
2. Incorporate the user's initial thoughts if provided.
3. Weave in details from the company context and the candidate's resume.
4. Return a single, valid JSON object with one key: "answers". The value should be an array of objects with "question" and "answer" keys.

**OUTPUT FORMAT:**

Return ONLY a valid JSON object. No markdown, no extra text.

{{
  "answers": [
    {{
      "question": "Why are you interested in this role?",
      "answer": "I've been following the company's progress..."
    }}
  ]
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            result_text = response.text.strip()

            # Clean response
            if result_text.startswith('```json'):
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif result_text.startswith('```'):
                result_text = result_text.split('```')[1].split('```')[0].strip()

            result = json.loads(result_text)
            logger.info(f"Successfully generated {len(result['answers'])} application answers")
            return result['answers']

        except Exception as e:
            logger.error(f"Failed to generate application answers: {e}")
            raise

    def _get_default_questions(self) -> List[str]:
        """Get default application questions if none are provided."""
        return [
            "Why are you interested in this role at our company?",
            "What makes you a strong fit for this position?",
            "What are your salary expectations?",
            "When are you available to start?"
        ]


def get_application_generator() -> ApplicationGeneratorService:
    """Get application generator service instance."""
    return ApplicationGeneratorService()
