import React from 'react';
import type { WidgetProps } from '../types';
import { formatTimestamp, linesToList, listToLines } from '../utils';
import type { JobCheatSheetData } from '../types';

const SectionField = ({
    label,
    value,
}: {
    label: string;
    value?: string | string[];
}) => {
    if (!value || (Array.isArray(value) && value.length === 0)) {
        return null;
    }
    const rendered = Array.isArray(value) ? value.join(', ') : value;
    if (!rendered) {
        return null;
    }
    return (
        <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{rendered}</p>
        </div>
    );
};

export const JobCheatSheetWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
}: WidgetProps<JobCheatSheetData>) => {
    const handleUpdate = (field: keyof JobCheatSheetData, value: string, asList = false) => {
        const next: JobCheatSheetData = {
            ...data,
            [field]: asList ? linesToList(value) : value,
        } as JobCheatSheetData;
        onChange(next);
    };

    if (!editable || mode === 'live') {
        return (
            <div className="space-y-3">
                <SectionField label="Core Problem" value={data.coreProblem} />
                <SectionField label="Suggested Positioning" value={data.suggestedPositioning} />
                <SectionField label="Success Metrics" value={data.keySuccessMetrics} />
                <SectionField label="Role Levers" value={data.roleLevers} />
                <SectionField label="Potential Blockers" value={data.potentialBlockers} />
                <SectionField label="Business Context" value={data.businessContext} />
                <SectionField label="Strategic Importance" value={data.strategicImportance} />
                <SectionField label="Focus Tags" value={data.focusTags} />
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Core Problem</label>
                <textarea
                    value={data.coreProblem}
                    onChange={(event) => handleUpdate('coreProblem', event.target.value)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Suggested Positioning</label>
                <textarea
                    value={data.suggestedPositioning}
                    onChange={(event) => handleUpdate('suggestedPositioning', event.target.value)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Key Success Metrics</label>
                <textarea
                    value={listToLines(data.keySuccessMetrics)}
                    onChange={(event) => handleUpdate('keySuccessMetrics', event.target.value, true)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-mono text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    placeholder="One metric per line"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Role Levers</label>
                <textarea
                    value={listToLines(data.roleLevers)}
                    onChange={(event) => handleUpdate('roleLevers', event.target.value, true)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-mono text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    placeholder="One lever per line"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Potential Blockers</label>
                <textarea
                    value={listToLines(data.potentialBlockers)}
                    onChange={(event) => handleUpdate('potentialBlockers', event.target.value, true)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-mono text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    placeholder="One blocker per line"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Business Context</label>
                <textarea
                    value={data.businessContext}
                    onChange={(event) => handleUpdate('businessContext', event.target.value)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Strategic Importance</label>
                <textarea
                    value={data.strategicImportance}
                    onChange={(event) => handleUpdate('strategicImportance', event.target.value)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Focus Tags</label>
                <textarea
                    value={listToLines(data.focusTags)}
                    onChange={(event) => handleUpdate('focusTags', event.target.value, true)}
                    rows={3}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-mono text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    placeholder="One tag per line"
                />
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default JobCheatSheetWidget;
