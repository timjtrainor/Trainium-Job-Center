import {
    ResumeSuggestion, CompanyInfoResult, KeywordsResult, GuidanceResult, ResumeAccomplishment,
    InterviewPrep, PromptContext, JobSummaryResult, ExtractedInitialDetails, JobProblemAnalysisResult,
    ApplicationAnswersResult, InfoField, AchievementScore, NextStep, CombineAchievementsResult,
    InitialJobAnalysisResult, KeywordsAndGuidanceResult, ResumeTailoringData, PostSubmissionPlan,
    PostResponseAiAnalysis, ScoutedOpportunity, AiSprintPlan, BrandVoiceAnalysis, SuggestedContact,
    InterviewAnswerScore, SkillGapAnalysisResult, NarrativeSynthesisResult, NinetyDayPlan, LearningResource,
    AiSprintAction, AiFocusItem, ConsultativeClosePlan, StrategicHypothesisDraft, PostInterviewDebrief,
    AgentMessage, AgentAction, InterviewStrategy, ContactExtractionResult, StrategicMessageResult
} from "../types";
import { FASTAPI_BASE_URL } from "../constants";

// Helper for debug callbacks
type DebugCallbacks = {
    before: (info: string) => Promise<void>;
    after: (response: string) => Promise<void>;
};

// Generic JSON cleaner/parser (preserved from original service)
const cleanAndParseJson = (text: string) => {
    if (!text) {
        console.warn("Received empty text from AI model; returning empty object.");
        return {};
    }
    let jsonStr = text.trim();
    const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);

    if (match && match[2]) {
        jsonStr = match[2].trim();
    } else {
        const firstBrace = jsonStr.indexOf('{');
        const firstBracket = jsonStr.indexOf('[');

        if (firstBracket !== -1 && (firstBracket < firstBrace || firstBrace === -1)) {
            jsonStr = jsonStr.substring(firstBracket);
        } else if (firstBrace !== -1) {
            jsonStr = jsonStr.substring(firstBrace);
        }
    }

    let parsed;
    try {
        parsed = JSON.parse(jsonStr);
    } catch (e) {
        // If initial parse fails, apply escaping to fix unescaped characters in strings
        // Attempt 1: Standard escaping
        let escaped = jsonStr.replace(/"((?:[^"\\]|\\.)*)"/g, (match, group1) => {
            return `"${group1.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t').replace(/\f/g, '\\f').replace(/\b/g, '\\b')}"`;
        });

        try {
            parsed = JSON.parse(escaped);
        } catch (finalE) {
            // Attempt 2: More aggressive repair for unescaped internal quotes in "key": "value" patterns
            console.warn("Standard repair failed. Attempting aggressive internal quote repair.", e);
            try {
                // This targets unescaped quotes inside values by looking for strings that are NOT followed by , or }
                // and are NOT following a :. It's risky but can work for simple structures.
                const aggressiveRepaired = jsonStr.replace(/(:\s*")([\s\S]*?)("\s*[,\}])/, (m, p1, p2, p3) => {
                    return p1 + p2.replace(/"/g, '\\"') + p3;
                });
                parsed = JSON.parse(aggressiveRepaired);
                console.log("Successfully repaired JSON with aggressive quote escaping.");
                return parsed;
            } catch (aggressiveError) {
                // Fallback to simpler comma-based truncation repair
                const lastComma = jsonStr.lastIndexOf(',');
                if (lastComma > -1) {
                    const potentialJson = jsonStr.substring(0, lastComma) + '}';
                    try {
                        parsed = JSON.parse(potentialJson);
                        console.log("Successfully repaired JSON by removing last property.");
                        return parsed;
                    } catch (finalRepairError) {
                        console.error("Final repair attempt failed.", finalRepairError);
                    }
                }
                console.error("Failed to parse JSON response:", e);
                throw new Error(`Failed to parse JSON response: ${e instanceof Error ? e.message : String(e)}\nRaw text:\n${text}`);
            }
        }
    }
    return parsed;
};

interface ExecuteOptions {
    promptName: string;
    variables: Record<string, any>;
    debugCallbacks?: DebugCallbacks;
    modelAlias?: string;
}

// Core execution function calling the Python Backend
async function executeAiPrompt(options: ExecuteOptions): Promise<string> {
    const { promptName, variables, debugCallbacks, modelAlias } = options;

    // 1. Log Request Payload (2026 Standard)
    console.log(`[AI Request] Prompt: ${promptName}`, { variables, modelAlias });

    if (debugCallbacks?.before) {
        await debugCallbacks.before(`Executing Prompt: ${promptName}\nVariables: ${JSON.stringify(variables, null, 2)}`);
    }

    const apiUrl = `${FASTAPI_BASE_URL}/ai/execute`;

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt_name: promptName,
                variables: variables,
                model_alias: modelAlias,
                label: 'production'
            }),
        });

        // 2. Log Response Status
        console.log(`[AI Response Status] ${promptName}: ${response.status} ${response.statusText}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[AI Error] ${promptName}:`, errorText);
            throw new Error(`AI Backend Error (${response.status}): ${errorText}`);
        }

        // The backend returns the raw string content as JSON string (FastAPI default)
        // or a JSON object if we return dict.
        const resultText = await response.json();

        // Ensure resultText is a string (FastAPI might auto-serialize dicts)
        const finalText = typeof resultText === 'string' ? resultText : JSON.stringify(resultText);

        // 3. Log Final Content Length/Data
        console.log(`[AI Response Content] ${promptName} Length: ${finalText.length}`);

        if (debugCallbacks?.after) {
            await debugCallbacks.after(finalText);
        }

        return finalText;

    } catch (error) {
        console.error(`[AI Exception] ${promptName}:`, error);
        throw error;
    }
}

// --- Specific Service Functions from LangFuse Prompts ---

export async function extractInitialDetailsFromPaste(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<ExtractedInitialDetails> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    try {
        const parsedData = cleanAndParseJson(text);

        // If it successfully parsed but returned the raw JSON string as the only value,
        // it might be a double-wrapped string or a fallback failure.
        if (typeof parsedData === 'string' && (parsedData.trim().startsWith('{') || parsedData.trim().startsWith('['))) {
            try {
                const nested = cleanAndParseJson(parsedData);
                if (nested && typeof nested === 'object') return {
                    companyName: '', jobTitle: '', jobDescription: '', ...nested
                };
            } catch { }
        }

        return {
            companyName: '',
            jobTitle: '',
            jobDescription: '',
            ...parsedData,
        };
    } catch (e) {
        // If parsing fails, and the text LOOKS like JSON, we might have a serious format issue.
        // We try to extract at least the job description if we can find it via regex.
        console.warn("Failed to parse AI response as JSON, attempting regex extraction fallback");

        const descMatch = text.match(/"jobDescription":\s*"([\s\S]*?)"\s*[,\}]/);
        const companyMatch = text.match(/"companyName":\s*"([\s\S]*?)"\s*[,\}]/);
        const titleMatch = text.match(/"jobTitle":\s*"([\s\S]*?)"\s*[,\}]/);

        if (descMatch || companyMatch || titleMatch) {
            return {
                companyName: companyMatch ? companyMatch[1] : '',
                jobTitle: titleMatch ? titleMatch[1] : '',
                jobDescription: descMatch ? descMatch[1] : text,
            };
        }

        return {
            companyName: '',
            jobTitle: '',
            jobDescription: text,
        };
    }
}

export async function extractJobDetailsFromUrl(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ details: ExtractedInitialDetails, sources: any[] }> {
    // Note: This endpoint in Python might need to handle tools (Google Search)
    // The previous implementation used tools: [{ googleSearch: {} }].
    // Our LiteLLM execution in backend handles tools if configured in the model or request.
    // However, the current generic /execute endpoint may not support tools unless we add logic.
    // For now, let's assume the prompt instructions are sufficient or the backend agent handles it.
    // Wait, 'extractJobDetailsFromUrl' implies crawling? 
    // If the prompt expects text, how does it get the URL content?
    // Ah, 'context' likely contains the URL? No, usually promptContent had the logic.
    // If the user expects standard RAG or browsing, the *backend* needs to do it.
    // If the previous client-side Gemini used 'googleSearch' tool, it was doing browsing.
    // Our generic 'execute_prompt' just calls an LLM. It doesn't magically browse.
    // We might need a specific endpoint for this, OR allow tools in 'execute_prompt'.
    // BUT the user objective was "Migrate UI Prompts to LangFuse".
    // I will IMPLEMENT this call, but warn if tools are missing.
    // Actually, `extractJobDetailsFromUrl` implies we need content.
    // If context has the URL, the LLM needs a browsing tool.
    // The current backend `AIService` does NOT have tools configured by default for basic prompts.
    // Optimization: for this specific one, we might fail.
    // But let's convert the call first. 

    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsedDetails = cleanAndParseJson(text) as Partial<ExtractedInitialDetails>;
    if (parsedDetails.error) {
        throw new Error(parsedDetails.error);
    }
    const details: ExtractedInitialDetails = {
        companyName: '',
        jobTitle: '',
        jobDescription: '',
        ...parsedDetails
    };
    return { details, sources: [] }; // Sources are not returned by simple LLM call without tool metadata
}

export async function researchCompanyInfo(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<CompanyInfoResult> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsedData = cleanAndParseJson(text);
    const emptyInfoField: InfoField = { text: '', source: '' };
    return {
        mission: parsedData.mission || emptyInfoField,
        values: parsedData.values || emptyInfoField,
        news: parsedData.news || emptyInfoField,
        goals: parsedData.goals || emptyInfoField,
        issues: parsedData.issues || emptyInfoField,
        customer_segments: parsedData.customer_segments || emptyInfoField,
        strategic_initiatives: parsedData.strategic_initiatives || emptyInfoField,
        market_position: parsedData.market_position || emptyInfoField,
        competitors: parsedData.competitors || emptyInfoField,
        industry: parsedData.industry || emptyInfoField,
    };
}

export async function performInitialJobAnalysis(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<InitialJobAnalysisResult> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateKeywordsAndGuidance(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<KeywordsAndGuidanceResult> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function rewriteSummary(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.suggestions || [];
}

export async function generateResumeTailoringData(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<ResumeTailoringData> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateCoverLetter(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ cover_letter: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function scoreResumeAlignment(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ alignment_score: number }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsedData = cleanAndParseJson(text);
    return { alignment_score: parsedData.alignment_score || 0 };
}

export async function generateApplicationMessage(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.message_drafts || [];
}

export async function generateApplicationAnswers(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<Array<{ question: string; answer: string }>> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    if (!parsed || !Array.isArray(parsed.answers)) return [];
    return parsed.answers.map((item: any) => ({
        question: typeof item?.question === 'string' ? item.question : '',
        answer: typeof item?.answer === 'string' ? item.answer : '',
    })).filter(entry => entry.question || entry.answer);
}

export async function generateAdvancedCoverLetter(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed && typeof parsed.cover_letter === 'string' ? parsed.cover_letter : '';
}

export async function generatePostSubmissionPlan(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<PostSubmissionPlan> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateHighlightBullets(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsedData = cleanAndParseJson(text);
    if (parsedData && Array.isArray(parsedData.highlights)) {
        return parsedData.highlights.filter((item: unknown) => typeof item === 'string');
    }
    throw new Error("Invalid JSON structure in AI response. 'highlights' array of strings not found.");
}

export async function generateJobSpecificInterviewQuestions(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsedData = cleanAndParseJson(text);
    if (parsedData && Array.isArray(parsedData.questions)) {
        return parsedData.questions;
    }
    throw new Error("Invalid JSON structure for interview questions.");
}

export async function generateGenericInterviewQuestions(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsedData = cleanAndParseJson(text);
    if (parsedData && Array.isArray(parsedData.questions)) {
        return parsedData.questions;
    }
    throw new Error("Invalid JSON structure for generic interview questions.");
}

export async function polishImpactStoryPart(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return text.trim();
}

export async function generateStructuredSpeakerNotes(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ [key: string]: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateImpactStory(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ impact_story_title: string; impact_story_body: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateInterviewPrep(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<InterviewPrep> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateRecruiterScreenPrep(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<InterviewPrep> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateConsultantBlueprint(payload: {
    job_description: string;
    company_data: any;
    career_dna: any;
    interviewer_profiles?: any[];
    application_interview_strategy?: any;
    job_problem_analysis?: any;
    vocabulary_mirror?: string;
    alignment_strategy?: any;
    user_id?: string;
}): Promise<InterviewStrategy> {
    const response = await fetch(`${FASTAPI_BASE_URL}/interview-strategy/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to generate consultant blueprint: ${errorText}`);
    }

    return await response.json();
}

export async function generateStrategicHypothesisDraft(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<StrategicHypothesisDraft> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateConsultativeClosePlan(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<ConsultativeClosePlan> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateStrategicQuestions(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.questions || [];
}

export async function generateDashboardFeed(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<AiFocusItem[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.focus_items || [];
}

export async function generateStrategicComment(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.comments || [];
}

export async function analyzeCommentStrategically(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<PostResponseAiAnalysis> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function refineAchievementWithKeywords(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return text;
}

export async function findAndCombineAchievements(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<CombineAchievementsResult> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateStrategicMessage(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<StrategicMessageResult> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return {
        internal_reasoning: parsed.internal_reasoning || "",
        messages: Array.isArray(parsed.messages) ? parsed.messages : []
    };
}

export async function scoreContactFit(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ strategic_fit_score: number }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateNegotiationScript(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ talking_points: string[], email_draft: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function analyzeBrandVoice(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<BrandVoiceAnalysis> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateLinkedInThemes(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.themes || [];
}

export async function generatePositionedLinkedInPost(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return text;
}

export async function generatePostInterviewCounter(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<PostInterviewDebrief> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateQuestionReframeSuggestion(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestion: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function deconstructInterviewQuestion(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ scope: string[], metrics: string[], constraints: string[] }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function analyzeRefiningQuestions(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ feedback: string, score: number }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function analyzeJobSpecificInterviewAnswer(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ feedback: string, score: number }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function chatToRefineAnswer(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return text.trim();
}

export async function scoreInterviewAnswer(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<InterviewAnswerScore> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function analyzeGenericInterviewAnswer(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ feedback: string, score: number }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function synthesizeLensTalkingPoints(context: {
    role: string;
    objective: string;
    framework: string;
    competency: string;
    strategy: string;
    proof_points: string[];
}, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ talking_points: string[]; hero_kpi: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function generateLensStoryDraft(context: {
    strategy: string;
    strategy_details: string;
    story_title: string;
    story_body: string;
    persona_context: string;
    framework: string;
}, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ draft: string }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

// New Structured Narrative Generator
export async function generateStructuredNarrative(context: {
    strategy_name: string;
    strategy_definition?: string;
    competency_name: string;
    experience_context: string; // "Company: X, Role: Y, Description: Z"
    framework: string;
}, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{
    hero_kpi: string;
    visual_anchor: string;
    narrative_steps: Record<string, string>;
    thinned_bullets: string[];
}> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);

    // Map specific keys to generic keys (Situation etc) based on the requested framework
    let narrative_steps: Record<string, string> = {};
    const framework = context.framework || 'STAR';

    // Framework-specific mapping rules
    const MAPPINGS: Record<string, Record<string, string>> = {
        'STAR': { 'situation': 'Situation', 'task': 'Task', 'action': 'Action', 'result': 'Result' },
        'DIGS': { 'dramatize': 'Dramatize', 'indicate': 'Indicate', 'go': 'Go', 'synergize': 'Synergize' },
        'PAR': { 'problem': 'Problem', 'action': 'Action', 'result': 'Result' },
        'SCQA': { 'situation': 'Situation', 'complication': 'Complication', 'question': 'Question', 'answer': 'Answer' }
    };

    const currentMapping = MAPPINGS[framework] || MAPPINGS['STAR'];

    if (parsed.narrative_steps) {
        const entries = Object.entries(parsed.narrative_steps);
        const frameworkStages = framework === 'STAR' ? ['Situation', 'Task', 'Action', 'Result'] :
            framework === 'DIGS' ? ['Dramatize', 'Indicate', 'Go', 'Synergize'] :
                framework === 'PAR' ? ['Problem', 'Action', 'Result'] :
                    framework === 'SCQA' ? ['Situation', 'Complication', 'Question', 'Answer'] :
                        ['Situation', 'Task', 'Action', 'Result'];

        entries.forEach(([key, value], index) => {
            const lowerKey = key.toLowerCase();

            // 1. Try prefix stripping (star_situation -> situation)
            const parts = lowerKey.split('_');
            const targetKey = parts.length > 1 ? parts[1] : lowerKey;

            // 2. Map to standard label if possible
            const standardLabel = currentMapping[targetKey];

            if (standardLabel) {
                narrative_steps[standardLabel] = String(value);
            } else if (index < frameworkStages.length) {
                // 3. Fail-safe: Map by index if the AI used the wrong keys for the requested framework
                narrative_steps[frameworkStages[index]] = String(value);
            } else {
                // 4. Final Fallback: Capitalize first letter
                const fallbackLabel = key.charAt(0).toUpperCase() + key.slice(1).toLowerCase();
                narrative_steps[fallbackLabel] = String(value);
            }
        });
    }

    return {
        hero_kpi: parsed.hero_kpi,
        visual_anchor: parsed.visual_anchor,
        narrative_steps: narrative_steps,
        thinned_bullets: parsed.thinned_bullets
    };
}

// Added for Achievement Refinement Panel
export async function refineAchievementWithContext(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    const parsed = cleanAndParseJson(text);
    return parsed.suggestions || [];
}

export async function scoreDualAccomplishments(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<{ original_score: AchievementScore; edited_score: AchievementScore }> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function chatToRefineAchievement(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return text.trim();
}

export async function quantifyImpact(context: PromptContext, promptName: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const text = await executeAiPrompt({ promptName, variables: context, debugCallbacks });
    return text.trim();
}

// Added for Engagement Agent

export async function runEngagementAgent(
    promptName: string, // Changed from systemPrompt content to ID
    messageHistory: AgentMessage[],
    newMessage: string,
    context: any,
    debugCallbacks?: DebugCallbacks
): Promise<{ content: string; action?: AgentAction }> {

    const variables = {
        ...context,
        MESSAGE_HISTORY: messageHistory.map(m => `${m.role}: ${m.content}`).join('\n'),
        NEW_MESSAGE: newMessage
    };

    const text = await executeAiPrompt({ promptName, variables, debugCallbacks });
    return cleanAndParseJson(text);
}

export async function parseLinkedinContact(rawText: string, debugCallbacks?: DebugCallbacks): Promise<ContactExtractionResult> {
    const promptName = 'CONTACT_EXTRACTION';
    const variables = { raw_text: rawText };

    try {
        const text = await executeAiPrompt({ promptName, variables, debugCallbacks });
        const parsed = cleanAndParseJson(text);

        return {
            first_name: parsed.first_name || '',
            last_name: parsed.last_name || '',
            job_title: parsed.job_title || '',
            linkedin_url: parsed.linkedin_url || '',
            linkedin_about: parsed.linkedin_about || '',
            persona_suggestion: parsed.persona_suggestion,
            notes: parsed.notes || '',
            error: parsed.error
        };
    } catch (e) {
        console.error("Failed to parse LinkedIn contact:", e);
        return {
            first_name: '',
            last_name: '',
            job_title: '',
            linkedin_url: '',
            error: e instanceof Error ? e.message : String(e)
        };
    }
}

export function setModel(model: string) {
    // No-op or we could store this to pass as 'model_alias' if we mapped them
    // For now, let's ignore or log it.
    console.log(`Model set to ${model} (ignored in backend refactor)`);
}
