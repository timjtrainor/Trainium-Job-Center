import React from 'react';
import { StrategicNarrative } from '../types';
import { ChevronUpDownIcon } from './IconComponents';

interface GlobalNarrativeSwitcherProps {
    narratives: StrategicNarrative[];
    activeNarrativeId: string | null;
    onSetNarrative: (id: string | null) => void;
}

export const GlobalNarrativeSwitcher = ({ narratives, activeNarrativeId, onSetNarrative }: GlobalNarrativeSwitcherProps) => {
    if (narratives.length === 0) {
        return null;
    }

    return (
        <div className="px-2 py-4">
            <label htmlFor="narrative-select" className="px-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Active Narrative
            </label>
            <div className="relative mt-1">
                <select
                    id="narrative-select"
                    value={activeNarrativeId || ''}
                    onChange={(e) => onSetNarrative(e.target.value)}
                    className="w-full appearance-none rounded-md border border-slate-300 bg-white py-2 pl-3 pr-10 text-base text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white sm:text-sm"
                >
                    {narratives.map(n => (
                        <option key={n.narrative_id} value={n.narrative_id}>{n.narrative_name}</option>
                    ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                    <ChevronUpDownIcon className="h-5 w-5" />
                </div>
            </div>
        </div>
    );
};
