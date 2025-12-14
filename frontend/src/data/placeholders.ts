export interface Placeholder {
    name: string;
    description: string;
}

export const PLACEHOLDERS: Placeholder[] = [
    // Job & Company Data
    { name: 'URL', description: 'The URL of the job posting.' },
    { name: 'COMPANY_NAME', description: 'The name of the company.' },
    { name: 'JOB_TITLE', description: 'The title of the job.' },
    { name: 'JOB_DESCRIPTION', description: 'The full job description text.' },
    { name: 'MISSION', description: "The company's mission statement." },
    { name: 'VALUES', description: "The company's core values." },
    { name: 'NEWS', description: 'A recent news snippet about the company.' },
    { name: 'GOALS', description: "The company's strategic goals." },
    { name: 'ISSUES', description: "Publicly known issues or challenges for the company." },
    
    // Resume & Skills Data
    { name: 'ACCOMPLISHMENTS', description: 'A JSON array of resume accomplishments to be optimized.' },
    { name: 'ACCOMPLISHMENT_COUNT', description: 'The number of accomplishments to rank and return.' },
    { name: 'FULL_RESUME_BULLETS', description: 'A single string of all work experience bullet points from the resume.' },
    { name: 'FULL_WORK_EXPERIENCE_JSON', description: 'A JSON string of the work_experience array from the resume.' },
    { name: 'FULL_RESUME_JSON', description: 'A JSON string of the entire resume object.' },
    { name: 'RESUME_TEXT', description: 'A single string of all work experience bullet points from the resume.' },
    { name: 'SKILL_SECTION_HEADING', description: 'The heading of a specific skill section (e.g., "Technical").' },
    { name: 'CURRENT_SKILLS', description: 'A comma-separated string of current skills in a section.' },

    // AI-Generated Context
    { name: 'GUIDANCE', description: 'The AI-generated strategic guidance for resume tailoring.' },
    { name: 'KEYWORDS', description: 'The AI-generated hard and soft keywords.' },
    { name: 'AI_SUMMARY', description: "The AI's analysis of the core business problem of the job." },
    { name: 'SUMMARY', description: 'The user-selected summary paragraph (for generating summary bullets).' },
    { name: 'QUESTIONS', description: 'A JSON array of application questions to be answered.' },
    { name: 'USER_THOUGHTS', description: 'A JSON array of user-provided notes for each question.' },
    { name: 'VOICE_GUIDANCE', description: 'Optional guidance on the narrative voice to use for answers.' },


    // Networking & Contact Data
    { name: 'MY_JOB_TITLE', description: "Your current job title from your base resume." },
    { name: 'MY_SUMMARY', description: "Your professional summary paragraph from your base resume." },
    { name: 'CONTACT_FIRST_NAME', description: "The first name of the professional contact." },
    { name: 'CONTACT_JOB_TITLE', description: "The job title of the professional contact." },
    { name: 'POST_TEXT', description: 'The text of the LinkedIn post to comment on.' },
    { name: 'CONNECTION_MESSAGE', description: 'The original connection message sent to the contact.' },
    
    // LinkedIn Post Generation
    { name: 'RECENT_APPLICATIONS', description: 'A summary of recent job applications.' },
    { name: 'RECENT_MESSAGES', description: 'A summary of recent outreach messages.' },
    { name: 'THEME', description: 'The selected theme for a LinkedIn post.' },
];