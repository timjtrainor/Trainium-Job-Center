import { fireEvent, render, screen } from '@testing-library/react';
import { InterviewCopilotView } from '../InterviewCopilotView';
import { Company, Interview, JobApplication, JobProblemAnalysisResult, StrategicNarrative } from '../../types';

const jobAnalysis: JobProblemAnalysisResult = {
    core_problem_analysis: {
        business_context: 'Retention is lagging in the first 90 days.',
        core_problem: 'Reducing churn for new customers',
        strategic_importance: 'Critical for recurring revenue stability'
    },
    key_success_metrics: ['Increase day-30 retention to 60%'],
    role_levers: ['Onboarding experience', 'Lifecycle messaging'],
    potential_blockers: ['Limited analytics visibility'],
    suggested_positioning: 'Product leader who has rebuilt onboarding funnels',
    tags: ['growth', 'activation']
};

const baseApplication: JobApplication = {
    job_application_id: 'app-1',
    user_id: 'user-1',
    narrative_id: 'nar-1',
    company_id: 'comp-1',
    job_title: 'Product Manager',
    job_description: 'Drive adoption',
    date_applied: '2024-01-01',
    created_at: '2024-01-01',
    job_problem_analysis_result: jobAnalysis
} as JobApplication;

const baseInterview: Interview = {
    interview_id: 'int-1',
    job_application_id: 'app-1',
    interview_type: 'Hiring Manager',
    interview_date: '2024-01-10',
    strategic_opening: 'Opening line',
    strategic_questions_to_ask: ['How is retention trending?'],
    story_deck: [],
    live_notes: 'Initial notes',
    prep_outline: {
        role_intelligence: {
            core_problem: 'Reducing churn for new customers',
            key_success_metrics: ['Increase day-30 retention to 60%'],
            role_levers: ['Onboarding experience'],
            potential_blockers: ['Limited analytics visibility'],
            suggested_positioning: 'Product leader who has rebuilt onboarding funnels'
        },
        jd_insights: {
            business_context: 'Retention is lagging in the first 90 days.',
            strategic_importance: 'Critical for recurring revenue stability',
            tags: ['growth', 'activation']
        }
    }
} as unknown as Interview;

const activeNarrative: StrategicNarrative = {
    narrative_id: 'nar-1',
    user_id: 'user-1',
    narrative_name: 'North Star',
    desired_title: 'Product Leader',
    positioning_statement: 'Product operator delivering retention turnarounds',
    impact_story_title: 'Improved activation by 25%',
    impact_stories: []
} as unknown as StrategicNarrative;

const company: Company = {
    company_id: 'comp-1',
    user_id: 'user-1',
    company_name: 'Acme Corp'
};

describe('InterviewCopilotView', () => {
    const renderView = () =>
        render(
            <InterviewCopilotView
                application={baseApplication}
                interview={baseInterview}
                company={company}
                activeNarrative={activeNarrative}
                onBack={() => undefined}
                onSaveInterview={async () => undefined}
                onGenerateInterviewPrep={async () => undefined}
                onGenerateRecruiterScreenPrep={async () => undefined}
            />
        );

    it('shows live rundown elements in view mode by default', () => {
        renderView();

        expect(screen.getByText('Job Cheat Sheet')).toBeInTheDocument();
        expect(screen.getByText('Live Notes')).toBeInTheDocument();
        expect(screen.queryByText('Role Intelligence Research')).not.toBeInTheDocument();
    });

    it('switches to prep workspace when toggled', () => {
        renderView();

        const toggle = screen.getByRole('switch');
        fireEvent.click(toggle);

        expect(screen.getByText('Role Intelligence Research')).toBeInTheDocument();
        expect(screen.queryByText('Live Notes')).not.toBeInTheDocument();
    });
});
