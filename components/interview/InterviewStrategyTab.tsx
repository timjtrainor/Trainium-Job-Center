import React, { useState, useEffect } from 'react';
import {
    JobApplication,
    Company,
    InterviewStrategy,
    JobProblemAnalysis
} from '../../types';
import * as apiService from '../../services/apiService';
import {
    ArrowPathIcon,
    SparklesIcon,
    BeakerIcon,
    MagnifyingGlassIcon,
    BoltIcon,
    ChartBarIcon,
    ChatBubbleBottomCenterTextIcon,
    ExclamationTriangleIcon,
    CheckCircleIcon
} from '@heroicons/react/24/outline';

interface InterviewStrategyTabProps {
    application: JobApplication;
    company: Company;
    onUpdateApplication: (appId: string, data: Partial<JobApplication>) => Promise<void>;
    userProfile: any;
}

export const InterviewStrategyTab: React.FC<InterviewStrategyTabProps> = ({
    application,
    company,
    onUpdateApplication,
    userProfile
}) => {
    const [strategy, setStrategy] = useState<InterviewStrategy | undefined>(application.interview_strategy);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [researchingField, setResearchingField] = useState<string | null>(null);

    useEffect(() => {
        setStrategy(application.interview_strategy);
    }, [application.interview_strategy]);

    const handleGenerateStrategy = async () => {
        setIsGenerating(true);
        setError(null);
        try {
            const careerDna = userProfile?.master_career_dna || {
                mission: "To build software that matters.",
                stories: []
            };

            const result = await apiService.generateApplicationStrategy(
                application.job_description,
                company,
                careerDna,
                application.job_problem_analysis_result,
                application.vocabulary_mirror,
                application.alignment_strategy
            );

            setStrategy(result);
            await onUpdateApplication(application.job_application_id, { interview_strategy: result });
        } catch (error: any) {
            console.error("Failed to generate strategy:", error);
            setError(error.message || "Failed to generate strategy.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleResearchField = async (field: keyof Company, topic: string) => {
        setResearchingField(String(field));
        try {
            const result = await apiService.researchShadowTruth(
                company.company_name,
                topic,
                `Context: I am applying for ${application.job_title}. Need to know about ${topic}.`
            );
            await apiService.updateCompany(company.company_id, { [field]: { text: result.content, source: 'ai_research' } });
            alert(`Research complete for ${topic}. Please refresh page to see updates in Context Hub.`);
        } catch (e: any) {
            console.error(e);
            setError(e.message || `Failed to research ${topic}.`);
        } finally {
            setResearchingField(null);
        }
    };

    if (!strategy) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                <div className="p-4 bg-white dark:bg-slate-800 rounded-full shadow-lg mb-6">
                    <SparklesIcon className="h-10 w-10 text-blue-500" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                    No Interview Strategy Generated
                </h3>
                <p className="text-slate-500 dark:text-slate-400 max-w-md text-center mb-8">
                    Transform your interview prep from "Feature Listing" to "Consultative Selling".
                    Generate a bespoke strategy based on the company's diagnosed pathologies.
                </p>
                {error && (
                    <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/20 rounded-xl text-red-700 dark:text-red-400 text-sm">
                        {error}
                    </div>
                )}
                <button
                    onClick={handleGenerateStrategy}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
                >
                    {isGenerating ? (
                        <>
                            <ArrowPathIcon className="h-5 w-5 animate-spin" />
                            Diagnosing Pathology...
                        </>
                    ) : (
                        <>
                            <BeakerIcon className="h-5 w-5" />
                            Generate Strategy
                        </>
                    )}
                </button>
            </div>
        );
    }

    const { job_problem_analysis, strategic_fit_score = 0, assumed_requirements = [] } = strategy;

    // Defensive guard for non-v3 data
    if (!job_problem_analysis || !job_problem_analysis.diagnostic_intel) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                <div className="p-4 bg-white dark:bg-slate-800 rounded-full shadow-lg mb-6">
                    <ExclamationTriangleIcon className="h-10 w-10 text-amber-500" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                    Incompatible Strategy Flow
                </h3>
                <p className="text-slate-500 dark:text-slate-400 max-w-md text-center mb-8">
                    This application contains legacy strategy data. Please regenerate the strategy to use the new Consultative Blueprint format.
                </p>
                <button
                    onClick={handleGenerateStrategy}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
                >
                    {isGenerating ? (
                        <>
                            <ArrowPathIcon className="h-5 w-5 animate-spin" />
                            Regenerating...
                        </>
                    ) : (
                        <>
                            <ArrowPathIcon className="h-5 w-5" />
                            Regenerate Strategy
                        </>
                    )}
                </button>
            </div>
        );
    }

    const { diagnostic_intel, economic_logic_gates, content_intelligence } = job_problem_analysis;

    return (
        <div className="space-y-8 animate-fade-in pb-20">
            {/* Header / Actions / Score */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Application Strategy Studio</h2>
                    <p className="text-slate-500 dark:text-slate-400">Consultative gameplan for {company.company_name}.</p>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Strategic Fit</span>
                        <div className="flex items-center gap-2">
                            <div className="h-2 w-32 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-1000 ${strategic_fit_score >= 80 ? 'bg-emerald-500' :
                                        strategic_fit_score >= 60 ? 'bg-amber-500' : 'bg-red-500'
                                        }`}
                                    style={{ width: `${strategic_fit_score}%` }}
                                />
                            </div>
                            <span className="text-lg font-black text-slate-900 dark:text-white">{strategic_fit_score}%</span>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerateStrategy}
                        disabled={isGenerating}
                        className="flex items-center gap-1.5 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
                    >
                        <ArrowPathIcon className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
                        {isGenerating ? 'Refreshing...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* Gap Analysis Warning */}
            {(!company.internal_gripes?.text || !company.org_headwinds?.text) && (
                <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/20 rounded-2xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex items-start gap-3">
                        <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                            <h4 className="font-bold text-amber-800 dark:text-amber-200 text-sm">Missing Shadow Truth</h4>
                            <p className="text-xs text-amber-700 dark:text-amber-300">
                                Your strategy is optimized for public data. Add internal insights for better diagnostic accuracy.
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        {!company.internal_gripes?.text && (
                            <button
                                onClick={() => handleResearchField('internal_gripes', 'Internal Employee Gripes & Culture Issues')}
                                disabled={!!researchingField}
                                className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-amber-200 dark:border-amber-700 rounded-lg text-[10px] font-bold text-amber-700 dark:text-amber-300 shadow-sm"
                            >
                                Research Gripes
                            </button>
                        )}
                        {!company.org_headwinds?.text && (
                            <button
                                onClick={() => handleResearchField('org_headwinds', 'Organizational Headwinds & Market Threats')}
                                disabled={!!researchingField}
                                className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-amber-200 dark:border-amber-700 rounded-lg text-[10px] font-bold text-amber-700 dark:text-amber-300 shadow-sm"
                            >
                                Research Headwinds
                            </button>
                        )}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* 1. Diagnostic Intel */}
                <div className="space-y-6">
                    <div className="flex items-center gap-2 mb-2">
                        <BoltIcon className="h-5 w-5 text-blue-500" />
                        <h3 className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-widest text-xs">Diagnostic Intel</h3>
                    </div>

                    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-6">
                        <div>
                            <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">The Diagnosed Pathology</h4>
                            <div className="space-y-1">
                                {Array.isArray(diagnostic_intel.failure_state_portfolio) ? (
                                    diagnostic_intel.failure_state_portfolio.map((item, i) => (
                                        <p key={i} className="text-sm font-bold text-red-600 dark:text-red-400 leading-tight border-l-2 border-red-200 dark:border-red-900/30 pl-3 py-1">
                                            "{item}"
                                        </p>
                                    ))
                                ) : (
                                    <p className="text-lg font-bold text-red-600 dark:text-red-400 leading-tight">
                                        "{diagnostic_intel.failure_state_portfolio}"
                                    </p>
                                )}
                            </div>
                        </div>

                        <div>
                            <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Candidate Antidote Persona</h4>
                            <div className="bg-slate-50 dark:bg-slate-900/30 rounded-xl p-4 border border-slate-100 dark:border-slate-800">
                                <p className="text-sm text-emerald-600 dark:text-emerald-400 font-bold mb-2">
                                    {diagnostic_intel.composite_antidote_persona}
                                </p>
                                {typeof diagnostic_intel.experience_anchoring === 'object' ? (
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-bold text-slate-400 uppercase">Anchor Role:</span>
                                            <span className="text-xs font-bold text-slate-700 dark:text-slate-300">{(diagnostic_intel.experience_anchoring as any).anchor_role_title}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-bold text-slate-400 uppercase">Alignment:</span>
                                            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">{(diagnostic_intel.experience_anchoring as any).alignment_type}</span>
                                        </div>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 italic leading-relaxed pt-1 border-t border-slate-100 dark:border-white/5">
                                            {(diagnostic_intel.experience_anchoring as any).fidelity_logic}
                                        </p>
                                    </div>
                                ) : (
                                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic">
                                        {diagnostic_intel.experience_anchoring}
                                    </p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-100 dark:border-slate-700/50">
                            <div className="col-span-2">
                                <h4 className="text-[10px] font-bold text-slate-400 uppercase mb-2">Mandate Quadrant</h4>
                                {typeof diagnostic_intel.mandate_quadrant === 'object' ? (
                                    <div className="grid grid-cols-2 gap-2">
                                        {Object.entries(diagnostic_intel.mandate_quadrant).map(([key, value]) => (
                                            <div key={key} className="p-2 bg-slate-50 dark:bg-slate-900/40 rounded-lg border border-slate-100 dark:border-slate-800">
                                                <div className="text-[9px] font-bold text-blue-600 dark:text-blue-400 uppercase mb-1">{key}</div>
                                                <div className="text-[10px] text-slate-600 dark:text-slate-400 leading-tight">{value as string}</div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <span className="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-[10px] font-bold rounded border border-blue-100 dark:border-blue-900/30 uppercase">
                                        {diagnostic_intel.mandate_quadrant}
                                    </span>
                                )}
                            </div>
                            <div>
                                <h4 className="text-[10px] font-bold text-slate-400 uppercase mb-1">Functional Gravity</h4>
                                <div className="flex flex-wrap gap-1">
                                    {diagnostic_intel.functional_gravity_stack.map((func, i) => (
                                        <span key={i} className="text-[10px] font-medium text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700/50 px-1.5 py-0.5 rounded">
                                            {func}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Strategic Friction Hooks</h4>
                            <div className="space-y-2">
                                {diagnostic_intel.strategic_friction_hooks.map((hook, i) => (
                                    <div key={i} className="flex gap-3 text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                                        <div className="h-5 w-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 font-bold text-[10px]">
                                            {i + 1}
                                        </div>
                                        <p className="leading-relaxed">{hook}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Logic Gates, Content Intel, Requirements */}
                <div className="space-y-10">
                    {/* 2. Economic Logic Gates */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2">
                            <ChartBarIcon className="h-5 w-5 text-emerald-500" />
                            <h3 className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-widest text-xs">Economic Logic Gates</h3>
                        </div>
                        <div className="bg-emerald-50/30 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/20 rounded-2xl p-6">
                            <h4 className="text-xs font-bold text-emerald-600/70 dark:text-emerald-400/70 uppercase mb-2">Primary Value Driver</h4>
                            <p className="text-base font-bold text-slate-900 dark:text-white mb-4">
                                {economic_logic_gates.primary_value_driver}
                            </p>
                            <h4 className="text-[10px] font-bold text-emerald-600/70 dark:text-emerald-400/70 uppercase mb-2">Metric Hierarchy</h4>
                            <div className="flex flex-wrap gap-2">
                                {economic_logic_gates.metric_hierarchy.map((metric, i) => (
                                    <span key={i} className="px-2 py-1 bg-white dark:bg-slate-800 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold rounded-lg shadow-sm">
                                        {metric}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* 3. Content Intelligence */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2">
                            <ChatBubbleBottomCenterTextIcon className="h-5 w-5 text-purple-500" />
                            <h3 className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-widest text-xs">Content Intelligence</h3>
                        </div>
                        <div className="bg-purple-50/30 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/20 rounded-2xl p-6 space-y-4">
                            <div>
                                <h4 className="text-xs font-bold text-purple-600/70 dark:text-purple-400/70 uppercase mb-2">Vocabulary Mirror</h4>
                                <div className="flex flex-wrap gap-1.5">
                                    {content_intelligence.vocabulary_mirror.map((word, i) => (
                                        <span key={i} className="text-[10px] font-medium text-purple-700 dark:text-purple-300 bg-purple-100/50 dark:bg-purple-900/30 px-2 py-0.5 rounded-full border border-purple-200/50 dark:border-purple-800/50">
                                            {word}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h4 className="text-xs font-bold text-purple-600/70 dark:text-purple-400/70 uppercase mb-2">Must-Have Tech Signals</h4>
                                <div className="flex flex-wrap gap-1.5">
                                    {content_intelligence.must_have_tech_signals.map((signal, i) => (
                                        <span key={i} className="text-[10px] font-bold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-1 rounded shadow-sm border border-slate-200 dark:border-slate-700">
                                            {signal}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 4. Assumed Requirements */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2">
                            <CheckCircleIcon className="h-5 w-5 text-indigo-500" />
                            <h3 className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-widest text-xs">Assumed Requirements</h3>
                        </div>
                        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6">
                            <ul className="space-y-3">
                                {assumed_requirements.map((req, i) => (
                                    <li key={i} className="flex gap-3 text-xs text-slate-600 dark:text-slate-400">
                                        <CheckCircleIcon className="h-4 w-4 text-emerald-500 shrink-0" />
                                        <span>{req}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
