import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as Icons from '../IconComponents';
import {
    JobApplication, Interview, Company, StrategicNarrative,
    InterviewLensSetup, LensCompetency, LensStrategy,
    TrackCompetencies, Competency, LensNarrativeStyle,
    PersonaDefinition, TMAYConfig, BuyerType, UploadedDocument
} from '../../types';
import * as apiService from '../../services/apiService';
import * as geminiService from '../../services/geminiService';
import { USER_ID } from '../../constants';

interface StrategySetupProps {
    application: JobApplication;
    interview: Interview;
    company: Company;
    activeNarrative: StrategicNarrative;
    onSave: (setup: InterviewLensSetup, persona: PersonaDefinition, tmay: TMAYConfig) => void;
    onLaunchWarRoom: () => void;
}

const AVAILABLE_COLORS = ['blue', 'green', 'indigo', 'purple', 'orange'];
const AVAILABLE_ICONS = [
    'RocketLaunchIcon', 'ShieldCheckIcon', 'BoltIcon', 'PresentationChartLineIcon',
    'CloudArrowUpIcon', 'FlagIcon', 'UsersIcon', 'CurrencyDollarIcon',
    'GlobeAltIcon', 'BeakerIcon', 'CubeIcon', 'SparklesIcon'
];

const BUYER_TYPES: BuyerType[] = ['Recruiter', 'Hiring Manager', 'Technical Buyer', 'Peer', 'Executive'];

export const StrategySetup: React.FC<StrategySetupProps> = ({
    application,
    interview,
    company,
    activeNarrative,
    onSave,
    onLaunchWarRoom,
}) => {
    const [setup, setSetup] = useState<InterviewLensSetup>(
        interview.interview_strategy_state?.lens_setup || {
            active_competencies: [],
            is_locked: false,
            role_id: application.job_title || '',
            objective: 'Win the offer',
            narrative_style: 'STAR',
            experience_company: '',
            experience_role: ''
        }
    );
    const [persona, setPersona] = useState<PersonaDefinition>(
        interview.interview_strategy_state?.persona || {
            buyer_type: 'Hiring Manager',
            primary_anxiety: '',
            win_condition: '',
            functional_friction_point: '',
            interviewer_title: '',
            interviewer_linkedin_about: '',
            mirroring_style: ''
        }
    );
    const [tmay, setTMAY] = useState<TMAYConfig>(
        interview.interview_strategy_state?.tmay || {
            hook: activeNarrative?.positioning_statement || '',
            bridge: '',
            pivot: ''
        }
    );
    const [trackCompetencies, setTrackCompetencies] = useState<TrackCompetencies | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAIUpdating, setIsAIUpdating] = useState(false);
    const [isTMAYUpdating, setIsTMAYUpdating] = useState(false);
    const [isStoryGenerating, setIsStoryGenerating] = useState<Record<string, boolean>>({});
    const [showOverwriteWarning, setShowOverwriteWarning] = useState(false);
    const [availableExperiences, setAvailableExperiences] = useState<UploadedDocument[]>([]);

    // 1. Load competencies based on the application's track
    useEffect(() => {
        const loadCompetencies = async () => {
            setIsLoading(true);
            try {
                const track = application.job?.track || 'General Leadership';
                const data = await apiService.getTrackCompetencies(track);
                setTrackCompetencies(data);
            } catch (err) {
                console.error('Failed to load track competencies:', err);
            } finally {
                setIsLoading(false);
            }
        };
        loadCompetencies();
    }, [application]);

    // 2. Load all available Proof Points from ChromaDB
    useEffect(() => {
        const loadProofPoints = async () => {
            try {
                // Fetch all documents from proof_points collection directly
                const allDocs = await apiService.getCollectionDocuments('proof_points');

                // Group by Company + Role and select only the latest version
                const groups: Record<string, UploadedDocument[]> = {};
                allDocs.forEach(doc => {
                    const company = doc.metadata?.company || 'Unknown Company';
                    const role = doc.metadata?.role_title || doc.title || 'Unknown Role';
                    const key = `${company}|${role}`;
                    if (!groups[key]) groups[key] = [];
                    groups[key].push(doc);
                });

                const latestExperiences = Object.values(groups).map(docs => {
                    // Sort by creation date descending (newest first)
                    return docs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];
                }).sort((a, b) => {
                    // Sort final list by start date if available, else created_at
                    const dateA = a.metadata?.start_date ? new Date(a.metadata.start_date as string).getTime() : new Date(a.created_at).getTime();
                    const dateB = b.metadata?.start_date ? new Date(b.metadata.start_date as string).getTime() : new Date(b.created_at).getTime();
                    return dateB - dateA;
                });

                setAvailableExperiences(latestExperiences);
            } catch (err) {
                console.error('Failed to load proof points:', err);
            }
        };
        loadProofPoints();
    }, []);


    const toggleCompetency = (comp: Competency) => {
        if (setup.is_locked) return;

        const isAlreadyActive = setup.active_competencies.some(c => c.title === comp.title);

        if (isAlreadyActive) {
            setSetup(prev => ({
                ...prev,
                active_competencies: prev.active_competencies.filter(c => c.title !== comp.title)
            }));
        } else {
            if (setup.active_competencies.length >= 3) return;

            const newComp: LensCompetency = {
                competency_id: comp.title,
                title: comp.title,
                color_code: AVAILABLE_COLORS[setup.active_competencies.length % AVAILABLE_COLORS.length],
                strategies: comp.strategies.map((s, idx) => ({
                    strategy_id: `${comp.title}-${idx}`,
                    strategy_name: s.strategy_name,
                    icon_name: 'RocketLaunchIcon',
                    hero_kpi: s.kpis?.[0] || '10X',
                    talking_points: s.talking_points.slice(0, 3).map(p => p.slice(0, 50)),
                }))
            };

            setSetup(prev => ({
                ...prev,
                active_competencies: [...prev.active_competencies, newComp]
            }));
        }
    };

    const updateStrategy = (compId: string, stratId: string, updates: Partial<LensStrategy>) => {
        if (setup.is_locked) return;
        setSetup(prev => ({
            ...prev,
            active_competencies: prev.active_competencies.map(c =>
                c.competency_id === compId
                    ? {
                        ...c,
                        strategies: c.strategies.map(s => s.strategy_id === stratId ? { ...s, ...updates } : s)
                    }
                    : c
            )
        }));
    };

    const removeStrategy = (compId: string, stratId: string) => {
        if (setup.is_locked) return;
        setSetup(prev => ({
            ...prev,
            active_competencies: prev.active_competencies.map(c =>
                c.competency_id === compId
                    ? {
                        ...c,
                        strategies: c.strategies.filter(s => s.strategy_id !== stratId)
                    }
                    : c
            ).filter(c => c.strategies.length > 0) // Remove competency if no strategies left
        }));
    };

    const handleGenerateStoryDraft = async (compId: string, strat: LensStrategy) => {
        if (setup.is_locked) return;
        setIsStoryGenerating(prev => ({ ...prev, [strat.strategy_id]: true }));

        try {
            const sourceDoc = availableExperiences.find(s => s.id === strat.source_story_id);
            const context = {
                strategy: strat.strategy_name,
                strategy_details: strat.talking_points.join(', '),
                story_title: sourceDoc ? `${sourceDoc.metadata?.company || 'Unknown'} - ${sourceDoc.metadata?.title || sourceDoc.title}` : 'The Experience',
                story_body: sourceDoc?.content_snippet || 'No specific story body provided',
                persona_context: `${persona.buyer_type}: ${persona.primary_anxiety}. Win Condition: ${persona.win_condition}`,
                framework: strat.framework || 'STAR'
            };

            const res = await geminiService.generateLensStoryDraft(context, 'GENERATE_LENS_STORY_DRAFT');

            updateStrategy(compId, strat.strategy_id, {
                draft_story: res.draft
            });
        } catch (err) {
            console.error('Failed to generate story draft:', err);
        } finally {
            setIsStoryGenerating(prev => ({ ...prev, [strat.strategy_id]: false }));
        }
    };

    const handleStorySelection = (docId: string) => {
        const doc = availableExperiences.find(d => d.id === docId);
        if (doc) {
            setSetup(prev => ({
                ...prev,
                experience_company: (doc.metadata?.company as string) || '',
                experience_role: (doc.metadata?.role_title as string) || (doc.metadata?.title as string) || doc.title || '',
            }));
        } else {
            setSetup(prev => ({
                ...prev,
                experience_company: '',
                experience_role: '',
            }));
        }
    };

    const handlePersonaChange = (field: keyof PersonaDefinition, value: any) => {
        setPersona(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const updateTMAY = (field: keyof TMAYConfig, value: string) => {
        setTMAY(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleRunAI = async () => {
        setIsAIUpdating(true);
        setShowOverwriteWarning(false);

        try {
            const buyerType = persona.buyer_type;
            const interviewerTitle = persona.interviewer_title || "Interviewer Job Title";
            const interviewerAbout = persona.interviewer_linkedin_about || "Extracted from LinkedIn profile...";
            const jdAnalysis = application.ai_summary || application.job_description.substring(0, 200);
            const alignment = application.why_this_job || "";

            // Consolidate Previous Interview Context
            const previousInterviews = application.interviews || [];
            const previousContext = previousInterviews
                .map(int => {
                    const type = int.interview_type;
                    const date = int.interview_date ? ` on ${int.interview_date}` : '';
                    const notes = int.live_notes || '';
                    const debrief = int.post_interview_debrief ?
                        `Wins: ${int.post_interview_debrief.performance_analysis.wins.join(', ')}. Fumbles: ${int.post_interview_debrief.performance_analysis.areas_for_improvement.join(', ')}` : '';
                    return `[${type}${date}] Notes: ${notes}. ${debrief}`;
                })
                .join('\n---\n');

            const aiResponse = await apiService.generatePersonaDefinition(
                buyerType,
                interviewerTitle,
                interviewerAbout,
                jdAnalysis,
                alignment,
                application.interview_strategy,
                previousContext
            );

            setPersona(prev => ({
                ...prev,
                primary_anxiety: aiResponse.primary_anxiety,
                win_condition: aiResponse.win_condition,
                functional_friction_point: aiResponse.functional_friction_point,
                mirroring_style: aiResponse.mirroring_style
            }));
        } catch (error) {
            console.error(error);
        } finally {
            setIsAIUpdating(false);
        }
    };

    const handleRunAITMAY = async () => {
        setIsTMAYUpdating(true);
        try {
            const alignment = application.why_this_job || JSON.stringify(application.interview_strategy || {});
            const dna = application.resume_summary || "";

            const aiResponse = await apiService.generateTMAY(
                persona.primary_anxiety,
                persona.win_condition,
                persona.functional_friction_point,
                persona.mirroring_style || '',
                alignment,
                dna
            );

            setTMAY({
                hook: aiResponse.hook,
                bridge: aiResponse.bridge,
                pivot: aiResponse.pivot
            });
        } catch (error) {
            console.error(error);
        } finally {
            setIsTMAYUpdating(false);
        }
    };

    const enhanceWithAIClick = () => {
        const { primary_anxiety, win_condition, functional_friction_point, mirroring_style } = persona;
        if (primary_anxiety || win_condition || functional_friction_point || mirroring_style) {
            setShowOverwriteWarning(true);
        } else {
            handleRunAI();
        }
    };

    const handleSave = () => {
        onSave(setup, persona, tmay);
    };

    if (isLoading) {
        return <div className="flex h-64 items-center justify-center"><Icons.LoadingSpinner /></div>;
    }

    return (
        <div className="max-w-6xl mx-auto py-8 px-4 font-sans">
            <div className="mb-8 flex items-end justify-between border-b pb-6">
                <div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Interview Lens Setup</h2>
                    <p className="text-slate-500 mt-1 font-medium text-sm">Architect your leadership narrative through visual association.</p>
                </div>
                <div className="flex space-x-3">
                    <button
                        onClick={handleSave}
                        className="px-6 py-2.5 bg-white border-2 border-slate-200 text-slate-700 font-bold rounded-xl hover:bg-slate-50 transition-all text-sm"
                    >
                        Save Architecture
                    </button>
                    <button
                        onClick={onLaunchWarRoom}
                        disabled={setup.active_competencies.length === 0}
                        className="px-8 py-2.5 bg-blue-600 text-white font-bold rounded-xl shadow-lg shadow-blue-200 hover:bg-blue-700 disabled:opacity-50 disabled:shadow-none transition-all text-sm"
                    >
                        Launch The War Room
                    </button>
                </div>
            </div>

            {/* Identity & Context Stack */}
            <div className="grid grid-cols-12 gap-6 mb-8">
                <div className="col-span-12 md:col-span-6 space-y-4">
                    <div className="p-6 bg-white rounded-2xl border-2 border-slate-100 shadow-sm space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center">
                                <Icons.UserIcon className="h-4 w-4 mr-2" />
                                Persona Definition
                            </h3>
                            <div className="flex items-center space-x-2">
                                <select
                                    value={persona.buyer_type}
                                    onChange={(e) => handlePersonaChange('buyer_type', e.target.value as BuyerType)}
                                    className="text-[10px] font-bold px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full uppercase tracking-tighter border border-indigo-100 outline-none"
                                >
                                    {BUYER_TYPES.map(type => (
                                        <option key={type} value={type}>{type}</option>
                                    ))}
                                </select>
                                <button
                                    onClick={enhanceWithAIClick}
                                    disabled={isAIUpdating}
                                    className="flex items-center space-x-1 text-[10px] font-black text-blue-600 uppercase tracking-widest hover:text-blue-700 disabled:opacity-30"
                                >
                                    {isAIUpdating ? <Icons.LoadingSpinner className="h-3 w-3" /> : <Icons.SparklesIcon className="h-3 w-3" />}
                                    <span>AI Profile</span>
                                </button>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Title</label>
                                    <input
                                        type="text"
                                        value={persona.interviewer_title || ''}
                                        onChange={(e) => handlePersonaChange('interviewer_title', e.target.value)}
                                        className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-2"
                                        placeholder="e.g. VP Engineering"
                                    />
                                </div>
                                <div>
                                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">LinkedIn Bio Snippet</label>
                                    <input
                                        type="text"
                                        value={persona.interviewer_linkedin_about || ''}
                                        onChange={(e) => handlePersonaChange('interviewer_linkedin_about', e.target.value)}
                                        className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-2"
                                        placeholder="Paste extracted text..."
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Primary Anxiety</label>
                                <textarea
                                    value={persona.primary_anxiety}
                                    onChange={(e) => handlePersonaChange('primary_anxiety', e.target.value)}
                                    className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-3 resize-none min-h-[60px]"
                                    placeholder="What prevents them from hiring you?"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Win Condition</label>
                                    <textarea
                                        value={persona.win_condition}
                                        onChange={(e) => handlePersonaChange('win_condition', e.target.value)}
                                        className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-3 resize-none min-h-[60px]"
                                        placeholder="What makes them look like a hero?"
                                    />
                                </div>
                                <div>
                                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Mirroring Style</label>
                                    <textarea
                                        value={persona.mirroring_style || ''}
                                        onChange={(e) => handlePersonaChange('mirroring_style', e.target.value)}
                                        className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-3 resize-none min-h-[60px]"
                                        placeholder="Tone, energy, speed..."
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-span-12 md:col-span-6 space-y-4">
                    <div className="p-6 bg-white rounded-2xl border-2 border-slate-100 shadow-sm space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center">
                                <Icons.MicrophoneIcon className="h-4 w-4 mr-2" />
                                Tell Me About Yourself (TMAY)
                            </h3>
                            <button
                                onClick={handleRunAITMAY}
                                disabled={isTMAYUpdating}
                                className="flex items-center space-x-1 text-[10px] font-black text-blue-600 uppercase tracking-widest hover:text-blue-700 disabled:opacity-30"
                            >
                                {isTMAYUpdating ? <Icons.LoadingSpinner className="h-3 w-3" /> : <Icons.SparklesIcon className="h-3 w-3" />}
                                <span>AI Script</span>
                            </button>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">The Hook (Past)</label>
                                <textarea
                                    value={tmay.hook}
                                    onChange={(e) => updateTMAY('hook', e.target.value)}
                                    className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-3 resize-none min-h-[60px]"
                                    placeholder="Past/Context: Your origin story."
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">The Bridge (Present)</label>
                                    <textarea
                                        value={tmay.bridge}
                                        onChange={(e) => updateTMAY('bridge', e.target.value)}
                                        className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-3 resize-none min-h-[60px]"
                                        placeholder="Present/Success: Your tangible wins."
                                    />
                                </div>
                                <div>
                                    <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block mb-1">The Pivot (Future)</label>
                                    <textarea
                                        value={tmay.pivot || ''}
                                        onChange={(e) => updateTMAY('pivot', e.target.value)}
                                        className="w-full text-xs font-bold text-slate-800 bg-slate-50 border-none focus:ring-1 focus:ring-blue-500 rounded-lg p-3 resize-none min-h-[60px]"
                                        placeholder="Why this company and why now?"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Global Controls - Lock Only */}
            <div className="flex justify-end mb-8">
                <button
                    onClick={() => setSetup(prev => ({ ...prev, is_locked: !prev.is_locked }))}
                    className={`px-4 py-2 rounded-xl font-black uppercase tracking-widest transition-all border-2 text-xs ${setup.is_locked
                        ? 'bg-red-50 border-red-200 text-red-600'
                        : 'bg-slate-50 border-slate-200 text-slate-400'
                        }`}
                >
                    {setup.is_locked ? 'Unlock Strategy' : 'Lock Strategy'}
                </button>
            </div>

            <div className="grid grid-cols-12 gap-8">
                {/* Left Column - Repository */}
                <div className="col-span-4">
                    <section className="bg-white rounded-2xl p-6 border-2 border-slate-100 shadow-sm">
                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-6 flex items-center">
                            <Icons.CircleStackIcon className="h-4 w-4 mr-2" />
                            Competency Repository
                        </h3>

                        <div className="space-y-3">
                            {trackCompetencies?.competencies.map((comp) => {
                                const isActive = setup.active_competencies.some(c => c.title === comp.title);
                                return (
                                    <button
                                        key={comp.title}
                                        disabled={setup.is_locked && !isActive}
                                        onClick={() => toggleCompetency(comp)}
                                        className={`w-full text-left p-4 rounded-xl border-2 transition-all ${isActive
                                            ? 'border-blue-600 bg-blue-50'
                                            : 'border-slate-100 hover:border-slate-200 bg-white'
                                            } ${setup.is_locked && !isActive ? 'opacity-30 cursor-not-allowed' : ''}`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className={`font-bold text-sm ${isActive ? 'text-blue-700' : 'text-slate-700'}`}>
                                                {comp.title}
                                            </span>
                                            {isActive ? (
                                                <Icons.CheckBadgeIcon className="h-5 w-5 text-blue-600" />
                                            ) : (
                                                <Icons.PlusCircleIcon className="h-5 w-5 text-slate-300" />
                                            )}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </section>
                </div>

                {/* Right Column - Active Configuration */}
                <div className="col-span-8 space-y-6">
                    <AnimatePresence>
                        {setup.active_competencies.map((comp) => (
                            <motion.div
                                key={comp.competency_id}
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className={`bg-white rounded-2xl border-l-8 overflow-hidden border-2 border-slate-100 shadow-sm ${comp.color_code === 'blue' ? 'border-l-blue-600' :
                                    comp.color_code === 'green' ? 'border-l-emerald-600' :
                                        comp.color_code === 'indigo' ? 'border-l-indigo-600' :
                                            comp.color_code === 'purple' ? 'border-l-purple-600' :
                                                'border-l-orange-600'
                                    }`}
                            >
                                <div className="p-6 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                                    <h4 className="text-xl font-black text-slate-800 uppercase tracking-tight">{comp.title}</h4>
                                    <button
                                        onClick={() => toggleCompetency({ title: comp.title } as any)}
                                        disabled={setup.is_locked}
                                        className="text-slate-300 hover:text-red-500 transition-colors disabled:opacity-0"
                                    >
                                        <Icons.TrashIcon className="h-5 w-5" />
                                    </button>
                                </div>

                                <div className="p-6 space-y-8">
                                    {comp.strategies.map((strat) => {
                                        const StrategyIcon = (Icons as any)[strat.icon_name] || Icons.StrategyIcon;
                                        return (
                                            <div key={strat.strategy_id} className="grid grid-cols-12 gap-6 pb-6 border-b border-slate-100 last:border-b-0 last:pb-0">
                                                <div className="col-span-3 flex flex-col items-center">
                                                    <div className="h-16 w-16 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-600 mb-2 relative group cursor-pointer">
                                                        <StrategyIcon className="h-10 w-10" />
                                                    </div>
                                                    <select
                                                        value={strat.icon_name}
                                                        disabled={setup.is_locked}
                                                        onChange={(e) => updateStrategy(comp.competency_id, strat.strategy_id, { icon_name: e.target.value })}
                                                        className="text-[10px] uppercase font-black tracking-widest text-slate-400 bg-transparent border-none focus:ring-0 p-0 text-center cursor-pointer disabled:cursor-not-allowed"
                                                    >
                                                        {AVAILABLE_ICONS.map(icon => (
                                                            <option key={icon} value={icon}>{icon.replace('Icon', '')}</option>
                                                        ))}
                                                    </select>

                                                    <button
                                                        disabled={setup.is_locked}
                                                        onClick={async () => {
                                                            try {
                                                                const res = await geminiService.synthesizeLensTalkingPoints({
                                                                    role: setup.role_id,
                                                                    objective: setup.objective,
                                                                    framework: strat.framework || 'STAR',
                                                                    competency: comp.title,
                                                                    strategy: strat.strategy_name,
                                                                    proof_points: availableExperiences.map(doc => `${doc.metadata?.company || ''} - ${doc.metadata?.title || doc.title}`)
                                                                }, 'SYNTHESIZE_LENS_STRATEGY');
                                                                updateStrategy(comp.competency_id, strat.strategy_id, {
                                                                    hero_kpi: res.hero_kpi,
                                                                    talking_points: res.talking_points
                                                                });
                                                            } catch (err) { console.error(err); }
                                                        }}
                                                        className="mt-4 flex items-center space-x-1 text-[10px] font-black uppercase tracking-widest text-blue-600 hover:text-blue-700 disabled:opacity-30"
                                                    >
                                                        <Icons.SparklesIcon className="h-3 w-3" />
                                                        <span>Synthesize Points</span>
                                                    </button>

                                                    <div className="mt-6 pt-4 border-t border-slate-100 flex flex-col items-center space-y-3">
                                                        <div className="w-full">
                                                            <label className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2 block">Framework</label>
                                                            <select
                                                                value={strat.framework || 'STAR'}
                                                                disabled={setup.is_locked}
                                                                onChange={(e) => updateStrategy(comp.competency_id, strat.strategy_id, { framework: e.target.value as LensNarrativeStyle })}
                                                                className="w-full text-[10px] font-bold text-slate-600 bg-white border border-slate-200 rounded-lg px-2 py-1 outline-none"
                                                            >
                                                                <option value="STAR">STAR</option>
                                                                <option value="PAR">PAR</option>
                                                                <option value="DIGS">DIGS</option>
                                                                <option value="SPI">SPI</option>
                                                            </select>
                                                        </div>

                                                        <div className="w-full">
                                                            <label className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2 block">Base Story</label>
                                                            <select
                                                                value={strat.source_story_id || ''}
                                                                disabled={setup.is_locked}
                                                                onChange={(e) => updateStrategy(comp.competency_id, strat.strategy_id, { source_story_id: e.target.value })}
                                                                className="w-full text-[10px] font-bold text-slate-600 bg-white border border-slate-200 rounded-lg px-2 py-1 outline-none"
                                                            >
                                                                <option value="">Select source...</option>
                                                                {availableExperiences.map(doc => (
                                                                    <option key={doc.id} value={doc.id}>
                                                                        {doc.metadata?.company || 'Unknown'} - {doc.metadata?.title || doc.title}
                                                                    </option>
                                                                ))}
                                                            </select>
                                                        </div>

                                                        <button
                                                            disabled={setup.is_locked || !strat.source_story_id || isStoryGenerating[strat.strategy_id]}
                                                            onClick={() => handleGenerateStoryDraft(comp.competency_id, strat)}
                                                            className={`mt-3 w-full flex items-center justify-center space-x-1 text-[10px] font-black uppercase tracking-widest px-3 py-2 rounded-lg transition-all ${strat.draft_story
                                                                ? 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                                                                : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                                                                } disabled:opacity-30`}
                                                        >
                                                            {isStoryGenerating[strat.strategy_id] ? (
                                                                <Icons.LoadingSpinner className="h-3 w-3" />
                                                            ) : (
                                                                <Icons.SparklesIcon className="h-3 w-3" />
                                                            )}
                                                            <span>{strat.draft_story ? 'Regen' : 'Draft Story'}</span>
                                                        </button>
                                                    </div>
                                                </div>

                                                <div className="col-span-9 space-y-4 relative group">
                                                    {!setup.is_locked && (
                                                        <button
                                                            onClick={() => removeStrategy(comp.competency_id, strat.strategy_id)}
                                                            className="absolute top-0 right-0 p-1 text-slate-200 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                                                            title="Remove Strategy"
                                                        >
                                                            <Icons.TrashIcon className="h-4 w-4" />
                                                        </button>
                                                    )}
                                                    <div>
                                                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">Strategy & Hero KPI</label>
                                                        <div className="flex items-center space-x-4">
                                                            <input
                                                                type="text"
                                                                value={strat.strategy_name}
                                                                disabled={setup.is_locked}
                                                                onChange={(e) => updateStrategy(comp.competency_id, strat.strategy_id, { strategy_name: e.target.value })}
                                                                className="flex-1 text-lg font-bold text-slate-800 bg-transparent border-b-2 border-transparent focus:border-blue-600 outline-none disabled:opacity-50"
                                                            />
                                                            <input
                                                                type="text"
                                                                value={strat.hero_kpi}
                                                                disabled={setup.is_locked}
                                                                onChange={(e) => updateStrategy(comp.competency_id, strat.strategy_id, { hero_kpi: e.target.value })}
                                                                className="w-24 text-xl font-black text-blue-600 text-right bg-transparent border-b-2 border-transparent focus:border-blue-600 outline-none disabled:opacity-50"
                                                            />
                                                        </div>
                                                    </div>
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">Talking Points (7-word limit)</label>
                                                        {strat.talking_points.map((point, pIdx) => (
                                                            <div key={pIdx} className="flex items-center space-x-2 group">
                                                                <div className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${comp.color_code === 'blue' ? 'bg-blue-600' : 'bg-slate-400'}`} />
                                                                <input
                                                                    type="text"
                                                                    value={point}
                                                                    disabled={setup.is_locked}
                                                                    onChange={(e) => {
                                                                        const pts = [...strat.talking_points];
                                                                        pts[pIdx] = e.target.value;
                                                                        updateStrategy(comp.competency_id, strat.strategy_id, { talking_points: pts });
                                                                    }}
                                                                    className={`flex-1 text-sm font-medium text-slate-600 bg-transparent border-b border-slate-100 focus:border-slate-300 outline-none disabled:opacity-50 ${point.split(/\s+/).length > 7 ? 'text-red-500' : ''}`}
                                                                />
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {strat.draft_story && (
                                                        <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-100 relative group/story">
                                                            <div className="flex items-center justify-between mb-2">
                                                                <span className="text-[9px] font-black uppercase tracking-[0.2em] text-emerald-600 flex items-center">
                                                                    <Icons.CheckBadgeIcon className="h-3 w-3 mr-1" />
                                                                    Story Defined
                                                                </span>
                                                            </div>
                                                            <textarea
                                                                value={strat.draft_story}
                                                                disabled={setup.is_locked}
                                                                onChange={(e) => updateStrategy(comp.competency_id, strat.strategy_id, { draft_story: e.target.value })}
                                                                className="w-full text-xs font-medium text-slate-700 bg-transparent border-none focus:ring-0 p-0 resize-none min-h-[100px] leading-relaxed"
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {setup.active_competencies.length === 0 && (
                        <div className="h-64 rounded-2xl border-4 border-dashed border-slate-100 flex flex-col items-center justify-center text-slate-300">
                            <Icons.SparklesIcon className="h-12 w-12 mb-2 opacity-20" />
                            <p className="font-bold">Select competencies to begin setup</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Warning Modal */}
            <AnimatePresence>
                {showOverwriteWarning && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-slate-100"
                        >
                            <div className="h-12 w-12 bg-amber-50 rounded-2xl flex items-center justify-center mb-6">
                                <Icons.SparklesIcon className="h-6 w-6 text-amber-600" />
                            </div>
                            <h3 className="text-xl font-black text-slate-900 mb-2">Overwrite Existing Data?</h3>
                            <p className="text-slate-500 font-medium text-sm mb-8 leading-relaxed">
                                Running AI analysis will verify and potentially replace your current Anxiety, Win Condition, and Friction Point definitions.
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowOverwriteWarning(false)}
                                    className="flex-1 px-4 py-3 text-sm font-bold text-slate-500 hover:text-slate-700 bg-slate-50 rounded-xl transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleRunAI}
                                    className="flex-1 px-4 py-3 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all"
                                >
                                    Overwrite & Update
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
