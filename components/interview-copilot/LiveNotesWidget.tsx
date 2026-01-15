import React, { useState, useEffect, useCallback } from 'react';
import { Interview, InterviewPayload } from '../../types';
import { CheckIcon, LoadingSpinner } from '../IconComponents';

interface LiveNotesWidgetProps {
    notes: string;
    onChange: (value: string) => void;
    onSave: () => void;
    className?: string;
}

const LiveNotesWidget = ({ notes, onChange, onSave, className }: LiveNotesWidgetProps) => {
    return (
        <div className={`flex flex-col h-full bg-white dark:bg-slate-800 ${className}`}>
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-700 dark:text-slate-200">Live Notes</span>
                </div>
                <span className="text-[10px] text-slate-400">Captured in real-time</span>
            </div>

            <textarea
                className="flex-1 w-full p-4 resize-none border-0 focus:ring-0 bg-transparent text-sm leading-relaxed text-slate-700 dark:text-slate-300 placeholder-slate-400 custom-scrollbar"
                placeholder="Capture wins, fumbles, and new intelligence in real-time..."
                value={notes}
                onChange={(e) => onChange(e.target.value)}
                onBlur={onSave}
            />
        </div>
    );
};

export default LiveNotesWidget;
