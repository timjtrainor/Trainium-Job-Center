import React from 'react';
import type { WidgetProps } from '../../../../types';
import type { TopOfMindData } from '../../../../types';
import { formatTimestamp } from '../utils';

export const TopOfMindWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
}: WidgetProps<TopOfMindData>) => {
    if (!editable || mode === 'live') {
        return (
            <div className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                <p>
                    <strong>Interviewing with:</strong> {data.interviewerName || 'TBD'}
                </p>
                <p>
                    <strong>Format:</strong> {data.interviewFormat}
                </p>
                <p className="pt-2 text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Interviewer</label>
                <input
                    type="text"
                    value={data.interviewerName || ''}
                    onChange={(event) => onChange({ ...data, interviewerName: event.target.value })}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    placeholder="Name of the interviewer"
                />
            </div>
            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Format</label>
                <input
                    type="text"
                    value={data.interviewFormat}
                    onChange={(event) => onChange({ ...data, interviewFormat: event.target.value })}
                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default TopOfMindWidget;
