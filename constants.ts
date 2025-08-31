// This file contains constants for the application.

// Placeholder for the PostgREST server URL.
// In a real-world scenario, this would come from an environment variable.
export const API_BASE_URL = 'http://localhost:3000';

// Hardcoded user ID for the single-user version of the app.
// This allows the data model to be ready for multi-user in the future.
export const USER_ID = '11111111-2222-3333-4444-555555555555';


export const CONTACT_PERSONAS = [
    { type: 'Hiring Manager', description: 'The person who owns the open role and is likely to make the final hiring decision. Usually a Director, VP, or Head of Product.' },
    { type: 'Peer', description: 'A fellow Product Manager or Engineer at the same level or in a collaborating team. Useful for internal advocacy and cultural signal.' },
    { type: 'Recruiter', description: 'An internal or external recruiter involved in filling the role. Often the first point of contact, especially for larger orgs.' },
    { type: 'Product Leader', description: 'A senior leader such as Principal PM, Group PM, or CPO who can be an advocate or influencer in hiring.' },
    { type: 'Cross-Functional Stakeholder', description: 'Someone in adjacent roles (Engineering, Design, Data, Customer Success) who may influence hiring or provide insider context.' },
    { type: 'Alumni Contact', description: 'Someone who has worked at the same company as you before or shares an educational/professional background. Great for warm intros.' },
    { type: 'Executive Contact', description: 'High-level exec (VP, SVP, C-level) with broad strategic influence. Used selectively for high-impact outreach.' }
] as const;

export const INTERVIEW_TYPES = [
    "Recruiter Call",
    "Phone Screen",
    "Hiring Manager",
    "Technical Interview",
    "Behavioral Interview",
    "Case Study",
    "Panel Interview",
    "Final Round",
    "Informational",
] as const;