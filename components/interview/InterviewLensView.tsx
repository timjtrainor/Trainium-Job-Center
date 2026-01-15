import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StrategySetup } from './StrategySetup';
import { TheWarRoom } from './TheWarRoom';
import { LoadingSpinner, ChevronLeftIcon } from '../IconComponents';
import * as apiService from '../../services/apiService';
import {
    JobApplication, Interview, Company, StrategicNarrative,
    InterviewLensSetup, LensNarrativeStyle, PersonaDefinition, TMAYConfig
} from '../../types';

interface InterviewLensViewProps {
    applications: JobApplication[];
    companies: Company[];
    activeNarrative: StrategicNarrative | null;
    onSaveInterview: (data: any, id: string) => Promise<void>;
    isAppLoading: boolean;
}

export const InterviewLensView: React.FC<InterviewLensViewProps> = ({
    applications,
    companies,
    activeNarrative,
    onSaveInterview,
    isAppLoading,
}) => {
    const { interviewId } = useParams<{ interviewId: string }>();
    const navigate = useNavigate();
    const [isWarRoomActive, setIsWarRoomActive] = useState(false);

    const { app, interview, company } = useMemo(() => {
        console.log('InterviewLensView search:', { interviewId, applicationCount: applications?.length, companyCount: companies?.length });
        if (!applications || !companies || !interviewId) return { app: null, interview: null, company: null };
        for (const app of applications) {
            const interview = app.interviews?.find((i: any) => i.interview_id === interviewId);
            if (interview) {
                const company = companies.find((c: any) => c.company_id === app.company_id);
                console.log('InterviewLensView found:', { app: app.job_title, interview: interview.interview_type, company: company?.company_name });
                return { app, interview, company };
            }
        }
        console.warn('InterviewLensView: No match found for interviewId:', interviewId);
        return { app: null, interview: null, company: null };
    }, [applications, interviewId, companies]);

    if (isAppLoading || !app || !interview || !company) {
        return <div className="flex h-screen items-center justify-center bg-slate-50"><LoadingSpinner className="h-12 w-12" /></div>;
    }

    // Handle saving the setup
    const handleSaveSetup = async (setup: InterviewLensSetup, persona: PersonaDefinition, tmay: TMAYConfig) => {
        try {
            await onSaveInterview({
                interview_strategy_state: {
                    ...(interview.interview_strategy_state || {}),
                    persona,
                    tmay,
                    lens_setup: setup
                }
            }, interview.interview_id);
        } catch (err) {
            console.error('Failed to save interview lens setup:', err);
        }
    };

    const handleLaunchWarRoom = () => {
        setIsWarRoomActive(true);
    };

    if (isWarRoomActive) {
        const setup = interview.interview_strategy_state?.lens_setup;
        if (!setup) {
            setIsWarRoomActive(false);
            return null;
        }

        return (
            <TheWarRoom
                setup={setup}
                tmay={interview.interview_strategy_state?.tmay || { hook: '', bridge: '', pivot: '' }}
                persona={interview.interview_strategy_state?.persona || { buyer_type: 'Hiring Manager', primary_anxiety: '', win_condition: '', functional_friction_point: '' }}
                activeNarrative={activeNarrative}
                onExit={() => setIsWarRoomActive(false)}
            />
        );
    }

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Navigation Header */}
            <nav className="h-16 border-b bg-white flex items-center px-8">
                <button
                    onClick={() => navigate(`/application/${app.job_application_id}?tab=interviews`)}
                    className="flex items-center text-slate-500 hover:text-slate-800 transition-colors font-bold text-sm"
                >
                    <ChevronLeftIcon className="h-4 w-4 mr-2" />
                    Back to Interview Prep
                </button>
                <div className="ml-auto flex items-center space-x-4">
                    <span className="text-xs font-black uppercase tracking-widest text-slate-400">Context: {company.company_name}</span>
                    <div className="h-8 w-[2px] bg-slate-100" />
                    <span className="text-sm font-bold text-slate-800">{app.job_title}</span>
                </div>
            </nav>

            <StrategySetup
                application={app}
                interview={interview}
                company={company}
                activeNarrative={activeNarrative}
                onSave={handleSaveSetup}
                onLaunchWarRoom={handleLaunchWarRoom}
            />
        </div>
    );
};
