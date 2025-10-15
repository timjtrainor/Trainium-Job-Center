import React from 'react';
import type { WidgetProps } from '../types';
import type { QuestionArsenalData } from '../types';
import { formatTimestamp, listToLines, linesToList } from '../utils';

export const QuestionArsenalWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
}: WidgetProps<QuestionArsenalData>) => {
    const toggleAsked = (question: string) => {
        const asked = new Set(data.asked);
        if (asked.has(question)) {
            asked.delete(question);
        } else {
            asked.add(question);
        }
        onChange({ ...data, asked: Array.from(asked) });
    };

    if (mode === 'prep' && editable) {
        return (
            <div className="space-y-3">
                <textarea
                    value={listToLines(data.questions)}
                    onChange={(event) => onChange({ ...data, questions: linesToList(event.target.value) })}
                    rows={10}
                    className="w-full rounded-md border border-slate-300 bg-white p-3 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    placeholder="List strategic questions you plan to ask, one per line."
                />
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {data.questions.length > 0 ? (
                data.questions.map((question, index) => {
                    const id = `${index}-${question}`;
                    const isChecked = data.asked.includes(question);
                    return (
                        <label key={id} htmlFor={id} className="flex cursor-pointer items-start gap-2">
                            <input
                                id={id}
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => toggleAsked(question)}
                                className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className={`text-sm leading-6 text-slate-700 dark:text-slate-300 ${isChecked ? 'line-through text-slate-400 dark:text-slate-500' : ''}`}>
                                {question}
                            </span>
                        </label>
                    );
                })
            ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">Add strategic questions in prep mode.</p>
            )}
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default QuestionArsenalWidget;
