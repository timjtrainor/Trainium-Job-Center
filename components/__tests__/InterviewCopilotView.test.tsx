import { fireEvent, render, screen } from '@testing-library/react';
import { InterviewCopilotView } from '../InterviewCopilotView';
import { Company, Interview, JobApplication, JobProblemAnalysisResult, StrategicNarrative } from '../../types';

const baseApplication: JobApplication = {
    job_application_id: 'app-1',
    user_id: 'user-1',
    company_id: 'comp-1',
    // Mock company_name here for convenience if needed by checks that rely on application data, 
    // but the component uses the separate company prop now.
    job_title: 'Product Manager',
    job_description: 'Drive adoption',
    date_applied: '2024-01-01',
    created_at: '2024-01-01',
} as JobApplication;

const baseInterview: Interview = {
    interview_id: 'int-1',
    job_application_id: 'app-1',
    interview_type: 'Hiring Manager',
    interview_date: '2024-01-10',
    live_notes: 'Initial notes',
    interview_strategy_state: {
        persona: {
            buyer_type: 'Recruiter',
            primary_anxiety: 'Loss Aversion',
            win_condition: 'Safety',
            functional_friction_point: 'Process'
        },
        tmay: { hook: 'Hook', bridge: 'Bridge', pivot: 'Pivot' },
        questions: [],
        success_metrics: [],
        potential_blockers: [],
        power_vocabulary: {},
        discovery_questions: []
    }
} as unknown as Interview;

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
                onBack={() => undefined}
                onSaveInterview={async () => undefined}
            />
        );

    it('renders the Command Center with company info', () => {
        renderView();
        expect(screen.getByText('Command Center')).toBeInTheDocument();
        expect(screen.getByText('Acme Corp')).toBeInTheDocument();
        expect(screen.getByText('Product Manager')).toBeInTheDocument();
    });

    it('defaults to Interview Strategy tab and shows editor', () => {
        renderView();
        // There might be multiple "Interview Strategy" texts (button and header)
        const headings = screen.getAllByText('Interview Strategy');
        expect(headings.length).toBeGreaterThan(0);

        expect(screen.getByText('Must-Have Definitions')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Loss Aversion')).toBeInTheDocument();
    });

    it('navigates to TMAY tab', () => {
        renderView();
        const tmayTab = screen.getByText('TMAY');
        fireEvent.click(tmayTab);

        expect(screen.getByText('The Hook (Past/Context)')).toBeInTheDocument();
        expect(screen.getByText('Hook')).toBeInTheDocument();
    });

    it('shows Live Notes in the right sidebar', () => {
        renderView();
        expect(screen.getByText('Live Notes')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Initial notes')).toBeInTheDocument();
    });
});
