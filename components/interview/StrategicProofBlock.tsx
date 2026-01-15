import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as Icons from '../IconComponents';
import { LensStrategy } from '../../types';

interface StrategicProofBlockProps {
    strategy: LensStrategy;
    colorCode?: string; // e.g., 'blue', 'green', 'indigo'
    isActive?: boolean;
    onClick?: () => void;
    isAlwaysExpanded?: boolean;
}

const colorMap: Record<string, { border: string; bg: string; text: string; lightBg: string }> = {
    blue: {
        border: 'border-blue-600',
        bg: 'bg-blue-600',
        text: 'text-blue-600',
        lightBg: 'bg-blue-50',
    },
    green: {
        border: 'border-emerald-600',
        bg: 'bg-emerald-600',
        text: 'text-emerald-600',
        lightBg: 'bg-emerald-50',
    },
    indigo: {
        border: 'border-indigo-600',
        bg: 'bg-indigo-600',
        text: 'text-indigo-600',
        lightBg: 'bg-indigo-50',
    },
    purple: {
        border: 'border-purple-600',
        bg: 'bg-purple-600',
        text: 'text-purple-600',
        lightBg: 'bg-purple-50',
    },
    orange: {
        border: 'border-orange-600',
        bg: 'bg-orange-600',
        text: 'text-orange-600',
        lightBg: 'bg-orange-50',
    },
};

export const StrategicProofBlock: React.FC<StrategicProofBlockProps> = ({
    strategy,
    colorCode = 'blue',
    isActive = true,
    onClick,
    isAlwaysExpanded = false,
}) => {
    const [isExpanded, setIsExpanded] = React.useState(isAlwaysExpanded);
    const colors = colorMap[colorCode] || colorMap.blue;

    // Dynamic Icon selection
    const StrategyIcon = (Icons as any)[strategy.icon_name] || Icons.StrategyIcon;
    const ContextIcon = strategy.context_icon_name ? (Icons as any)[strategy.context_icon_name] : null;

    return (
        <motion.div
            layout
            initial={{ opacity: 1 }}
            animate={{
                opacity: isActive ? 1 : 0.6,
                scale: isActive ? 1 : 0.99,
            }}
            transition={{ duration: 0.2 }}
            className={`relative flex flex-col w-full overflow-hidden rounded-2xl bg-white shadow-md transition-all ${isActive ? 'shadow-xl ring-2 ring-slate-100' : 'cursor-pointer hover:opacity-100'} border-t-8 ${colors.border}`}
            onClick={onClick}
        >
            {/* Top Bar: Hero Signal */}
            <div className={`p-8 ${colors.lightBg} border-b border-slate-100`}>
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                    <div className="flex items-start space-x-6">
                        <div className={`${colors.text} bg-white p-3 rounded-2xl shadow-sm border border-slate-100 flex-shrink-0`}>
                            <StrategyIcon className="h-10 w-10" />
                        </div>
                        <div className="space-y-4">
                            <h3 className="text-2xl font-black tracking-tighter text-slate-900 uppercase leading-[1.1] max-w-xl">
                                {strategy.strategy_name}
                            </h3>

                            {/* Framework Hint Badge - High Legibility */}
                            {(() => {
                                const framework = strategy.framework || 'STAR';
                                const hints: Record<string, string> = {
                                    'STAR': 'Situation, Task, Action, Result',
                                    'PAR': 'Problem, Action, Result',
                                    'DIGS': 'Dramatize, Indicate, Go, Synergize',
                                    'SCQA': 'Situation, Complication, Question, Answer',
                                    'SPI': 'Situation, Problem, Implication'
                                };
                                return (
                                    <div className="inline-flex items-center px-4 py-1.5 bg-white/60 border border-slate-200 rounded-xl shadow-sm">
                                        <span className="text-xs font-black text-blue-600 mr-3 uppercase tracking-widest">{framework}</span>
                                        <div className="w-px h-3 bg-slate-300 mr-3" />
                                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">{hints[framework]}</span>
                                    </div>
                                );
                            })()}

                            {ContextIcon && (
                                <div className="flex items-center text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] pt-1 opacity-60">
                                    <ContextIcon className="h-3 w-3 mr-1.5" />
                                    <span>RELEVANT CONTEXT</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Hero KPI - Integrated Flex */}
                    {strategy.hero_kpi && (
                        <div className="text-right flex-shrink-0">
                            <div className={`text-4xl font-black leading-none ${colors.text} tracking-tighter drop-shadow-md`}>
                                {strategy.hero_kpi}
                            </div>
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Impact Signal</div>
                        </div>
                    )}
                </div>
            </div>

            {/* Content Area: The Signal (Always Visible) */}
            <div className="p-8 bg-white/40">
                <div className="space-y-4">
                    {/* Ensure we always show up to 6 bullets for a consistent look */}
                    {[...Array(6)].map((_, index) => {
                        const point = strategy.talking_points[index];
                        if (!point && strategy.talking_points.length > 0) return null; // Only show empty slots if we have NO points, otherwise just show what exists

                        let phase = '';
                        const framework = strategy.framework || 'STAR';
                        const phases: Record<string, string[]> = {
                            'STAR': ['S', 'T', 'A', 'R'],
                            'PAR': ['P', 'A', 'R'],
                            'DIGS': ['D', 'I', 'G', 'S'],
                            'SPI': ['S', 'P', 'I'],
                            'SCQA': ['S', 'C', 'Q', 'A']
                        };

                        // Map index to phase label
                        phase = phases[framework]?.[index] || '';

                        return (
                            <div
                                key={index}
                                className={`flex items-start ${!point ? 'opacity-30' : 'opacity-100'} transition-opacity`}
                            >
                                <div className={`mt-2.5 mr-4 h-2 w-2 rounded-full ${colors.bg} flex-shrink-0 shadow-sm`} />
                                <span
                                    className="text-xl leading-tight text-slate-800 font-bold tracking-tight py-0.5"
                                    style={{ fontFamily: '"Atkinson Hyperlegible", sans-serif' }}
                                >
                                    {point || '...'}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Expansion Toggle */}
                {strategy.narrative_steps && (
                    <div className="mt-8 border-t border-slate-100 pt-6">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsExpanded(!isExpanded);
                            }}
                            className="flex items-center text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-blue-600 transition-colors bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100"
                        >
                            <Icons.ChevronDownIcon className={`h-4 w-4 mr-2 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                            {isExpanded ? 'Minimize Depth' : 'Full Narrative Depth'}
                        </button>

                        <AnimatePresence>
                            {isExpanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="pt-8 space-y-6">
                                        {(() => {
                                            const FRAMEWORK_STEPS: Record<string, string[]> = {
                                                'STAR': ['Situation', 'Task', 'Action', 'Result'],
                                                'DIGS': ['Dramatize', 'Indicate', 'Go', 'Synergize'],
                                                'PAR': ['Problem', 'Action', 'Result'],
                                                'SCQA': ['Situation', 'Complication', 'Question', 'Answer']
                                            };
                                            const format = strategy.framework || 'STAR';
                                            const order = FRAMEWORK_STEPS[format] || [];

                                            return order.map((label) => {
                                                const keys = Object.keys(strategy.narrative_steps!);
                                                const matchKey = keys.find(k =>
                                                    k.toLowerCase() === label.toLowerCase() ||
                                                    k.toLowerCase().includes(label.toLowerCase())
                                                );

                                                const value = matchKey ? strategy.narrative_steps![matchKey] : null;
                                                if (!value) return null;

                                                return (
                                                    <div key={label} className="border-l-4 border-slate-100 pl-6 py-2">
                                                        <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-1.5">{label}</span>
                                                        <p className="text-lg text-slate-600 leading-relaxed font-serif italic">{value}</p>
                                                    </div>
                                                );
                                            });
                                        })()}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}
            </div>
        </motion.div>
    );
};
