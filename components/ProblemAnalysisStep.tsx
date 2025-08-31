import React from 'react';
import { LoadingSpinner } from './IconComponents';
import { JobProblemAnalysisResult, CoreProblemAnalysis } from '../types';

interface ProblemAnalysisStepProps {
  jobProblemAnalysisResult: JobProblemAnalysisResult | null;
  strategicFitScore: number | null;
  assumedRequirements: string[];
  onConfirm: (isInterested: boolean) => void;
  companyName: string;
  isLoadingAnalysis: boolean;
  isConfirming: boolean;
}

const EditableTextarea = ({ label, value, readOnly = true }: { label: string, value: string | undefined, readOnly?: boolean }) => (
    <div>
        <label className="block text-sm font-medium text-slate-600 dark:text-slate-400">{label}</label>
        <textarea
            rows={3}
            value={value || ''}
            readOnly={readOnly}
            className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 shadow-sm sm:text-sm"
        />
    </div>
);

const ReadonlyStringList = ({ label, values }: { label: string, values: string[] | undefined }) => (
     <div>
        <label className="block text-sm font-medium text-slate-600 dark:text-slate-400">{label}</label>
        <ul className="mt-1 list-disc list-inside text-sm text-slate-700 dark:text-slate-300 space-y-1">
            {(values || []).map((v, i) => <li key={i}>{v}</li>)}
            {(values || []).length === 0 && <li className="list-none">N/A</li>}
        </ul>
    </div>
);


export const ProblemAnalysisStep = (props: ProblemAnalysisStepProps) => {
    const { jobProblemAnalysisResult, strategicFitScore, assumedRequirements, onConfirm, companyName, isLoadingAnalysis, isConfirming } = props;

    if (isLoadingAnalysis || !jobProblemAnalysisResult) {
        return (
            <div className="flex flex-col items-center justify-center text-center py-24 animate-fade-in">
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 bg-blue-200 dark:bg-blue-500/30 rounded-full animate-ping"></div>
                    <svg className="relative w-16 h-16 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-1.83m-1.5 1.83a6.01 6.01 0 0 1-1.5-1.83m1.5 1.83v-5.25m0 0A2.25 2.25 0 0 1 9.75 9.75M12 12.75c0 .621.504 1.125 1.125 1.125s1.125-.504 1.125-1.125S13.125 11.625 12 11.625 10.875 12.129 10.875 12.75m0-4.5A2.25 2.25 0 0 1 12 6.75" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.41-.04-.81-.1-1.2M15 4.5l-1.5 1.5" />
                    </svg>
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-6">Analyzing Job...</h2>
                <p className="mt-2 max-w-md mx-auto text-slate-600 dark:text-slate-400">
                    The AI is deconstructing the role for {companyName} to find the core business problem. This may take a moment.
                </p>
            </div>
        );
    }
    
    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 4: Strategic Fit Check</h2>
                <p className="mt-1 text-slate-600 dark:text-slate-400">Review the AI's strategic analysis of the role. Does this opportunity align with your goals?</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700 space-y-4">
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">Strategic Role Analysis for {companyName}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4 md:col-span-2">
                            <h4 className="text-md font-semibold text-slate-700 dark:text-slate-300">Core Problem Analysis</h4>
                            <EditableTextarea label="Business Context" value={jobProblemAnalysisResult.core_problem_analysis?.business_context} />
                            <EditableTextarea label="Core Problem" value={jobProblemAnalysisResult.core_problem_analysis?.core_problem} />
                            <EditableTextarea label="Strategic Importance" value={jobProblemAnalysisResult.core_problem_analysis?.strategic_importance} />
                        </div>
                        <ReadonlyStringList label="Key Success Metrics" values={jobProblemAnalysisResult.key_success_metrics} />
                        <ReadonlyStringList label="Role Levers" values={jobProblemAnalysisResult.role_levers} />
                        <ReadonlyStringList label="Potential Blockers" values={jobProblemAnalysisResult.potential_blockers} />
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-slate-600 dark:text-slate-400">Suggested Positioning</label>
                            <p className="mt-1 text-sm text-slate-800 dark:text-slate-200 italic p-2 bg-slate-100 dark:bg-slate-700/50 rounded-md">"{jobProblemAnalysisResult.suggested_positioning}"</p>
                        </div>
                    </div>
                </div>
                <div className="space-y-4">
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700 text-center"><h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300">Strategic Fit Score</h4><p className="text-5xl font-bold text-blue-600 dark:text-blue-400 my-2">{strategicFitScore?.toFixed(1) ?? '...'}</p><p className="text-xs text-blue-700 dark:text-blue-400">Alignment with your career North Star and Mastery.</p></div>
                    <div className="p-4 bg-purple-50 dark:bg-purple-900/30 rounded-lg border border-purple-200 dark:border-purple-700"><h4 className="text-sm font-semibold text-purple-800 dark:text-purple-300">Assumed Requirements</h4><p className="text-xs text-purple-600 dark:text-purple-400 mt-1">Based on standard roles, the AI assumes these are unstated expectations.</p><ul className="list-disc pl-4 text-xs mt-2 text-purple-700 dark:text-purple-300 space-y-1">{(assumedRequirements || []).map((req, i) => <li key={i}>{req}</li>)}</ul></div>
                </div>
            </div>
            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-slate-200 dark:border-slate-700"><button onClick={() => onConfirm(false)} disabled={isConfirming} className="px-6 py-2 text-base font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm transition-colors">Not Interested</button><button onClick={() => onConfirm(true)} disabled={isConfirming} className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors disabled:bg-green-400">{isConfirming ? <LoadingSpinner /> : "Yes, I'm Interested!"}</button></div>
        </div>
    );
};