import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { StrategicProofBlock } from './StrategicProofBlock';
import { StrategicNarrative, InterviewLensSetup, TMAYConfig, PersonaDefinition, ImpactStory } from '../../types';
import * as Icons from '../IconComponents';
import { PrintableCheatSheet } from './PrintableCheatSheet';

interface TheWarRoomProps {
    setup: InterviewLensSetup;
    tmay: TMAYConfig;
    persona: PersonaDefinition;
    activeNarrative?: StrategicNarrative | null;
    onExit: () => void;
}

export const TheWarRoom: React.FC<TheWarRoomProps> = ({
    setup,
    tmay,
    persona,
    activeNarrative,
    onExit,
}) => {
    const [activeFocusId, setActiveFocusId] = useState<string | null>(null);
    const [isIdentityCollapsed, setIsIdentityCollapsed] = useState(false);

    const toggleFocus = (id: string) => {
        if (activeFocusId === id) {
            setActiveFocusId(null);
        } else {
            setActiveFocusId(id);
        }
    };

    const handlePrint = () => {
        window.print();
    };

    return (
        <div className="fixed inset-0 z-50 flex flex-col bg-slate-100 font-sans overflow-hidden">
            {/* Header - Minimalist */}
            <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8 print:hidden">
                <div className="flex items-center space-x-3">
                    <Icons.ShieldCheckIcon className="h-6 w-6 text-blue-600" />
                    <h1 className="text-xl font-bold tracking-tight text-slate-900">
                        War Room Mode: <span className="text-blue-600">{persona.buyer_type} Persona</span>
                    </h1>
                </div>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={handlePrint}
                        className="flex items-center space-x-2 text-slate-500 hover:text-slate-800 transition-colors bg-slate-50 px-4 py-2 rounded-lg border border-slate-200"
                    >
                        <Icons.ArrowDownTrayIcon className="h-4 w-4" />
                        <span className="text-xs font-bold uppercase tracking-widest">Print Sheet</span>
                    </button>
                    <button
                        onClick={onExit}
                        className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                        Exit Cockpit
                    </button>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto p-8 print:p-0">
                <div className="max-w-6xl mx-auto space-y-12">

                    {/* Identity Stack Profile - Streamlined unified header */}
                    <section className="bg-slate-900 rounded-3xl shadow-2xl relative overflow-hidden transition-all duration-300">
                        {/* Decorative Background Element */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full -mr-32 -mt-32 blur-3xl pointer-events-none" />

                        {/* Master Collapse Toggle */}
                        <div className="flex items-center justify-between px-8 py-4 border-b border-slate-800/50 relative z-10">
                            <span className="text-blue-400 text-[10px] font-black uppercase tracking-[0.3em]">Identity & Persona Context</span>
                            <button
                                onClick={() => setIsIdentityCollapsed(!isIdentityCollapsed)}
                                className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors"
                            >
                                <span className="text-[10px] font-bold uppercase tracking-widest">{isIdentityCollapsed ? 'Show Profile' : 'Minimize Profile'}</span>
                                <Icons.ChevronDownIcon className={`h-4 w-4 transition-transform ${isIdentityCollapsed ? '' : 'rotate-180'}`} />
                            </button>
                        </div>

                        <AnimatePresence>
                            {!isIdentityCollapsed && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="p-8 relative z-10 space-y-12">
                                        {/* Persona Context - Full Width Top Bar */}
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-slate-800/50">
                                            <div className="md:col-span-1">
                                                <span className="text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] mb-4 block">Interviewer Mandate</span>
                                                <h2 className="text-4xl font-black text-white leading-tight uppercase tracking-tighter">
                                                    {persona.buyer_type}
                                                </h2>
                                            </div>
                                            <div className="md:col-span-1">
                                                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Win Condition</p>
                                                <p className="text-lg font-medium text-slate-200">{persona.win_condition}</p>
                                            </div>
                                            <div className="md:col-span-1">
                                                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Mirroring Style</p>
                                                <div className="flex flex-wrap gap-2">
                                                    <div className="px-3 py-1 bg-slate-800 rounded-full text-blue-400 text-[10px] font-black uppercase tracking-widest border border-blue-900/30">
                                                        {persona.communication_style || 'Analytical'}
                                                    </div>
                                                    {persona.professional_pedigree && (
                                                        <div className="px-3 py-1 bg-slate-800 rounded-full text-emerald-400 text-[10px] font-black uppercase tracking-widest border border-emerald-900/30">
                                                            {persona.professional_pedigree}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Identity TMAY Bullets - Full Visibility Stack */}
                                        <div className="space-y-6">
                                            <span className="text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] mb-4 block text-center">Tell Me About Yourself (Full Script)</span>
                                            <div className="space-y-6">
                                                {[
                                                    { label: 'The Hook', text: tmay.hook },
                                                    { label: 'The Bridge', text: tmay.bridge },
                                                    { label: 'The Pivot', text: tmay.pivot }
                                                ].map((item, index) => (
                                                    <div
                                                        key={index}
                                                        className="bg-slate-800/30 rounded-3xl border border-slate-800 hover:border-blue-500/30 transition-all flex flex-col group p-8"
                                                    >
                                                        <div className="mb-4">
                                                            <span className="text-xs font-black text-blue-500 uppercase tracking-widest">
                                                                {item.label}
                                                            </span>
                                                        </div>
                                                        <p className="text-white text-2xl font-bold leading-relaxed tracking-tight" style={{ fontFamily: '"Atkinson Hyperlegible", sans-serif' }}>
                                                            {item.text}
                                                        </p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </section>

                    {/* Strategic Proof Grid */}
                    <div className="space-y-6 pb-24">
                        <div className="flex items-center justify-between px-2">
                            <h2 className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">Strategic Proof Portfolio (Signal Only)</h2>
                            <div className="h-px flex-1 bg-slate-200 mx-8" />
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {activeNarrative?.impact_stories?.map((story) => {
                                // 1. Find the competency for color coding
                                const comp = setup.active_competencies.find(c =>
                                    c.strategies.some(s => s.strategy_id === story.associated_strategy_id)
                                );

                                // 2. Assemble the strategy object for the display block
                                const mergedStrategy: any = {
                                    strategy_id: story.story_id,
                                    strategy_name: story.story_title,
                                    icon_name: story.visual_anchor || 'StrategyIcon',
                                    hero_kpi: story.hero_kpi,
                                    talking_points: story.thinned_bullets || [],
                                    narrative_steps: story.narrative_steps,
                                    framework: story.format || 'STAR'
                                };

                                return (
                                    <StrategicProofBlock
                                        key={story.story_id}
                                        strategy={mergedStrategy}
                                        colorCode={comp?.color_code}
                                        isActive={activeFocusId === null || activeFocusId === story.story_id}
                                        onClick={() => toggleFocus(story.story_id)}
                                    />
                                );
                            })}
                        </div>
                    </div>
                </div>
            </main>

            <PrintableCheatSheet
                setup={setup}
                tmay={tmay}
                persona={persona}
                activeNarrative={activeNarrative}
            />
        </div >
    );
};
