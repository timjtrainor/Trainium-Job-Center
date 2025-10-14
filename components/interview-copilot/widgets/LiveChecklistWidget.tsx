import React from 'react';
import type { WidgetProps } from '../types';
import type { LiveChecklistData } from '../types';
import { formatTimestamp } from '../utils';
import { CheckIcon } from '../../IconComponents';

const ToggleList = ({
    label,
    items,
    covered,
    onToggle,
}: {
    label: string;
    items: string[];
    covered: string[];
    onToggle: (item: string) => void;
}) => (
    <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</h4>
        <ul className="mt-1 space-y-1">
            {items.map((item, index) => {
                const isCovered = covered.includes(item);
                return (
                    <li key={`${label}-${index}`}>
                        <button
                            type="button"
                            onClick={() => onToggle(item)}
                            className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition ${isCovered ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-200' : 'text-slate-700 hover:bg-slate-200 dark:text-slate-200 dark:hover:bg-slate-700/80'}`}
                        >
                            <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                                <CheckIcon className="h-3 w-3" />
                            </span>
                            <span className={isCovered ? 'line-through' : ''}>{item}</span>
                        </button>
                    </li>
                );
            })}
        </ul>
    </div>
);

export const LiveChecklistWidget = ({
    data,
    onChange,
    lastUpdated,
}: WidgetProps<LiveChecklistData>) => {
    const toggleItem = (category: keyof LiveChecklistData['covered'], value: string) => {
        const existing = new Set(data.covered[category]);
        if (existing.has(value)) {
            existing.delete(value);
        } else {
            existing.add(value);
        }
        onChange({
            ...data,
            covered: {
                ...data.covered,
                [category]: Array.from(existing),
            },
        });
    };

    const totalItems = data.metrics.length + data.levers.length + data.blockers.length;
    const completed = data.covered.metrics.length + data.covered.levers.length + data.covered.blockers.length;
    const coveragePercent = totalItems === 0 ? 0 : Math.round((completed / totalItems) * 100);

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Coverage Progress</p>
                <span className="text-xs text-slate-500 dark:text-slate-400">{coveragePercent}%</span>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <ToggleList
                    label="Success Metrics"
                    items={data.metrics}
                    covered={data.covered.metrics}
                    onToggle={(value) => toggleItem('metrics', value)}
                />
                <ToggleList
                    label="Role Levers"
                    items={data.levers}
                    covered={data.covered.levers}
                    onToggle={(value) => toggleItem('levers', value)}
                />
                <ToggleList
                    label="Potential Blockers"
                    items={data.blockers}
                    covered={data.covered.blockers}
                    onToggle={(value) => toggleItem('blockers', value)}
                />
            </div>
            <button
                type="button"
                onClick={() =>
                    onChange({
                        ...data,
                        covered: { metrics: [], levers: [], blockers: [] },
                    })
                }
                className="inline-flex items-center rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm hover:bg-slate-200 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
                Reset Coverage
            </button>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default LiveChecklistWidget;
