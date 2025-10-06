import { 
    JobApplication, Company, BaseResume, Status, CompanyPayload, JobApplicationPayload, 
    BaseResumePayload, Contact, ContactPayload, Message, MessagePayload, Interview, 
    InterviewPayload, LinkedInPost, LinkedInPostPayload, UserProfile, 
    UserProfilePayload, LinkedInEngagement, PostResponse, PostResponsePayload, 
    LinkedInEngagementPayload, StandardJobRole, StandardJobRolePayload, Resume, ResumeHeader, DateInfo, Education, Certification,
    StrategicNarrative, StrategicNarrativePayload, Offer, OfferPayload,
    BragBankEntry, BragBankEntryPayload, SkillTrend, SkillTrendPayload,
    Sprint, SprintAction, CreateSprintPayload, SprintActionPayload, ApplicationQuestion,
    SiteSchedule, SiteDetails, SiteSchedulePayload,
    UploadedDocument, UploadSuccessResponse, ContentType,
    PaginatedResponse, ReviewedJob, ReviewedJobRecommendation,
    TaskEnqueueResponse, TaskRunRecord, ResumeTailoringJobPayload, CompanyResearchJobPayload
} from '../types';
import { API_BASE_URL, USER_ID, FASTAPI_BASE_URL } from '../constants';
import { v4 as uuidv4 } from 'uuid';
import { ensureUniqueAchievementIds } from '../utils/resume';

// --- API Helpers ---

const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
};

const handleResponse = async (response: Response) => {
    if (!response.ok) {
        const errorText = await response.text();
        console.error(`API Error (${response.status}): ${errorText}`);
        throw new Error(`API Error: ${errorText || response.statusText}`);
    }
    // Handle cases where the response body might be empty (e.g., 204 No Content)
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        return response.json();
    }
    return null;
};

const safeParseJson = (data: any, fieldName: string, recordId: string): any => {
    if (data === null || data === undefined || typeof data === 'object') {
        return data; // It's already an object/null, no parsing needed
    }
    if (typeof data === 'string') {
        try {
            return JSON.parse(data);
        } catch (e) {
            console.warn(`Could not parse JSON for field '${fieldName}' on record ID '${recordId}'. Returning null. Error: ${e.message}. Raw data:`, data);
            return null;
        }
    }
    return data; // Return as is if it's not a string or object
};

const FASTAPI_BASE = FASTAPI_BASE_URL.replace(/\/+$/u, '') || '/api';

const buildFastApiUrl = (path = ''): string => {
    const normalizedPath = path ? (path.startsWith('/') ? path : `/${path}`) : '';
    return `${FASTAPI_BASE}${normalizedPath}`;
};


const parseDateString = (dateString: string | null | undefined): DateInfo => {
    if (!dateString) return { year: new Date().getFullYear(), month: 1 };
    const dateParts = String(dateString).split('-');
    if (dateParts.length >= 2) {
        const year = parseInt(dateParts[0], 10);
        const month = parseInt(dateParts[1], 10);
        // Ensure year and month are valid numbers before returning
        if (!isNaN(year) && !isNaN(month)) {
            return {
                year: year,
                month: month,
                day: dateParts[2] ? parseInt(dateParts[2], 10) : undefined,
            };
        }
    }
    // Return a sensible default if parsing fails
    return { year: new Date().getFullYear(), month: 1 };
};

const formatDateInfoToString = (dateInfo: DateInfo | undefined | null): string | null => {
    if (!dateInfo || !dateInfo.year || !dateInfo.month) return null;
    const month = String(dateInfo.month).padStart(2, '0');
    const day = String(dateInfo.day || '01').padStart(2, '0');
    return `${dateInfo.year}-${month}-${day}`;
};


// Helper function to parse a raw contact object from the API into the frontend Contact type
const _parseContact = (contact: any): Contact => {
    const { company, strategic_narratives, ...rest } = contact;
    const mappedNarratives = (strategic_narratives || []).map((sn: any) => ({
        narrative_id: sn.narrative_id,
        narrative_name: sn.narrative_name
    }));
    return {
        ...rest,
        company_name: company?.company_name,
        company_url: company?.company_url,
        strategic_narratives: mappedNarratives,
    };
};

// --- Health Check ---

// Generic helper for health checks to avoid duplication
const genericHealthCheck = async (url: string): Promise<{ status: number; statusText: string; data: any; }> => {
    try {
        const response = await fetch(url);
        // Handle non-json responses gracefully
        const data = await response.json().catch(() => response.text()); 
        return {
            status: response.status,
            statusText: response.statusText,
            data: data,
        };
    } catch (error) {
        let errorMessage = 'An unknown network error occurred.';
        let statusText = 'Network Error';
        if (error instanceof TypeError) {
             errorMessage = 'Network request failed. Is the API server running and CORS configured?';
        } else if (error instanceof SyntaxError) {
             errorMessage = 'Failed to parse JSON response from server.';
             statusText = 'JSON Parse Error';
        } else if (error instanceof Error) {
            errorMessage = error.message;
        }
        return {
            status: 0,
            statusText: statusText,
            data: { error: errorMessage },
        };
    }
};

export const checkPostgrestHealth = async (): Promise<{ status: number; statusText: string; data: any; }> => {
    // PostgREST root returns a service description JSON. A 200 OK is a pass.
    return genericHealthCheck(API_BASE_URL);
};

export const checkFastApiHealth = async (): Promise<{ status: number; statusText: string; data: any; }> => {
    // Assuming the FastAPI health endpoint is at /health
    return genericHealthCheck(buildFastApiUrl('health'));
};


// --- Applications --

const _parseApplication = (app: any): JobApplication => {
    const appId = app.job_application_id;
    const parsedApp: any = {
        ...app,
        job_problem_analysis_result: safeParseJson(app.job_problem_analysis_result, 'job_problem_analysis_result', appId),
        keywords: safeParseJson(app.keywords, 'keywords', appId),
        guidance: safeParseJson(app.guidance, 'guidance', appId),
        tailored_resume_json: safeParseJson(app.tailored_resume_json, 'tailored_resume_json', appId),
        assumed_requirements: safeParseJson(app.assumed_requirements, 'assumed_requirements', appId),
        initial_interview_prep: safeParseJson(app.initial_interview_prep, 'initial_interview_prep', appId),
        next_steps_plan: safeParseJson(app.next_steps_plan, 'next_steps_plan', appId),
        first_90_day_plan: safeParseJson(app.first_90_day_plan, 'first_90_day_plan', appId),
    };

    const parsedQuestions = safeParseJson(app.application_questions, 'application_questions', appId);
    parsedApp.application_questions = Array.isArray(parsedQuestions)
        ? parsedQuestions.map((q: any): ApplicationQuestion => ({ ...q, id: q.id || uuidv4() }))
        : [];

    if (parsedApp.interviews && Array.isArray(parsedApp.interviews)) {
        const mappedInterviews = parsedApp.interviews.map((interview: any) => {
            let mappedInterviewContacts = [];
            if (interview.interview_contacts && Array.isArray(interview.interview_contacts)) {
                mappedInterviewContacts = interview.interview_contacts
                    .map((ic: any) => {
                        if (ic.contacts) {
                            return {
                                contact_id: ic.contacts.contact_id,
                                first_name: ic.contacts.first_name,
                                last_name: ic.contacts.last_name,
                            };
                        }
                        return null;
                    })
                    .filter(Boolean);
            }

            const sanitizedInterviewDate = interview.interview_date
                ? new Date(interview.interview_date).toISOString().split('T')[0]
                : undefined;

            return {
                ...interview,
                interview_date: sanitizedInterviewDate,
                interview_contacts: mappedInterviewContacts,
                ai_prep_data: safeParseJson(interview.ai_prep_data, 'ai_prep_data', interview.interview_id),
                strategic_plan: safeParseJson(interview.strategic_plan, 'strategic_plan', interview.interview_id),
                post_interview_debrief: safeParseJson(interview.post_interview_debrief, 'post_interview_debrief', interview.interview_id),
            };
        });
        return { ...parsedApp, interviews: mappedInterviews };
    }
    return parsedApp;
};

export const getApplications = async (since?: string): Promise<JobApplication[]> => {
    let url = `${API_BASE_URL}/job_applications?user_id=eq.${USER_ID}` +
        `&select=*,` +
        `status:statuses(*),` +
        `messages(*),` +
        `interviews(interview_id,job_application_id,interview_date,interview_type,notes,ai_prep_data,strategic_plan,strategic_opening,post_interview_debrief,strategic_questions_to_ask,interview_contacts(*,contacts(contact_id,first_name,last_name))),` +
        `offers(*)` +
        `&order=date_applied.desc,created_at.desc`;
    if (since) {
        url += `&date_applied=gte.${since}`;
    }
    const response = await fetch(url);
    const applications: any[] = await handleResponse(response);

    return applications.map(_parseApplication);
};

export const getSingleApplication = async (appId: string): Promise<JobApplication> => {
    let url = `${API_BASE_URL}/job_applications?job_application_id=eq.${appId}&user_id=eq.${USER_ID}` +
        `&select=*,` +
        `status:statuses(*),` +
        `messages(*),` +
        `interviews(interview_id,job_application_id,interview_date,interview_type,notes,ai_prep_data,strategic_plan,strategic_opening,post_interview_debrief,strategic_questions_to_ask,interview_contacts(*,contacts(contact_id,first_name,last_name))),` +
        `offers(*)` +
        `&limit=1`;
    const response = await fetch(url);
    const applications: any[] = await handleResponse(response);

    if (!applications || applications.length === 0) {
        throw new Error(`Application with ID ${appId} not found.`);
    }

    return _parseApplication(applications[0]);
};

// --- Robust Application Create/Update ---

// A strict whitelist of fields that exist on the 'job_applications' table.
// This prevents client-side relational objects (like 'status' or 'interviews') from
// being sent in the request body, which would cause a "malformed json" error.
const APPLICATION_TABLE_FIELDS: (keyof JobApplicationPayload)[] = [
    'narrative_id', 'company_id', 'job_title', 'job_description', 'job_link', 'salary',
    'location', 'remote_status', 'date_applied', 'status_id', 'ai_summary',
    'job_problem_analysis_result', 'keywords', 'guidance', 'resume_summary',
    'resume_summary_bullets', 'tailored_resume_json', 'application_questions',
    'application_message', 'strategic_fit_score', 'initial_interview_prep', 'why_this_job', 'next_steps_plan',
    'first_90_day_plan', 'keyword_coverage_score', 'assumed_requirements',
    'referral_target_suggestion'
];

/**
 * Creates a sanitized payload for creating or updating a JobApplication.
 * This function is critical for preventing database errors by ensuring that only
 * valid fields from the 'job_applications' table are included in the request body.
 * @param data The raw payload from the client, which might contain extra data.
 * @returns A new object containing only the whitelisted fields.
 */
const createSanitizedApplicationPayload = (data: Partial<JobApplicationPayload>): object => {
    const payload: { [key: string]: any } = {};
    for (const key of APPLICATION_TABLE_FIELDS) {
        if (data.hasOwnProperty(key)) {
            const value = data[key];
            if (value !== undefined) {
                payload[key] = value;
            }
        }
    }
    return payload;
};

export const createApplication = async (appData: JobApplicationPayload): Promise<JobApplication> => {
    const payload = {
        ...createSanitizedApplicationPayload(appData),
        user_id: USER_ID,
    };

    const response = await fetch(`${API_BASE_URL}/job_applications`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    if (!data || data.length === 0) {
        throw new Error("Failed to create application: No data returned from API.");
    }
    // Re-fetch the full object to ensure all relational data is present for UI consistency.
    return getSingleApplication(data[0].job_application_id);
};

export const updateApplication = async (appId: string, appData: JobApplicationPayload): Promise<JobApplication> => {
    const payload = createSanitizedApplicationPayload(appData);

    if (Object.keys(payload).length === 0) {
        console.warn("Update application called with an empty payload. Re-fetching current state.");
        return getSingleApplication(appId);
    }

    const response = await fetch(`${API_BASE_URL}/job_applications?job_application_id=eq.${appId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: headers,
        body: JSON.stringify(payload),
    });
    
    // Use handleResponse to check for API errors and handle empty responses (like a 204 No Content).
    await handleResponse(response);
    
    // Always re-fetch the single, fully hydrated application after an update.
    // This is crucial to prevent the UI state from becoming corrupted with partial data,
    // which can happen if an update involves removing relational data (like interviews).
    return getSingleApplication(appId);
};


export const deleteApplication = async (appId: string): Promise<void> => {
    await handleResponse(await fetch(`${API_BASE_URL}/offers?job_application_id=eq.${appId}`, { method: 'DELETE', headers }));
    await handleResponse(await fetch(`${API_BASE_URL}/interviews?job_application_id=eq.${appId}`, { method: 'DELETE', headers }));
    await handleResponse(await fetch(`${API_BASE_URL}/messages?job_application_id=eq.${appId}`, { method: 'DELETE', headers }));
    
    await handleResponse(await fetch(`${API_BASE_URL}/contacts?job_application_id=eq.${appId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ job_application_id: null }),
    }));

    const finalResponse = await fetch(`${API_BASE_URL}/job_applications?job_application_id=eq.${appId}&user_id=eq.${USER_ID}`, { method: 'DELETE', headers });
    await handleResponse(finalResponse);
};

// --- Companies ---

// A strict whitelist of fields that exist on the 'companies' table.
const COMPANY_TABLE_FIELDS: (keyof CompanyPayload)[] = [
    'company_name', 'company_url', 'mission', 'values', 'news', 'goals', 'issues',
    'customer_segments', 'strategic_initiatives', 'market_position', 'competitors',
    'industry', 'is_recruiting_firm'
];

/**
 * Creates a sanitized payload for creating or updating a Company.
 * @param data The raw payload from the client.
 * @returns A new object containing only the whitelisted fields.
 */
const createSanitizedCompanyPayload = (data: Partial<CompanyPayload | Company>): object => {
    const payload: { [key: string]: any } = {};
    for (const key of COMPANY_TABLE_FIELDS) {
        if (data.hasOwnProperty(key)) {
            const value = data[key as keyof typeof data];
            if (value !== undefined) {
                payload[key] = value;
            }
        }
    }
    return payload;
};

export const getCompanies = async (): Promise<Company[]> => {
    const response = await fetch(`${API_BASE_URL}/companies?user_id=eq.${USER_ID}&order=company_name.asc`);
    return handleResponse(response);
};

export const getCompany = async (companyId: string): Promise<Company> => {
    const response = await fetch(`${API_BASE_URL}/companies?company_id=eq.${companyId}&user_id=eq.${USER_ID}`);
    const data = await handleResponse(response);
    if (!data || data.length === 0) throw new Error(`Company with ID ${companyId} not found.`);
    return data[0];
};

export const createCompany = async (companyData: CompanyPayload): Promise<Company> => {
    const sanitizedData = createSanitizedCompanyPayload(companyData);
    const payload = { ...sanitizedData, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/companies`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updateCompany = async (companyId: string, companyData: Partial<Company>): Promise<Company> => {
    const payload = createSanitizedCompanyPayload(companyData);

    if (Object.keys(payload).length === 0) {
        console.warn("Update company called with an empty payload. Re-fetching current state.");
        return getCompany(companyId);
    }

    const response = await fetch(`${API_BASE_URL}/companies?company_id=eq.${companyId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: headers,
        body: JSON.stringify(payload),
    });
    await handleResponse(response);
    
    // Re-fetch the full object for consistency
    return getCompany(companyId);
};

// --- Resumes ---

export const getBaseResumes = async (): Promise<BaseResume[]> => {
    const response = await fetch(`${API_BASE_URL}/resumes?user_id=eq.${USER_ID}&order=resume_name.asc`);
    const resumes = await handleResponse(response);
    // Eagerly load full content for all resumes on initial load
    const contentPromises = resumes.map((resume: BaseResume) => getResumeContent(resume.resume_id));
    const allContent = await Promise.all(contentPromises);
    return resumes.map((resume: BaseResume, index: number) => ({
        ...resume,
        content: allContent[index]
    }));
};

export const createBaseResume = async (resumeData: BaseResumePayload): Promise<BaseResume> => {
    const { content, ...payload } = { ...resumeData, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/resumes`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updateBaseResume = async (resumeId: string, resumeData: Partial<BaseResumePayload>): Promise<BaseResume> => {
    const { content, ...payload } = resumeData;
    const response = await fetch(`${API_BASE_URL}/resumes?resume_id=eq.${resumeId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const deleteBaseResume = async (resumeId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/resumes?resume_id=eq.${resumeId}&user_id=eq.${USER_ID}`, { method: 'DELETE', headers });
    await handleResponse(response);
};

export const getResumeContent = async (resumeId: string): Promise<Resume> => {
    const resumeQuery = `
        resume_id,resume_name,is_locked,summary_paragraph,summary_bullets,
        resume_work_experience(
            *,
            resume_accomplishments(*)
        ),
        resume_education(*),
        resume_certifications(*),
        resume_skill_sections(
            *,
            resume_skill_items(*)
        )
    `.replace(/\s/g, '');

    const [resumeResponse, userResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/resumes?resume_id=eq.${resumeId}&user_id=eq.${USER_ID}&select=${resumeQuery}`),
        fetch(`${API_BASE_URL}/users?user_id=eq.${USER_ID}&select=first_name,last_name,email,phone_number,city,state,links`),
    ]);

    const resumeData = await handleResponse(resumeResponse);
    const userData = await handleResponse(userResponse);
    
    if (!resumeData || resumeData.length === 0) {
        throw new Error(`Resume content not found for ID: ${resumeId}.`);
    }

    const rawResume = resumeData[0];
    const userProfile = userData?.[0] || {};
    
    // Resume-specific header and summary are assumed to be on the resumes table itself for simplicity now.
    // This aligns with the user's schema feedback.
      const assembledContent: Resume = {
        header: {
            first_name: userProfile.first_name || '',
            last_name: userProfile.last_name || '',
            job_title: '', // Job title is per-application, not on the base resume.
            email: userProfile.email || '',
            phone_number: userProfile.phone_number || '',
            city: userProfile.city || '',
            state: userProfile.state || '',
            links: userProfile.links || [],
        },
        summary: {
            paragraph: rawResume.summary_paragraph || '',
            bullets: safeParseJson(rawResume.summary_bullets, 'summary_bullets', resumeId) || [],
        },
        work_experience: (rawResume.resume_work_experience || [])
            .map((exp: any) => ({
                ...exp,
                start_date: parseDateString(exp.start_date),
                end_date: parseDateString(exp.end_date),
                accomplishments: (exp.resume_accomplishments || []).sort(
                    (a: any, b: any) => a.order_index - b.order_index
                )
            }))
            .sort((a: any, b: any) =>
                new Date(b.start_date.year, b.start_date.month - 1).getTime() -
                new Date(a.start_date.year, a.start_date.month - 1).getTime()
            ),
        education: (rawResume.resume_education || []).map((edu: Education) => ({ ...edu })),
        certifications: (rawResume.resume_certifications || []).map((cert: any) => ({ ...cert })),
        skills: (rawResume.resume_skill_sections || []).map((sec: any) => ({
            heading: sec.heading,
            items: (sec.resume_skill_items || []).map((item: any) => item.item_text)
        }))
      };

      const sanitized = ensureUniqueAchievementIds(assembledContent);
      return JSON.parse(JSON.stringify(sanitized));
  };

export const saveResumeContent = async (resumeId: string, content: Resume): Promise<void> => {
    try {
        // Wrap the entire function in a try...catch to ensure any failure is reported.
        // --- 1. Update User Profile Info (if any) ---
        const userProfilePayload: UserProfilePayload = {
            first_name: content.header.first_name,
            last_name: content.header.last_name,
            email: content.header.email,
            phone_number: content.header.phone_number,
            city: content.header.city,
            state: content.header.state,
            links: content.header.links,
        };
        await handleResponse(await fetch(`${API_BASE_URL}/users?user_id=eq.${USER_ID}`, {
            method: 'PATCH', headers, body: JSON.stringify(userProfilePayload)
        }));

        // --- 2. Update the main resumes table with summary info ---
        const resumeUpdatePayload = {
            summary_paragraph: content.summary.paragraph,
            summary_bullets: content.summary.bullets
        };
        await handleResponse(await fetch(`${API_BASE_URL}/resumes?resume_id=eq.${resumeId}`, {
            method: 'PATCH', headers, body: JSON.stringify(resumeUpdatePayload)
        }));

        // --- 3. Clear out existing relational data for this resume ---
        await handleResponse(await fetch(`${API_BASE_URL}/resume_work_experience?resume_id=eq.${resumeId}`, { method: 'DELETE', headers }));
        await handleResponse(await fetch(`${API_BASE_URL}/resume_education?resume_id=eq.${resumeId}`, { method: 'DELETE', headers }));
        await handleResponse(await fetch(`${API_BASE_URL}/resume_certifications?resume_id=eq.${resumeId}`, { method: 'DELETE', headers }));
        await handleResponse(await fetch(`${API_BASE_URL}/resume_skill_sections?resume_id=eq.${resumeId}`, { method: 'DELETE', headers }));

        // --- 4. Insert new relational data ---
        if (content.work_experience && content.work_experience.length > 0) {
            for (const exp of content.work_experience) {
                const expPayload = {
                    resume_id: resumeId,
                    company_name: exp.company_name,
                    job_title: exp.job_title,
                    location: exp.location,
                    start_date: formatDateInfoToString(exp.start_date),
                    end_date: formatDateInfoToString(exp.end_date),
                    is_current: exp.is_current,
                    filter_accomplishment_count: exp.filter_accomplishment_count,
                };
                
                const expResponse = await fetch(`${API_BASE_URL}/resume_work_experience`, {
                    method: 'POST',
                    headers: { ...headers, 'Prefer': 'return=representation' },
                    body: JSON.stringify(expPayload),
                });
                const newExpArray = await handleResponse(expResponse);

                if (newExpArray && newExpArray.length > 0) {
                    const newWorkExperienceId = newExpArray[0].work_experience_id;
                    if (newWorkExperienceId && exp.accomplishments && exp.accomplishments.length > 0) {
                        const accomplishmentsPayload = exp.accomplishments.map((acc: any) => ({
                            description: acc.description,
                            original_description: acc.original_description,
                            always_include: acc.always_include,
                            themes: acc.themes || undefined,
                            score: acc.score || undefined,
                            order_index: acc.order_index,
                            work_experience_id: newWorkExperienceId,
                        }));
                        await handleResponse(await fetch(`${API_BASE_URL}/resume_accomplishments`, {
                            method: 'POST',
                            headers,
                            body: JSON.stringify(accomplishmentsPayload),
                        }));
                    }
                }
            }
        }

        if (content.education && content.education.length > 0) {
            const educationPayload = content.education.map(edu => ({ ...edu, resume_id: resumeId }));
            await handleResponse(await fetch(`${API_BASE_URL}/resume_education`, {
                method: 'POST',
                headers,
                body: JSON.stringify(educationPayload),
            }));
        }

        if (content.certifications && content.certifications.length > 0) {
            const certificationsPayload = content.certifications.map(cert => ({
                name: cert.name,
                organization: cert.organization,
                link: cert.link,
                issued_date: cert.issued_date,
                resume_id: resumeId,
            }));
            await handleResponse(await fetch(`${API_BASE_URL}/resume_certifications`, {
                method: 'POST',
                headers,
                body: JSON.stringify(certificationsPayload),
            }));
        }

        if (content.skills && content.skills.length > 0) {
            for (const skillSection of content.skills) {
                if (skillSection.items && skillSection.items.length > 0) {
                    const sectionPayload = {
                        resume_id: resumeId,
                        heading: skillSection.heading,
                    };
                    const sectionResponse = await fetch(`${API_BASE_URL}/resume_skill_sections`, {
                        method: 'POST',
                        headers: { ...headers, 'Prefer': 'return=representation' },
                        body: JSON.stringify(sectionPayload),
                    });
                    const newSectionArray = await handleResponse(sectionResponse);

                    if (newSectionArray && newSectionArray.length > 0) {
                         const newSectionId = newSectionArray[0].skill_section_id;
                        if (newSectionId) {
                            const itemsPayload = skillSection.items.map(item => ({
                                skill_section_id: newSectionId,
                                item_text: item,
                            }));
                            await handleResponse(await fetch(`${API_BASE_URL}/resume_skill_items`, {
                                method: 'POST',
                                headers,
                                body: JSON.stringify(itemsPayload),
                            }));
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error("A critical error occurred while saving the resume:", error);
        // Re-throw the error so the UI layer can catch it and display a message.
        throw error;
    }
};


// --- Other Entities ---

export const getStatuses = async (): Promise<Status[]> => {
    const response = await fetch(`${API_BASE_URL}/statuses`);
    return handleResponse(response);
};

export const getContacts = async (): Promise<Contact[]> => {
    const response = await fetch(`${API_BASE_URL}/contacts?user_id=eq.${USER_ID}&select=*,company:companies(company_id,company_name,company_url),job_application:job_applications!job_application_id(job_application_id,job_title),messages(*),strategic_narratives!contact_narratives(narrative_id,narrative_name)&order=last_name.asc`);
    const data = await handleResponse(response);
    return data.map(_parseContact);
};

export const getSingleContact = async (contactId: string): Promise<Contact> => {
    const url = `${API_BASE_URL}/contacts?contact_id=eq.${contactId}&user_id=eq.${USER_ID}&select=*,company:companies(company_id,company_name,company_url),job_application:job_applications!job_application_id(job_application_id,job_title),messages(*),strategic_narratives!contact_narratives(narrative_id,narrative_name)&limit=1`;
    const response = await fetch(url);
    const data = await handleResponse(response);
    if (!data || data.length === 0) {
        throw new Error(`Contact with ID ${contactId} not found.`);
    }
    return _parseContact(data[0]);
};


export const createContact = async (contactData: Partial<Contact>): Promise<Contact> => {
    // Strip out properties that don't exist on the 'contacts' table before sending.
    const {
        contact_id,
        company_name,
        company_url,
        job_application,
        messages,
        narrative_ids,
        strategic_narratives,
        ...rest
    } = contactData as any;

    const payload = { ...rest, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/contacts`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    if (!data || data.length === 0) {
        throw new Error("Failed to create contact: no data returned.");
    }
    return getSingleContact(data[0].contact_id);
};

export const updateContact = async (contactId: string, contactData: Partial<Contact>): Promise<Contact> => {
    // Strip out properties that don't exist on the 'contacts' table before sending.
    const {
        contact_id,
        company_name,
        company_url,
        job_application,
        messages,
        narrative_ids,
        strategic_narratives,
        ...rest
    } = contactData as any;

    const payload = { ...rest };
    const response = await fetch(`${API_BASE_URL}/contacts?contact_id=eq.${contactId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: headers,
        body: JSON.stringify(payload),
    });
    await handleResponse(response);
    return getSingleContact(contactId);
};

export const setContactNarratives = async (contactId: string, narrativeIds: string[]): Promise<void> => {
    await fetch(`${API_BASE_URL}/contact_narratives?contact_id=eq.${contactId}`, {
        method: 'DELETE',
        headers,
    });
    if (narrativeIds.length > 0) {
        const payload = narrativeIds.map(narrative_id => ({
            contact_id: contactId,
            narrative_id: narrative_id
        }));
        await fetch(`${API_BASE_URL}/contact_narratives`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
        });
    }
};


export const deleteContact = async (contactId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/contacts?contact_id=eq.${contactId}&user_id=eq.${USER_ID}`, { method: 'DELETE', headers });
    await handleResponse(response);
};

export const getAllMessages = async (): Promise<Message[]> => {
    const response = await fetch(`${API_BASE_URL}/messages?user_id=eq.${USER_ID}&select=*,contact:contacts(first_name,last_name),company:companies(company_name)&order=created_at.desc`);
    return handleResponse(response);
};

export const getMessages = async (filters: { since?: string }): Promise<Message[]> => {
    let url = `${API_BASE_URL}/messages?user_id=eq.${USER_ID}&select=*,contact:contacts(first_name,last_name),company:companies(company_name)&order=created_at.desc`;
    if (filters.since) {
        url += `&created_at=gte.${filters.since}`;
    }
    const response = await fetch(url);
    return handleResponse(response);
};

export const getPendingFollowUps = async (): Promise<Message[]> => {
    const today = new Date().toISOString().split('T')[0];
    const response = await fetch(`${API_BASE_URL}/messages?user_id=eq.${USER_ID}&follow_up_due_date=lte.${today}&select=*,contact:contacts(first_name,last_name)&order=follow_up_due_date.asc`);
    return handleResponse(response);
};

export const createMessage = async (messageData: MessagePayload): Promise<Message> => {
    const payload = { ...messageData, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/messages`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

// --- Interviews ---

export const getInterviews = async (appId: string): Promise<Interview[]> => {
    const response = await fetch(
        `${API_BASE_URL}/interviews?job_application_id=eq.${appId}` +
        `&select=*,ai_prep_data,strategic_plan,strategic_opening,strategic_questions_to_ask,post_interview_debrief,interview_contacts(*,contacts(contact_id,first_name,last_name))`
    );
    const interviews = await handleResponse(response);
    return interviews.map((interview: any) => {
        let mappedInterviewContacts = [];
        if (interview.interview_contacts && Array.isArray(interview.interview_contacts)) {
            mappedInterviewContacts = interview.interview_contacts
                .map((ic: any) => {
                    if (ic.contacts) {
                        return {
                            contact_id: ic.contacts.contact_id,
                            first_name: ic.contacts.first_name,
                            last_name: ic.contacts.last_name,
                        };
                    }
                    return null;
                })
                .filter(Boolean);
        }
        const sanitizedInterviewDate = interview.interview_date
            ? new Date(interview.interview_date).toISOString().split('T')[0]
            : undefined;
        return { ...interview, interview_date: sanitizedInterviewDate, interview_contacts: mappedInterviewContacts };
    });
};

export const saveInterview = async (interviewData: InterviewPayload, interviewId?: string): Promise<Interview> => {
    const { contact_ids, ...rest } = interviewData;

    let savedInterview: Interview;
    if (interviewId) {
        const response = await fetch(`${API_BASE_URL}/interviews?interview_id=eq.${interviewId}`, {
            method: 'PATCH',
            headers: { ...headers, 'Prefer': 'return=representation' },
            body: JSON.stringify(rest),
        });
        const data = await handleResponse(response);
        savedInterview = data[0];
    } else {
        const response = await fetch(`${API_BASE_URL}/interviews`, {
            method: 'POST',
            headers: { ...headers, 'Prefer': 'return=representation' },
            body: JSON.stringify(rest),
        });
        const data = await handleResponse(response);
        savedInterview = data[0];
    }

    if (savedInterview && contact_ids) {
        await handleResponse(await fetch(`${API_BASE_URL}/interview_contacts?interview_id=eq.${savedInterview.interview_id}`, {
            method: 'DELETE',
            headers,
        }));
        if (contact_ids.length > 0) {
            const contactLinks = contact_ids.map(contact_id => ({
                interview_id: savedInterview.interview_id,
                contact_id: contact_id,
            }));
            await handleResponse(await fetch(`${API_BASE_URL}/interview_contacts`, {
                method: 'POST',
                headers,
                body: JSON.stringify(contactLinks),
            }));
        }
    }
    return savedInterview;
};

export const deleteInterview = async (interviewId: string): Promise<void> => {
    await handleResponse(await fetch(`${API_BASE_URL}/interview_contacts?interview_id=eq.${interviewId}`, {
        method: 'DELETE',
        headers,
    }));

    const response = await fetch(`${API_BASE_URL}/interviews?interview_id=eq.${interviewId}`, {
        method: 'DELETE',
        headers,
    });
    await handleResponse(response);
};

// --- LinkedIn ---

const _parseEngagement = (engagement: any): LinkedInEngagement => {
    const { engagement_type, contact, ...rest } = engagement;
    return {
        ...rest,
        interaction_type: engagement_type,
        contact,
    };
};

const _parsePost = (post: any): LinkedInPost => {
    return {
        ...post,
        engagements: post.engagements ? post.engagements.map(_parseEngagement) : [],
    };
};

export const getLinkedInPosts = async (): Promise<LinkedInPost[]> => {
    const response = await fetch(`${API_BASE_URL}/linkedin_posts?user_id=eq.${USER_ID}&select=*,engagements:post_engagements(*,contact:contacts(contact_id,first_name,last_name,job_title))&order=created_at.desc`);
    const data = await handleResponse(response);
    return data.map(_parsePost);
};

export const createLinkedInPost = async (payload: LinkedInPostPayload): Promise<LinkedInPost> => {
    const postPayload = { ...payload, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/linkedin_posts`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(postPayload),
    });
    const data = await handleResponse(response);
    return _parsePost(data[0]);
};

export const getLinkedInEngagements = async (): Promise<LinkedInEngagement[]> => {
    const response = await fetch(`${API_BASE_URL}/post_engagements?user_id=eq.${USER_ID}&select=*,contact:contacts(contact_id,first_name,last_name,job_title)&order=created_at.desc`);
    const data = await handleResponse(response);
    return data.map(_parseEngagement);
};

export const createLinkedInEngagement = async (payload: LinkedInEngagementPayload): Promise<LinkedInEngagement> => {
    const { interaction_type, ...rest } = payload;
    const engagementPayload = { 
        ...rest,
        engagement_type: interaction_type,
        user_id: USER_ID 
    };
    const response = await fetch(`${API_BASE_URL}/post_engagements`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(engagementPayload),
    });
    const data = await handleResponse(response);

    const newEngagementId = data[0].engagement_id;
    const refetchResponse = await fetch(`${API_BASE_URL}/post_engagements?engagement_id=eq.${newEngagementId}&select=*,contact:contacts(contact_id,first_name,last_name,job_title)`);
    const refetchedData = await handleResponse(refetchResponse);

    return _parseEngagement(refetchedData[0]);
};

export const updateLinkedInEngagement = async (engagementId: string, payload: Partial<LinkedInEngagementPayload>): Promise<LinkedInEngagement> => {
    const { interaction_type, ...rest } = payload;
    const updatePayload: { [key: string]: any } = { ...rest };

    if (interaction_type) {
        updatePayload.engagement_type = interaction_type;
    }
    
    const response = await fetch(`${API_BASE_URL}/post_engagements?engagement_id=eq.${engagementId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(updatePayload),
    });
    const data = await handleResponse(response);
    return _parseEngagement(data[0]);
};

export const getPostResponses = async (): Promise<PostResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/post_responses?user_id=eq.${USER_ID}&order=created_at.desc`);
    return handleResponse(response);
};

export const createPostResponse = async (payload: PostResponsePayload): Promise<PostResponse> => {
    const responsePayload = { ...payload, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/post_responses`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(responsePayload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updatePostResponse = async (commentId: string, payload: PostResponsePayload): Promise<PostResponse> => {
    const response = await fetch(`${API_BASE_URL}/post_responses?comment_id=eq.${commentId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};


// --- User Profile & Strategy ---

export const getUserProfile = async (): Promise<UserProfile> => {
    const response = await fetch(`${API_BASE_URL}/users?user_id=eq.${USER_ID}`);
    const data = await handleResponse(response);
    return data?.[0] || { user_id: USER_ID, links: [] };
};

export const saveUserProfileData = async (payload: UserProfilePayload): Promise<UserProfile> => {
    const response = await fetch(`${API_BASE_URL}/users?user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const getStrategicNarratives = async (): Promise<StrategicNarrative[]> => {
    const response = await fetch(`${API_BASE_URL}/strategic_narratives?user_id=eq.${USER_ID}&select=*,impact_stories&order=created_at.asc`);
    const narratives = await handleResponse(response);
    // Safely parse JSONB field
    return narratives.map((narrative: any) => ({
        ...narrative,
        impact_stories: safeParseJson(narrative.impact_stories, 'impact_stories', narrative.narrative_id)
    }));
};

export const createNarrative = async (payload: StrategicNarrativePayload): Promise<StrategicNarrative> => {
    const narrativePayload = { ...payload, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/strategic_narratives`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(narrativePayload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const createSingleNarrative = async (name: string): Promise<StrategicNarrative> => {
    return createNarrative({ narrative_name: name, desired_title: 'Product Leader' });
};

export const createDefaultNarratives = async (): Promise<StrategicNarrative[]> => {
    const narrativeA = await createNarrative({ narrative_name: 'Narrative A', desired_title: 'Product Leader' });
    const narrativeB = await createNarrative({ narrative_name: 'Narrative B', desired_title: 'Product Leader' });
    return [narrativeA, narrativeB];
};


export const saveStrategicNarrative = async (payload: StrategicNarrativePayload, narrativeId: string): Promise<StrategicNarrative> => {
    const { impact_stories, ...narrativeData } = payload;

    const finalPayload: any = { ...narrativeData };

    if (impact_stories) {
        finalPayload.impact_stories = impact_stories;
    }


    const response = await fetch(`${API_BASE_URL}/strategic_narratives?narrative_id=eq.${narrativeId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(finalPayload),
    });
    await handleResponse(response);
    
    const finalResponse = await fetch(`${API_BASE_URL}/strategic_narratives?narrative_id=eq.${narrativeId}&user_id=eq.${USER_ID}&select=*,impact_stories`);
    const finalDataArray = await handleResponse(finalResponse);
    const finalData = finalDataArray[0];

    return {
        ...finalData,
        impact_stories: safeParseJson(finalData.impact_stories, 'impact_stories', finalData.narrative_id)
    };
};

export const getStandardJobRoles = async (): Promise<StandardJobRole[]> => {
    const response = await fetch(`${API_BASE_URL}/standard_job_roles?order=role_title.asc`);
    return handleResponse(response);
};

export const createStandardJobRole = async (payload: StandardJobRolePayload, narrativeId: string): Promise<StandardJobRole> => {
    const rolePayload = { ...payload, narrative_id: narrativeId };
     const response = await fetch(`${API_BASE_URL}/standard_job_roles`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(rolePayload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updateStandardJobRole = async (roleId: string, payload: StandardJobRolePayload): Promise<StandardJobRole> => {
    const response = await fetch(`${API_BASE_URL}/standard_job_roles?role_id=eq.${roleId}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const deleteStandardJobRole = async (roleId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/standard_job_roles?role_id=eq.${roleId}`, { method: 'DELETE', headers });
    await handleResponse(response);
};

// --- Offers ---

export const getOffers = async (): Promise<Offer[]> => {
    const response = await fetch(`${API_BASE_URL}/offers?user_id=eq.${USER_ID}&order=created_at.desc`);
    return handleResponse(response);
};

export const saveOffer = async (offerData: OfferPayload, offerId?: string): Promise<Offer> => {
    if (offerId) {
        const response = await fetch(`${API_BASE_URL}/offers?offer_id=eq.${offerId}&user_id=eq.${USER_ID}`, {
            method: 'PATCH',
            headers: { ...headers, 'Prefer': 'return=representation' },
            body: JSON.stringify(offerData),
        });
        const data = await handleResponse(response);
        return data[0];
    } else {
        const payload = { ...offerData, user_id: USER_ID };
        const response = await fetch(`${API_BASE_URL}/offers`, {
            method: 'POST',
            headers: { ...headers, 'Prefer': 'return=representation' },
            body: JSON.stringify(payload),
        });
        const data = await handleResponse(response);
        return data[0];
    }
};

export const deleteOffer = async (offerId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/offers?offer_id=eq.${offerId}&user_id=eq.${USER_ID}`, { method: 'DELETE', headers });
    await handleResponse(response);
};

// --- Brag Bank & Skill Trends ---

export const getBragBankEntries = async (): Promise<BragBankEntry[]> => {
    const response = await fetch(`${API_BASE_URL}/brag_bank_entries?user_id=eq.${USER_ID}&order=created_at.desc`);
    return handleResponse(response);
};

export const createBragBankEntry = async (itemData: BragBankEntryPayload): Promise<BragBankEntry> => {
    const payload = { ...itemData, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/brag_bank_entries`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updateBragBankEntry = async (entryId: string, itemData: BragBankEntryPayload): Promise<BragBankEntry> => {
    const response = await fetch(`${API_BASE_URL}/brag_bank_entries?entry_id=eq.${entryId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(itemData),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const deleteBragBankEntry = async (entryId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/brag_bank_entries?entry_id=eq.${entryId}&user_id=eq.${USER_ID}`, { method: 'DELETE', headers });
    await handleResponse(response);
};

export const getSkillTrends = async (): Promise<SkillTrend[]> => {
    const response = await fetch(`${API_BASE_URL}/skill_trends?user_id=eq.${USER_ID}&order=created_at.desc`);
    return handleResponse(response);
};

export const saveSkillTrend = async (trendData: SkillTrendPayload): Promise<SkillTrend> => {
    const payload = { ...trendData, user_id: USER_ID };
    const response = await fetch(`${API_BASE_URL}/skill_trends`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation,resolution=merge-duplicates' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

// --- Sprint ---

export const getActiveSprint = async (): Promise<Sprint | null> => {
    const response = await fetch(`${API_BASE_URL}/weekly_sprints?user_id=eq.${USER_ID}&start_date=lte.today&select=*,actions:sprint_actions(*)&order=start_date.desc&limit=1`);
    const sprints = await handleResponse(response);
    const latestSprint = sprints?.[0] || null;

    if (latestSprint) {
        const startDate = new Date(latestSprint.start_date + 'T00:00:00Z');
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setUTCDate(sevenDaysAgo.getUTCDate() - 7);
        sevenDaysAgo.setUTCHours(0, 0, 0, 0);

        if (startDate >= sevenDaysAgo) {
            return latestSprint;
        }
    }
    
    return null;
};

export const createSprintWithActions = async (payload: CreateSprintPayload): Promise<Sprint> => {
    const sprintPayload = {
        theme: payload.theme,
        user_id: USER_ID,
        mode: payload.mode,
        start_date: new Date().toISOString().split('T')[0],
        learning_goal: payload.learning_goal,
        cross_functional_collaboration: payload.cross_functional_collaboration,
        growth_alignment: payload.growth_alignment,
        promotion_readiness_notes: payload.promotion_readiness_notes,
        tags: payload.tags,
        strategic_score: payload.strategic_score,
    };
    const sprintResponse = await fetch(`${API_BASE_URL}/weekly_sprints`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(sprintPayload),
    });
    const newSprintArray = await handleResponse(sprintResponse);
    if (!newSprintArray || newSprintArray.length === 0) {
        throw new Error("Failed to create sprint.");
    }
    const newSprint = newSprintArray[0];

    if (payload.actions && payload.actions.length > 0) {
        await addActionsToSprint(newSprint.sprint_id, payload.actions);
    }
    
    const finalSprint = await getActiveSprint();
    if (!finalSprint) {
        throw new Error("Failed to retrieve new sprint after creation.");
    }
    return finalSprint;
};

export const updateSprint = async (sprintId: string, payload: Partial<Sprint>): Promise<Sprint> => {
    const { sprint_id, user_id, created_at, actions, ...updatePayload } = payload;
    
    const response = await fetch(`${API_BASE_URL}/weekly_sprints?sprint_id=eq.${sprintId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(updatePayload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updateSprintAction = async (actionId: string, payload: SprintActionPayload): Promise<SprintAction> => {
     const { action_id, sprint_id, user_id, ...updatePayload } = payload as any;
     const response = await fetch(`${API_BASE_URL}/sprint_actions?action_id=eq.${actionId}&user_id=eq.${USER_ID}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(updatePayload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const addActionsToSprint = async (sprintId: string, actions: Omit<SprintActionPayload, 'sprint_id'>[]): Promise<void> => {
    const payload = actions.map(action => ({
        ...action,
        sprint_id: sprintId,
        user_id: USER_ID,
    }));
     await fetch(`${API_BASE_URL}/sprint_actions`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
};

// --- Scheduler / Dev Mode ---

export const getSiteSchedules = async (): Promise<SiteSchedule[]> => {
    const response = await fetch(`${API_BASE_URL}/site_schedules?order=site_name.asc,created_at.desc`);
    return handleResponse(response);
};

export const getJobSites = async (): Promise<SiteDetails[]> => {
    const response = await fetch(buildFastApiUrl('job-feed/sites'));
    const rawData = await handleResponse(response);

    if (rawData && rawData.status === 'success' && rawData.data) {
        // The data is an object of objects, where the key is the site id (e.g., 'indeed')
        // and the value is the site details.
        // We need to convert this into an array of SiteDetails.
        return Object.values(rawData.data).map((site: any) => ({
            site_name: site.name,
            supports_remote: site.supports_remote,
            supports_salary_filter: site.supports_salary_filter,
            requires: site.requires || [],
            optional: site.optional || [],
            conflicts: site.conflicts || [],
            notes: site.notes || []
        }));
    }

    console.warn('Unexpected data format for sites from API:', rawData);
    // If the format is unexpected or status is not 'success', return an empty array.
    return [];
};

export const createSiteSchedule = async (payload: SiteSchedulePayload): Promise<SiteSchedule> => {
    const response = await fetch(`${API_BASE_URL}/site_schedules`, {
        method: 'POST',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const updateSiteSchedule = async (scheduleId: string, payload: SiteSchedulePayload): Promise<SiteSchedule> => {
    const response = await fetch(`${API_BASE_URL}/site_schedules?id=eq.${scheduleId}`, {
        method: 'PATCH',
        headers: { ...headers, 'Prefer': 'return=representation' },
        body: JSON.stringify(payload),
    });
    const data = await handleResponse(response);
    return data[0];
};

export const deleteSiteSchedule = async (scheduleId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/site_schedules?id=eq.${scheduleId}`, {
        method: 'DELETE',
        headers,
    });
    await handleResponse(response);
};

// --- Document Management via FastAPI ---

// Generic uploader for JSON data
const uploadJsonDocument = async (endpoint: string, payload: object): Promise<UploadSuccessResponse> => {
    const response = await fetch(buildFastApiUrl(endpoint), {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
    });
    return handleResponse(response);
};

export const uploadCareerBrand = (payload: any) => uploadJsonDocument('/documents/career-brand', payload);
export const uploadCareerPath = (payload: any) => uploadJsonDocument('/documents/career-paths', payload);
export const uploadJobSearchStrategy = (payload: any) => uploadJsonDocument('/documents/job-search-strategies', payload);

// Uploader for resume file data
export const uploadResume = async (formData: FormData): Promise<UploadSuccessResponse> => {
    const response = await fetch(buildFastApiUrl('documents/resume'), {
        method: 'POST',
        body: formData,
        // No 'Content-Type' header here for FormData, browser sets it.
    });
    return handleResponse(response);
};

export const getUploadedDocuments = async (profileId: string): Promise<UploadedDocument[]> => {
    if (!profileId) return [];
    const response = await fetch(`${buildFastApiUrl('documents')}?profile_id=${profileId}`);
    const data = await handleResponse(response);
    return (data?.documents || []).sort((a: UploadedDocument, b: UploadedDocument) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
};

export const deleteUploadedDocument = async (documentId: string, contentType: ContentType): Promise<void> => {
    const response = await fetch(buildFastApiUrl(`documents/${documentId}`), {
        method: 'DELETE',
    });
    await handleResponse(response);
};

// --- Reviewed Jobs ---

export interface ReviewedJobsFilters {
  recommendation?: 'All' | 'Recommended' | 'Not Recommended';
  min_score?: number;
}

export interface ReviewedJobsSort {
  by: 'date_posted' | 'overall_alignment_score' | 'review_date';
  order: 'asc' | 'desc';
}

export const getReviewedJobs = async ({ page = 1, size = 15, filters = {}, sort = { by: 'date_posted', order: 'desc' } }: {
    page?: number;
    size?: number;
    filters?: ReviewedJobsFilters;
    sort?: ReviewedJobsSort;
}): Promise<PaginatedResponse<ReviewedJob>> => {
    const formatSalaryComponent = (value: unknown): string | null => {
        if (value === null || value === undefined) {
            return null;
        }

        const numericValue = Number(value);
        if (Number.isFinite(numericValue)) {
            return numericValue.toLocaleString(undefined, {
                maximumFractionDigits: 2,
                minimumFractionDigits: 0,
            });
        }

        return String(value);
    };

    const params = new URLSearchParams({
        limit: String(size),
        offset: String(Math.max(page - 1, 0) * size),
    });

    const sortByParam = sort.by;
    params.append('sort_by', sortByParam);
    params.append('sort_order', sort.order.toUpperCase());

    if (filters.recommendation && filters.recommendation !== 'All') {
        params.append('recommendation', filters.recommendation === 'Recommended' ? 'true' : 'false');
    }

    if (typeof filters.min_score === 'number') {
        params.append('min_score', String(filters.min_score));
    }

    const response = await fetch(`${buildFastApiUrl('jobs/reviews')}?${params.toString()}`);
    const rawData = await handleResponse(response);

    const items = (rawData.jobs || []).map((entry: any) => {
        const job = entry.job || {};
        const review = entry.review || {};

        const hasOverride = typeof review.override_recommend === 'boolean';
        const finalRecommendation = hasOverride ? review.override_recommend : review.recommendation;
        const recommendation: ReviewedJobRecommendation = finalRecommendation ? 'Recommended' : 'Not Recommended';
        const confidenceLookup: Record<string, number> = { high: 0.9, medium: 0.6, low: 0.3 };

        const overallScore = typeof review.overall_alignment_score === 'number'
            ? review.overall_alignment_score
            : 0;

        return {
            job_id: job.job_id ?? '',
            url: job.url ?? null,
            title: job.title ?? null,
            company_name: job.company ?? null,
            location: job.location ?? null,
            date_posted: job.date_posted ?? null,
            recommendation,
            confidence: confidenceLookup[String(review.confidence).toLowerCase()] ?? 0.3,
            overall_alignment_score: overallScore,
            is_eligible_for_application: Boolean(finalRecommendation),
            salary_min: formatSalaryComponent(job.salary_min),
            salary_max: formatSalaryComponent(job.salary_max),
            salary_currency: job.salary_currency ?? null,
            salary_range: job.salary_range ?? null,
            // AI review details
            rationale: review.rationale ?? null,
            tldr_summary: review.tldr_summary ?? null,
            confidence_level: review.confidence ?? null,
            crew_output: review.crew_output ?? null,
            // HITL override fields
            override_recommend: review.override_recommend ?? null,
            override_comment: review.override_comment ?? null,
            override_by: review.override_by ?? null,
            override_at: review.override_at ?? null,
            // Job description content
            description: job.description ?? null,
        } as ReviewedJob;
    });

    const pageSize = rawData.page_size ?? size;
    const total = rawData.total_count ?? 0;

    if (sort.by === 'overall_alignment_score') {
        items.sort((a: ReviewedJob, b: ReviewedJob) => {
            return sort.order === 'asc'
                ? a.overall_alignment_score - b.overall_alignment_score
                : b.overall_alignment_score - a.overall_alignment_score;
        });
    }

    return {
        items,
        total,
        page: rawData.page ?? page,
        size: pageSize,
        pages: pageSize ? Math.max(1, Math.ceil(total / pageSize)) : 1,
    };
};

// Job Review Override API
export interface JobReviewOverrideRequest {
    override_recommend: boolean;
    override_comment: string;
}

export interface JobReviewOverrideResponse {
    id: string;
    job_id: string;
    recommend: boolean | null;
    confidence: string | null;
    rationale: string | null;
    override_recommend: boolean;
    override_comment: string;
    override_by: string;
    override_at: string;
    created_at: string;
    updated_at: string;
}

export const overrideJobReview = async (
    jobId: string, 
    overrideData: JobReviewOverrideRequest
): Promise<JobReviewOverrideResponse> => {
    const response = await fetch(buildFastApiUrl(`jobs/reviews/${jobId}/override`), {
        method: 'POST',
        headers,
        body: JSON.stringify(overrideData),
    });

    return handleResponse(response);
};

// --- LinkedIn Jobs ---

export const fetchLinkedInJobByUrl = async (url: string): Promise<any> => {
    const response = await fetch(buildFastApiUrl('linkedin-jobs/fetch-by-url'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ url }),
    });

    return handleResponse(response);
};

export const getJobReviewStatus = async (jobId: string): Promise<any> => {
    const response = await fetch(buildFastApiUrl(`linkedin-jobs/review-status/${jobId}`), {
        method: 'GET',
        headers,
    });

    return handleResponse(response);
};

export const enqueueResumeTailoringJob = async (
    payload: ResumeTailoringJobPayload
): Promise<TaskEnqueueResponse> => {
    const response = await fetch(buildFastApiUrl('tasks/resume-tailoring'), {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    return handleResponse(response);
};

export const enqueueCompanyResearchJob = async (
    payload: CompanyResearchJobPayload
): Promise<TaskEnqueueResponse> => {
    const response = await fetch(buildFastApiUrl('tasks/company-research'), {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    return handleResponse(response);
};

export const getTaskRunStatus = async (runId: string): Promise<TaskRunRecord> => {
    const response = await fetch(buildFastApiUrl(`tasks/${runId}`), {
        method: 'GET',
        headers,
    });

    return handleResponse(response);
};

export const generateApplicationFromJob = async (jobId: string, narrativeId?: string): Promise<any> => {
    const url = narrativeId
        ? buildFastApiUrl(`applications/generate-from-job/${jobId}?narrative_id=${narrativeId}`)
        : buildFastApiUrl(`applications/generate-from-job/${jobId}`);

    const response = await fetch(url, {
        method: 'POST',
        headers,
    });

    return handleResponse(response);
};

export const createApplicationFromJob = async (jobId: string, mode: string = 'fast_track', narrativeId?: string): Promise<any> => {
    let url = buildFastApiUrl(`applications/create-from-job/${jobId}?mode=${mode}`);
    if (narrativeId) {
        url += `&narrative_id=${narrativeId}`;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers,
    });

    return handleResponse(response);
};
