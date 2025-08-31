import { GoogleGenAI, GenerateContentResponse, Type } from "@google/genai";
import { ResumeSuggestion, CompanyInfoResult, KeywordsResult, GuidanceResult, ResumeAccomplishment, InterviewPrep, PromptContext, JobSummaryResult, ExtractedInitialDetails, JobProblemAnalysisResult, ApplicationAnswersResult, InfoField, AchievementScore, NextStep, CombineAchievementsResult, InitialJobAnalysisResult, KeywordsAndGuidanceResult, ResumeTailoringData, PostSubmissionPlan, PostResponseAiAnalysis, ScoutedOpportunity, AiSprintPlan, BrandVoiceAnalysis, SuggestedContact, InterviewAnswerScore, SkillGapAnalysisResult, NarrativeSynthesisResult, NinetyDayPlan, LearningResource, AiSprintAction, AiFocusItem, ConsultativeClosePlan, StrategicHypothesisDraft, PostInterviewDebrief } from "../types";

let ai: GoogleGenAI | null = null;
let currentModel = 'gemini-2.5-flash';

export function setModel(model: string) {
    currentModel = model;
}


function getAiClient(): GoogleGenAI {
    if (ai) {
        return ai;
    }

    if (typeof process !== 'undefined' && process.env?.API_KEY) {
        ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
        return ai;
    }
    
    throw new Error("AI Service not initialized. API_KEY is missing in the environment.");
}

type DebugCallbacks = {
    before: (prompt: string) => Promise<void>;
    after: (response: string) => Promise<void>;
};

const replacePlaceholders = (content: string, context: PromptContext): string => {
    let newContent = content;
    for (const key of Object.keys(context)) {
        const placeholder = `{{${key}}}`;
        const value = (context as any)[key];
        
        // This is a safer way to handle various types, including false and 0, preventing them from becoming empty strings.
        const replacement = (value === null || value === undefined) ? '' : String(value);

        const regex = new RegExp(placeholder.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'g');
        newContent = newContent.replace(regex, () => replacement);
    }
    return newContent;
};


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
    
    // Attempt to fix unescaped newlines in string values
    jsonStr = jsonStr.replace(/:\s*"(.*?)"/g, (match, group1) => {
        return `: "${group1.replace(/\n/g, '\\n')}"`;
    });


    try {
        return JSON.parse(jsonStr);
    } catch (e) {
        console.warn("Initial JSON parsing failed. Attempting to repair truncated JSON.", e);
        console.warn("Original raw text:", text);

        let repairedJsonStr = jsonStr;
        // Iteratively try to fix the JSON by finding the last valid closing brace and bracket
        for (let i = repairedJsonStr.length - 1; i >= 0; i--) {
            if (repairedJsonStr[i] === '}' || repairedJsonStr[i] === ']') {
                let tempStr = repairedJsonStr.substring(0, i + 1);
                // Attempt to close open structures
                let openBraces = (tempStr.match(/{/g) || []).length;
                let closeBraces = (tempStr.match(/}/g) || []).length;
                let openBrackets = (tempStr.match(/\[/g) || []).length;
                let closeBrackets = (tempStr.match(/]/g) || []).length;

                while(closeBraces < openBraces) {
                    tempStr += '}';
                    closeBraces++;
                }
                 while(closeBrackets < openBrackets) {
                    tempStr += ']';
                    closeBrackets++;
                }

                try {
                    const parsed = JSON.parse(tempStr);
                    console.log("Successfully repaired truncated JSON by closing structures.");
                    return parsed;
                } catch (repairError) {
                    // continue loop
                }
            }
        }
        
        // Fallback to simpler comma-based truncation repair if the above fails
        const lastComma = jsonStr.lastIndexOf(',');
        if (lastComma > -1) {
             const potentialJson = jsonStr.substring(0, lastComma) + '}';
             try {
                const parsed = JSON.parse(potentialJson);
                console.log("Successfully repaired JSON by removing last property.");
                return parsed;
             } catch (finalRepairError) {
                console.error("Final repair attempt failed.", finalRepairError);
             }
        }
        
        console.error("Failed to parse even the repaired JSON response:", e);
        throw new Error(`Failed to parse JSON response: ${e.message}\nRaw text:\n${text}`);
    }
};

export async function extractInitialDetailsFromPaste(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<ExtractedInitialDetails> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an expert data extraction bot. Your task is to analyze raw text and extract structured information as a JSON object.";
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.1,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);

    const parsedData = cleanAndParseJson(response.text);
    return {
        companyName: '',
        jobTitle: '',
        jobDescription: '',
        ...parsedData,
    };
}

export async function extractJobDetailsFromUrl(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ details: ExtractedInitialDetails, sources: any[] }> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
          tools: [{googleSearch: {}}],
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);

    const sources = response.candidates?.[0]?.groundingMetadata?.groundingChunks || [];
    const parsedDetails = cleanAndParseJson(response.text) as Partial<ExtractedInitialDetails>;
    if (parsedDetails.error) {
        throw new Error(parsedDetails.error);
    }
    
    const details: ExtractedInitialDetails = {
        companyName: '',
        jobTitle: '',
        jobDescription: '',
        ...parsedDetails
    };

    return { details, sources };
}

export async function researchCompanyInfo(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<CompanyInfoResult> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
          tools: [{googleSearch: {}}],
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);

    const parsedData = cleanAndParseJson(response.text);

    const emptyInfoField: InfoField = { text: '', source: '' };
    
    // Ensure all fields exist, even if AI omits them
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

export async function performInitialJobAnalysis(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<InitialJobAnalysisResult> {
    const aiClient = getAiClient();
    const systemInstruction = "You are a strategic career analyst. Your task is to perform a multi-faceted analysis of a job opportunity for a senior professional and return a single, structured JSON object.";
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.3,
        },
    });

    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateKeywordsAndGuidance(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<KeywordsAndGuidanceResult> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an expert career coach providing resume tailoring advice.";
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.2,
        },
    });
    
    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}


export async function generateResumeTailoringData(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<ResumeTailoringData> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an expert resume optimization engine.";
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.4,
        },
    });
    
    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function scoreResumeAlignment(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ alignment_score: number }> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an expert resume analyzer providing a quantitative score.";
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.1,
        },
    });

    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    
    const parsedData = cleanAndParseJson(response.text);
    return {
        alignment_score: parsedData.alignment_score || 0,
    };
}

export async function generateApplicationMessage(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const systemInstruction = "You are a career strategist helping a candidate write a compelling, concise message to a hiring team for a job application where a custom resume is not allowed.";
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.7,
        },
    });

    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return parsed.message_drafts || [];
}

export async function generatePostSubmissionPlan(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<PostSubmissionPlan> {
    const aiClient = getAiClient();
    const systemInstruction = "You are a career strategist creating an immediate action plan for a candidate who just submitted an application.";
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.6,
        },
    });

    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateHighlightBullets(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an executive career coach working with high-performing product leaders. Your task is to select and rewrite resume achievements for maximum impact as summary highlights.";
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json"
        }
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    
    const parsedData = cleanAndParseJson(response.text);
    if (parsedData && Array.isArray(parsedData.highlights)) {
        return parsedData.highlights.filter((item: unknown) => typeof item === 'string');
    }
    throw new Error("Invalid JSON structure in AI response. 'highlights' array of strings not found.");
}

export async function generateJobSpecificInterviewQuestions(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an expert hiring manager and interview coach for senior product roles.";
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.7,
        }
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    
    const parsedData = cleanAndParseJson(response.text);
    if (parsedData && Array.isArray(parsedData.questions)) {
        return parsedData.questions;
    }
    throw new Error("Invalid JSON structure for interview questions.");
}

export async function generateGenericInterviewQuestions(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an expert career and interview coach.";
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.7,
        }
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    
    const parsedData = cleanAndParseJson(response.text);
    if (parsedData && Array.isArray(parsedData.questions)) {
        return parsedData.questions;
    }
    throw new Error("Invalid JSON structure for generic interview questions.");
}

// --- NEWLY IMPLEMENTED FUNCTIONS ---

export async function polishImpactStoryPart(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            temperature: 0.6,
        },
    });

    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    // This prompt returns a single string, so no JSON parsing needed.
    return response.text.trim();
}

export async function generateStructuredSpeakerNotes(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ [key: string]: string }> {
    const aiClient = getAiClient();
    const systemInstruction = "You are an executive interview coach creating concise speaker notes.";
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction,
            responseMimeType: "application/json",
            temperature: 0.3,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);

    return cleanAndParseJson(response.text);
}


export async function generateInterviewPrep(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<InterviewPrep> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a world-class interview coach for senior product leaders.",
            responseMimeType: "application/json",
            temperature: 0.5,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateRecruiterScreenPrep(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<InterviewPrep> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response: GenerateContentResponse = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert career coach creating a quick prep sheet for a recruiter screen.",
            responseMimeType: "application/json",
            temperature: 0.4,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateStrategicHypothesisDraft(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<StrategicHypothesisDraft> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert career strategist acting as a co-pilot for a senior executive.",
            responseMimeType: "application/json",
            temperature: 0.5,
        },
    });

    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateConsultativeClosePlan(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<ConsultativeClosePlan> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a world-class interview strategist for a senior executive.",
            responseMimeType: "application/json",
            temperature: 0.6,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateStrategicQuestions(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert interview coach for a senior executive.",
            responseMimeType: "application/json",
            temperature: 0.7,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return parsed.questions || [];
}

export async function generateDashboardFeed(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<AiFocusItem[]> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a career coach creating a personalized, actionable to-do list.",
            responseMimeType: "application/json",
            temperature: 0.7,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return parsed.focus_items || [];
}

export async function generateStrategicComment(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a strategic communications assistant.",
            responseMimeType: "application/json",
            temperature: 0.8,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return parsed.comments || [];
}

export async function refineAchievementWithKeywords(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a resume co-author.",
            temperature: 0.5,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return response.text;
}

export async function findAndCombineAchievements(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<CombineAchievementsResult> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert resume editor.",
            responseMimeType: "application/json",
            temperature: 0.3,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateStrategicMessage(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert career strategist specializing in high-impact, ultra-concise networking messages.",
            responseMimeType: "application/json",
            temperature: 0.8,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return parsed.messages || [];
}

export async function scoreContactFit(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ strategic_fit_score: number }> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a strategic networking analyst.",
            responseMimeType: "application/json",
            temperature: 0.1,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function analyzeBrandVoice(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<BrandVoiceAnalysis> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a brand voice analyst providing feedback on professional messaging.",
            responseMimeType: "application/json",
            temperature: 0.4,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateLinkedInThemes(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a career strategist and content expert for senior leaders.",
            responseMimeType: "application/json",
            temperature: 0.7,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return parsed.themes || [];
}

export async function generatePositionedLinkedInPost(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if(debugCallbacks?.before) await debugCallbacks.before(prompt);
    
    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert LinkedIn ghostwriter and career storyteller for senior executives.",
            temperature: 0.8,
        },
    });
    
    if(debugCallbacks?.after) await debugCallbacks.after(response.text);
    return response.text;
}

export async function generatePostInterviewCounter(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<PostInterviewDebrief> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a world-class executive career coach.",
            responseMimeType: "application/json",
            temperature: 0.5,
        },
    });

    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    return cleanAndParseJson(response.text);
}

export async function generateQuestionReframeSuggestion(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestion: string }> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are an expert interview coach providing a 'coach in the ear' suggestion.",
            responseMimeType: "application/json",
            temperature: 0.6,
        },
    });
    
    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return { suggestion: parsed.suggestion || '' };
}

export async function deconstructInterviewQuestion(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ scope: string[]; metrics: string[]; constraints: string[] }> {
    const aiClient = getAiClient();
    const prompt = replacePlaceholders(promptContent, context);
    if (debugCallbacks?.before) await debugCallbacks.before(prompt);

    const response = await aiClient.models.generateContent({
        model: currentModel,
        contents: prompt,
        config: {
            systemInstruction: "You are a world-class interview coach.",
            responseMimeType: "application/json",
            temperature: 0.4,
        },
    });
    
    if (debugCallbacks?.after) await debugCallbacks.after(response.text);
    const parsed = cleanAndParseJson(response.text);
    return { 
        scope: parsed.scope || [],
        metrics: parsed.metrics || [],
        constraints: parsed.constraints || [],
    };
}


export async function defineMissionAlignment(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestion: string }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function defineLongTermLegacy(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestion: string }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function definePositioningStatement(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestion: string }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function suggestKeyStrengths(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestions: string[] }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function defineSignatureCapability(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ suggestion: string }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function generateImpactStory(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ impact_story_title: string; impact_story_body: string; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function refineAchievementWithContext(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> { const p = cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); return p.rewrites || []; }
export async function scoreDualAccomplishments(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ original_score: AchievementScore; edited_score: AchievementScore }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function chatToRefineAchievement(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string> { return (await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context) })).text); }
export async function rewriteSummary(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string[]> { const p = cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); return p.summaries || []; }
export async function analyzeCommentStrategically(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<PostResponseAiAnalysis> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function expandRoleDescription(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ expanded_description: string }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function analyzeRefiningQuestions(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ score: number; feedback: string; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function analyzeGenericInterviewAnswer(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ score: number; feedback: string; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function analyzeJobSpecificInterviewAnswer(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ score: number; feedback: string; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function scoreInterviewAnswer(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<InterviewAnswerScore> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function generateNegotiationScript(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ talking_points: string[]; email_draft: string; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function quantifyImpact(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string> { return (await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context) })).text); }
export async function generateSpeakerNotesFromStory(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ speaker_notes: string; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function suggestTargetQuestions(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<{ questions: string[]; }> { return cleanAndParseJson((await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context), config: { responseMimeType: "application/json" } })).text)); }
export async function chatToRefineAnswer(context: PromptContext, promptContent: string, debugCallbacks?: DebugCallbacks): Promise<string> { return (await (await getAiClient().models.generateContent({ model: currentModel, contents: replacePlaceholders(promptContent, context) })).text); }