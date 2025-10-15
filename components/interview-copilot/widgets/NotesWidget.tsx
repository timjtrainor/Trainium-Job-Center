import React from 'react';
import type { WidgetProps } from '../types';
import type { NotesData } from '../types';
import { formatTimestamp } from '../utils';

export const NotesWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
}: WidgetProps<NotesData>) => {
    if (!editable) {
        return (
            <div className="space-y-2">
                <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{data.content || 'Notes captured during the conversation will appear here.'}</p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
            </div>
        );
    }

    return (
        <div className="space-y-2">
            <textarea
                value={data.content}
                onChange={(event) => onChange({ ...data, content: event.target.value })}
                rows={12}
                className="w-full flex-grow rounded-md border border-slate-300 bg-white p-3 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                placeholder={mode === 'live' ? 'Capture wins, fumbles, and new intelligence in real time…' : 'Use this space to pre-draft notes or reminders.'}
            />
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default NotesWidget;
