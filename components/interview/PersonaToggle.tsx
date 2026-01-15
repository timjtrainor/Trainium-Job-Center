import React, { useState } from 'react';
import { PersonaGuidance } from '../../types';
import {
    UserGroupIcon,
    LightBulbIcon,
    SpeakerWaveIcon,
    ExclamationTriangleIcon,
    ChatBubbleBottomCenterTextIcon
} from '@heroicons/react/24/outline';

interface PersonaToggleProps {
    guidanceMap: Record<string, PersonaGuidance>;
    activePersona: string;
    onToggle: (persona: string) => void;
}

const PERSONA_ICONS: Record<string, any> = {
    'Talent Sifter': UserGroupIcon,
    'The Owner': LightBulbIcon,
    'Deep Diver': ChatBubbleBottomCenterTextIcon,
    'Visionary': SpeakerWaveIcon,
};

const PERSONA_LABELS: Record<string, string> = {
    'Talent Sifter': 'Recruiter / HR',
    'The Owner': 'Hiring Manager',
    'Deep Diver': 'Peer / Technical',
    'Visionary': 'Executive / Founder',
};


export const PersonaToggle: React.FC<PersonaToggleProps> = ({ guidanceMap, activePersona, onToggle }) => {
    if (!guidanceMap) return null;
    // Ensure we have a valid active persona, or default to the first available
    const availablePersonas = Object.keys(guidanceMap);
    const currentPersona = activePersona || availablePersonas[0];
    const guidance = guidanceMap[currentPersona];

    if (!guidance) return null;

    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
            {/* Toggle Header */}
            <div className="flex border-b border-slate-200 dark:border-slate-700 overflow-x-auto">
                {availablePersonas.map((persona) => {
                    const Icon = PERSONA_ICONS[persona] || UserGroupIcon;
                    const isActive = currentPersona === persona;
                    return (
                        <button
                            key={persona}
                            onClick={() => onToggle(persona)}
                            className={`flex items-center gap-2 px-6 py-4 text-sm font-semibold whitespace-nowrap transition-colors border-b-2 ${isActive
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10'
                                : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                                }`}
                        >
                            <Icon className="h-4 w-4" />
                            {PERSONA_LABELS[persona] || persona}
                        </button>
                    );
                })}
            </div>

            {/* Content Area */}
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left Column: Focus & Metrics */}
                <div className="space-y-6">
                    <div>
                        <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                            <LightBulbIcon className="h-4 w-4" /> Primary Focus
                        </h4>
                        <div className="p-4 bg-amber-50 dark:bg-amber-900/10 rounded-xl border border-amber-100 dark:border-amber-900/20 text-slate-800 dark:text-slate-200 text-sm font-medium leading-relaxed">
                            {guidance.focus_area}
                        </div>
                    </div>

                    <div>
                        <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                            <ChatBubbleBottomCenterTextIcon className="h-4 w-4" /> Success Metric
                        </h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400 italic">
                            "{guidance.success_metric}"
                        </p>
                    </div>

                    {guidance.anti_persona_warning && (
                        <div className="p-4 bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-100 dark:border-red-900/20">
                            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400 mb-2">
                                <ExclamationTriangleIcon className="h-4 w-4" /> Anti-Persona Warning
                            </h4>
                            <p className="text-sm text-red-800 dark:text-red-200 leading-relaxed">
                                {guidance.anti_persona_warning}
                            </p>
                        </div>
                    )}
                </div>

                {/* Right Column: Vocabulary & Questions */}
                <div className="space-y-6">
                    <div>
                        <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                            <SpeakerWaveIcon className="h-4 w-4" /> Vocabulary Mirror
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {guidance.vocabulary_mirror.map((word, i) => (
                                <span key={i} className="px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600">
                                    "{word}"
                                </span>
                            ))}
                        </div>
                    </div>

                    <div>
                        <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                            <ChatBubbleBottomCenterTextIcon className="h-4 w-4" /> Consultative Questions
                        </h4>
                        <ul className="space-y-3">
                            {guidance.consultative_questions.map((q, i) => (
                                <li key={i} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
                                    <span className="font-bold text-blue-500 select-none">{i + 1}.</span>
                                    {q}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
