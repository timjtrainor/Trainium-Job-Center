import React from 'react';
import type { WidgetProps } from '../types';
import type { ClarifyingPromptData } from '../types';
import { formatTimestamp } from '../utils';
import { SparklesIcon } from '../../IconComponents';

export const ClarifyingPromptWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
    context,
}: WidgetProps<ClarifyingPromptData>) => {
    const handleSendToNotes = () => {
        if (data.prompt && context.appendToNotes) {
            context.appendToNotes(data.prompt);
        }
    };

    if (!editable || mode === 'live') {
        return (
            <div className="space-y-3">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs font-mono text-slate-700 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-200">
                    {data.prompt || 'Draft clarifying prompts in prep mode to launch them quickly during the interview.'}
                </div>
                {data.prompt && (
                    <button
                        type="button"
                        onClick={handleSendToNotes}
                        className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
                    >
                        <SparklesIcon className="h-4 w-4" />
                        Send to Notes
                    </button>
                )}
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <textarea
                value={data.prompt}
                onChange={(event) => onChange({ ...data, prompt: event.target.value })}
                rows={6}
                className="w-full rounded-md border border-slate-300 bg-white p-3 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                placeholder="Draft clarifying prompts to keep at your fingertips during the conversation."
            />
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default ClarifyingPromptWidget;
